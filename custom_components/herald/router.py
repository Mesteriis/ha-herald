"""Channel routing for Herald notifications."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .actions import build_ack_action, build_snooze_action
from .ai import HeraldAIClient
from .channel_tts_hume import HeraldHumeTTSChannel
from .const import (
    DEFAULT_PERSONALITY,
    DEFAULT_SNOOZE_MINUTES,
    QUIET_HOURS_POLICY_ALLOW,
    QUIET_HOURS_POLICY_BLOCK,
    QUIET_HOURS_POLICY_DEFAULT,
    SEVERITY_RANK,
)
from .controls import HeraldControlManager
from .flows import severity_allowed
from .models import ChannelConfig, FlowConfig, HeraldConfig, NotificationContext, PresenceSnapshot
from .presence import PresenceResolver

_LOGGER = logging.getLogger(__name__)

ROOM_AUDIO_PRIORITY: tuple[str, ...] = ("alisa", "homepod")
UNAVAILABLE_STATES: set[str] = {"off", "unavailable", "unknown"}
INACTIVE_MEDIA_STATES: set[str] = {"off", "idle", "standby", "unavailable", "unknown"}

ACTION_LABELS: dict[str, dict[str, str]] = {
    "ru": {"ack": "Принято", "snooze": "Отложить на 30 минут"},
    "en": {"ack": "Acknowledge", "snooze": "Snooze 30 min"},
    "es": {"ack": "Confirmado", "snooze": "Posponer 30 min"},
    "fr": {"ack": "Pris en compte", "snooze": "Reporter 30 min"},
}


class HeraldRouter:
    """Route notifications to channels based on flow, presence, and language."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: HeraldConfig,
        ai_client: HeraldAIClient,
        presence: PresenceResolver,
        controls: HeraldControlManager,
        dashboard_recorder: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self._hass = hass
        self._config = config
        self._ai_client = ai_client
        self._presence = presence
        self._controls = controls
        self._dashboard_recorder = dashboard_recorder
        self._hume_tts = HeraldHumeTTSChannel(hass)

    async def async_route(
        self,
        context: NotificationContext,
        flow: FlowConfig,
    ) -> list[dict[str, Any]]:
        """Route a notification to one or more output channels."""
        presence = await self._presence.async_resolve(context)
        channel_names = self._resolve_channel_names(context, flow, presence)
        channels = [
            self._config.channels[name]
            for name in channel_names
            if name in self._config.channels
            and self._channel_available_for_context(self._config.channels[name], context)
        ]

        rendered_cache: dict[tuple[str, str, str], dict[str, str]] = {}
        results: list[dict[str, Any]] = []
        channels_by_user: dict[str | None, list[ChannelConfig]] = defaultdict(list)
        for channel in channels:
            channels_by_user[channel.user].append(channel)

        for user_key, bucket in channels_by_user.items():
            language = self._resolve_language(user_key, context, presence)
            character = self._resolve_character(user_key, context, flow, presence)
            delivery_room = self._resolve_delivery_room(user_key, context, presence)
            cache_key = (language, character or DEFAULT_PERSONALITY, delivery_room or "")
            if cache_key not in rendered_cache:
                rendered_cache[cache_key] = await self._ai_client.async_rewrite_payload(
                    title=context.title,
                    message=context.message,
                    level=context.level,
                    language=language,
                    character=character,
                    rewrite=context.rewrite,
                    render_context=self._build_render_context(
                        context=context,
                        presence=presence,
                        language=language,
                        character=character,
                        room=delivery_room,
                    ),
                )
            payload = rendered_cache[cache_key]
            ai_meta = {
                key: value
                for key, value in payload.items()
                if key.startswith("_herald_ai_")
            }
            for channel in bucket:
                result = await self._async_send_channel(
                    channel=channel,
                    title=payload["title"],
                    message=payload["message"],
                    language=language,
                    context=context,
                    flow=flow,
                    presence=presence,
                    delivery_room=delivery_room,
                )
                results.append({**result, **ai_meta})
        return results

    def build_route_preview(
        self,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
    ) -> dict[str, Any]:
        """Return a non-delivery preview of Herald routing decisions."""
        resolution_trace: list[dict[str, Any]] = []
        channel_decisions: list[dict[str, Any]] = []
        channel_names = self._resolve_channel_names(
            context,
            flow,
            presence,
            resolution_trace=resolution_trace,
            channel_decisions=channel_decisions,
        )
        deliveries: list[dict[str, Any]] = []
        channels_by_user: dict[str | None, list[ChannelConfig]] = defaultdict(list)
        for name in channel_names:
            channel = self._config.channels.get(name)
            if channel is None:
                continue
            channels_by_user[channel.user].append(channel)

        for user_key, bucket in channels_by_user.items():
            language = self._resolve_language(user_key, context, presence)
            character = self._resolve_character(user_key, context, flow, presence)
            delivery_room = self._resolve_delivery_room(user_key, context, presence)
            for channel in bucket:
                deliveries.append(
                    self._preview_channel_delivery(
                        channel=channel,
                        context=context,
                        flow=flow,
                        presence=presence,
                        language=language,
                        character=character,
                        delivery_room=delivery_room,
                    )
                )

        return {
            "requested": {
                "flow": context.flow,
                "event": context.event,
                "level": context.level,
                "room": context.room,
                "device": context.device,
                "user": context.user,
                "users": list(context.users),
                "channels": list(context.channels),
                "message": context.message,
                "mobile_zone": self._requested_mobile_zone(context),
                "mobile_options": {
                    key: value
                    for key, value in self._mobile_options(context).items()
                    if key != "zone"
                },
            },
            "presence": presence.to_dict(),
            "resolved": {
                "final_channels": list(channel_names),
                "delivery_room": self._resolve_delivery_room(None, context, presence),
                "channel_count": len(channel_names),
            },
            "resolution_trace": resolution_trace,
            "channel_decisions": channel_decisions,
            "deliveries": deliveries,
        }

    def _resolve_channel_names(
        self,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
        *,
        resolution_trace: list[dict[str, Any]] | None = None,
        channel_decisions: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        explicit = list(context.channels)
        if explicit and self._should_bypass_channel_policy(context):
            selected = [
                name
                for name in dict.fromkeys(explicit)
                if name in self._config.channels
            ]
            self._record_resolution_stage(
                resolution_trace,
                stage="explicit_bypass",
                candidate_names=selected,
                note="Explicit channel request bypassed availability policy",
            )
            self._record_channel_decisions(channel_decisions, selected)
            return selected
        candidate_names = explicit or list(flow.channels) or list(self._config.channels)
        self._record_resolution_stage(
            resolution_trace,
            stage="initial",
            candidate_names=candidate_names,
        )
        candidate_names, explicit_device_match = self._apply_device_based_strategy(candidate_names, context)
        self._record_resolution_stage(
            resolution_trace,
            stage="device",
            candidate_names=candidate_names,
            note="Explicit device match" if explicit_device_match else None,
        )
        candidate_names = self._apply_presence_based_strategy(candidate_names, presence)
        self._record_resolution_stage(
            resolution_trace,
            stage="presence",
            candidate_names=candidate_names,
            note="Away routing applied" if presence.nobody_home else None,
        )
        candidate_names = self._apply_time_based_strategy(candidate_names, context, presence)
        self._record_resolution_stage(
            resolution_trace,
            stage="quiet_hours",
            candidate_names=candidate_names,
            note="Quiet hours filtering applied" if presence.quiet_hours else None,
        )
        candidate_names = self._apply_severity_based_strategy(candidate_names, context)
        self._record_resolution_stage(
            resolution_trace,
            stage="severity",
            candidate_names=candidate_names,
        )
        candidate_names = self._apply_activity_based_strategy(candidate_names, context)
        self._record_resolution_stage(
            resolution_trace,
            stage="activity",
            candidate_names=candidate_names,
        )
        if not explicit_device_match:
            candidate_names = self._apply_room_based_strategy(candidate_names, context, presence)
            self._record_resolution_stage(
                resolution_trace,
                stage="room",
                candidate_names=candidate_names,
            )
            candidate_names = self._apply_local_target_strategy(candidate_names, context, presence)
            self._record_resolution_stage(
                resolution_trace,
                stage="local_target",
                candidate_names=candidate_names,
            )

        filtered: list[str] = []
        for name in candidate_names:
            channel = self._config.channels.get(name)
            if channel is None:
                self._record_channel_decisions(channel_decisions, [], dropped=(name, "missing_channel"))
                continue
            if not self._should_bypass_channel_policy(context) and not self._channel_type_enabled(channel):
                self._record_channel_decisions(channel_decisions, [], dropped=(name, "channel_family_disabled"))
                continue
            if not self._channel_matches_presence_policy(channel, context, presence):
                self._record_channel_decisions(channel_decisions, [], dropped=(name, "presence_policy"))
                continue
            if not self._channel_matches_requested_mobile_zone(channel, context):
                self._record_channel_decisions(channel_decisions, [], dropped=(name, "mobile_zone_filter"))
                continue
            if channel.user and context.users and not self._should_bypass_channel_policy(context):
                allowed_users = {
                    user.split(".", maxsplit=1)[1] if "." in user else user
                    for user in context.users
                } | set(context.users)
                if channel.user not in allowed_users:
                    self._record_channel_decisions(channel_decisions, [], dropped=(name, "user_filter"))
                    continue
            filtered.append(name)
        self._record_channel_decisions(channel_decisions, filtered)
        self._record_resolution_stage(
            resolution_trace,
            stage="final",
            candidate_names=filtered,
        )
        return list(dict.fromkeys(filtered))

    def _record_resolution_stage(
        self,
        resolution_trace: list[dict[str, Any]] | None,
        *,
        stage: str,
        candidate_names: list[str],
        note: str | None = None,
    ) -> None:
        """Record one routing stage for route previews."""
        if resolution_trace is None:
            return
        resolution_trace.append(
            {
                "stage": stage,
                "channels": list(dict.fromkeys(candidate_names)),
                "count": len(list(dict.fromkeys(candidate_names))),
                "note": note,
            }
        )

    def _record_channel_decisions(
        self,
        decisions: list[dict[str, Any]] | None,
        selected: list[str],
        *,
        dropped: tuple[str, str] | None = None,
    ) -> None:
        """Record final channel decisions for route previews."""
        if decisions is None:
            return
        if dropped is not None:
            channel_name, reason = dropped
            decisions.append(
                {
                    "channel": channel_name,
                    "selected": False,
                    "reason": reason,
                }
            )
            return
        known = {item["channel"] for item in decisions}
        for name in list(dict.fromkeys(selected)):
            if name in known:
                continue
            decisions.append(
                {
                    "channel": name,
                    "selected": True,
                    "reason": "selected",
                }
            )

    def _apply_device_based_strategy(
        self,
        candidate_names: list[str],
        context: NotificationContext,
    ) -> tuple[list[str], bool]:
        """Prefer channels that can directly reach one explicitly requested device."""
        device = str(context.device or "").strip()
        if not device:
            return candidate_names, False

        matched = [
            name
            for name in candidate_names
            if self._channel_matches_device(self._config.channels.get(name), device)
        ]
        if not matched:
            return candidate_names, False
        return matched, True

    def _apply_presence_based_strategy(
        self,
        candidate_names: list[str],
        presence: PresenceSnapshot,
    ) -> list[str]:
        if not presence.nobody_home:
            return candidate_names
        away_channels = self._presence.away_channels()
        if away_channels:
            return away_channels
        return [
            name
            for name in candidate_names
            if self._config.channels.get(name)
            and self._config.channels[name].channel_type not in {"tts", "tts_hume", "tv"}
        ]

    def _apply_time_based_strategy(
        self,
        candidate_names: list[str],
        context: NotificationContext,
        presence: PresenceSnapshot,
    ) -> list[str]:
        if not presence.quiet_hours or severity_allowed(context.level, "critical"):
            return candidate_names
        filtered: list[str] = []
        for name in candidate_names:
            channel = self._config.channels.get(name)
            if channel is None:
                continue
            if self._channel_allowed_in_quiet_hours(channel):
                filtered.append(name)
        return filtered

    def _apply_severity_based_strategy(
        self,
        candidate_names: list[str],
        context: NotificationContext,
    ) -> list[str]:
        def score(name: str) -> tuple[int, str]:
            channel = self._config.channels.get(name)
            if channel is None:
                return (99, name)
            channel_type = channel.channel_type
            critical_rank = {
                "telegram": 0,
                "mobile_app": 1,
                "persistent_notification": 2,
                "tts_hume": 3,
                "tts": 4,
                "tv": 5,
                "dashboard": 6,
                "system_log": 7,
            }
            default_rank = {
                "dashboard": 0,
                "persistent_notification": 1,
                "tts": 2,
                "mobile_app": 3,
                "telegram": 4,
                "system_log": 5,
                "tv": 6,
                "tts_hume": 7,
            }
            rank_map = critical_rank if severity_allowed(context.level, "critical") else default_rank
            return (rank_map.get(channel_type, 20), name)

        return sorted(candidate_names, key=score)

    def _apply_activity_based_strategy(
        self,
        candidate_names: list[str],
        context: NotificationContext,
    ) -> list[str]:
        activity = str(context.context_data.get("activity", "idle"))
        if activity not in {"sleeping", "media_playing"}:
            return candidate_names
        preferred = [
            name
            for name in candidate_names
            if self._config.channels.get(name)
            and self._config.channels[name].channel_type in {"mobile_app", "telegram", "persistent_notification"}
        ]
        fallback = [name for name in candidate_names if name not in preferred]
        return preferred + fallback

    def _apply_room_based_strategy(
        self,
        candidate_names: list[str],
        context: NotificationContext,
        presence: PresenceSnapshot,
    ) -> list[str]:
        room = context.room or presence.primary_room
        if room is None:
            return candidate_names
        normalized_room = self._normalize_room_preference(room)
        if normalized_room in {None, "auto", "all"}:
            return candidate_names

        matched = [
            name
            for name in candidate_names
            if self._channel_matches_room(self._config.channels.get(name), normalized_room)
        ]
        return matched + [name for name in candidate_names if name not in matched]

    def _apply_local_target_strategy(
        self,
        candidate_names: list[str],
        context: NotificationContext,
        presence: PresenceSnapshot,
    ) -> list[str]:
        """Keep only one local room device using alisa -> homepod -> tv priority."""
        room = self._resolve_delivery_room(None, context, presence)
        if room in {None, "auto", "all"}:
            return candidate_names

        local_names = [
            name
            for name in candidate_names
            if (
                (channel := self._config.channels.get(name)) is not None
                and channel.channel_type in {"tts", "tts_hume", "tv"}
                and self._channel_matches_room(channel, room)
            )
        ]
        if len(local_names) <= 1:
            return candidate_names

        scored_locals: list[tuple[tuple[int, int, str], str]] = []
        for name in candidate_names:
            score = self._local_channel_score(self._config.channels.get(name), context, room)
            if score is None:
                continue
            scored_locals.append((score, name))

        if not scored_locals:
            return candidate_names

        best_name = min(scored_locals)[1]
        local_name_set = set(local_names)
        return [best_name, *[name for name in candidate_names if name not in local_name_set]]

    def _channel_matches_room(self, channel: ChannelConfig | None, room: str) -> bool:
        if channel is None:
            return False
        if channel.room == room:
            return True
        if room in dict(channel.data.get("room_targets", {})):
            return True
        return False

    def _local_channel_score(
        self,
        channel: ChannelConfig | None,
        context: NotificationContext,
        room: str,
    ) -> tuple[int, int, str] | None:
        """Return one sortable score for room-local channel preference."""
        if channel is None or channel.channel_type not in {"tts", "tts_hume", "tv"}:
            return None
        if not self._channel_matches_room(channel, room):
            return None

        if channel.channel_type == "tv":
            target_entity_id = self._resolve_tts_entity_id(channel, context, delivery_room=room)
            if not isinstance(target_entity_id, str):
                return None
            target_state = self._hass.states.get(target_entity_id)
            if target_state is None or target_state.state in INACTIVE_MEDIA_STATES:
                return None
            return (2, 0, channel.name)

        audio_target = self._resolve_room_audio_target(channel, context, delivery_room=room)
        if audio_target is not None:
            kind = str(audio_target.get("kind", "")).strip().lower()
            kind_rank = {
                "alisa": 0,
                "homepod": 1,
            }.get(kind, 1)
            return (kind_rank, int(audio_target.get("priority", 99)), channel.name)

        room_audio_targets = dict(channel.data.get("audio_targets", {}))
        if room in room_audio_targets:
            return None
        target_entity_id = self._resolve_tts_entity_id(channel, context, delivery_room=room)
        if target_entity_id is None:
            return None
        return (1, 99, channel.name)

    def _channel_matches_device(self, channel: ChannelConfig | None, device: str) -> bool:
        """Return True when a channel can reach one explicit entity/service target."""
        if channel is None:
            return False
        normalized_device = str(device).strip().lower()
        if not normalized_device:
            return False
        if channel.name.lower() == normalized_device:
            return True
        if str(channel.service or "").strip().lower() == normalized_device:
            return True
        for entity_id in self._iter_channel_entity_ids(channel):
            if entity_id.lower() == normalized_device:
                return True
        return False

    def _iter_channel_entity_ids(self, channel: ChannelConfig) -> list[str]:
        """Return all known concrete entity ids attached to one channel."""
        entity_ids: list[str] = []
        if isinstance(channel.entity_id, list):
            entity_ids.extend(str(item).strip() for item in channel.entity_id if str(item).strip())
        elif isinstance(channel.entity_id, str) and channel.entity_id.strip():
            entity_ids.append(channel.entity_id.strip())
        entity_ids.extend(
            str(item).strip()
            for item in dict(channel.data.get("room_targets", {})).values()
            if str(item).strip()
        )
        for targets in dict(channel.data.get("audio_targets", {})).values():
            if not isinstance(targets, list):
                continue
            for target in targets:
                entity_id = str(target.get("entity_id") or "").strip()
                if entity_id:
                    entity_ids.append(entity_id)
        return entity_ids

    def _channel_matches_presence_policy(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
        presence: PresenceSnapshot,
    ) -> bool:
        """Restrict mobile delivery to away users unless the device was explicitly requested."""
        if channel.channel_type != "mobile_app":
            return True
        if context.device and self._channel_matches_device(channel, context.device):
            return True
        if presence.nobody_home:
            return True
        if channel.user is None:
            return False
        return not self._user_is_home(channel.user, presence)

    def _user_is_home(self, user_key: str, presence: PresenceSnapshot) -> bool:
        """Return True when one channel user is currently at home."""
        normalized = str(user_key).strip()
        if not normalized:
            return False
        candidates = {
            normalized,
            normalized.split(".", maxsplit=1)[1] if "." in normalized else normalized,
        }
        for entity_id in presence.people_home:
            person_slug = entity_id.split(".", maxsplit=1)[1] if "." in entity_id else entity_id
            if entity_id in candidates or person_slug in candidates:
                return True
        return False

    def _channel_matches_requested_mobile_zone(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
    ) -> bool:
        """Restrict mobile delivery to one requested HA zone when configured."""
        if channel.channel_type != "mobile_app":
            return True
        requested_zone = self._requested_mobile_zone(context)
        if requested_zone is None:
            return True
        if person_state := self._resolve_mobile_channel_person_state(channel):
            return self._state_matches_zone(person_state, requested_zone)
        if tracker_state := self._resolve_mobile_channel_tracker_state(channel):
            return self._state_matches_zone(tracker_state, requested_zone)
        return False

    def _resolve_mobile_channel_person_state(self, channel: ChannelConfig):
        """Resolve one person state that owns the mobile_app channel when possible."""
        if person_state := self._person_state_from_user(channel.user):
            return person_state
        async_all = getattr(self._hass.states, "async_all", None)
        if async_all is None:
            return None
        channel_tokens = self._mobile_channel_tokens(channel)
        if not channel_tokens:
            return None
        for person_state in async_all("person"):
            tracker_entities = list(person_state.attributes.get("device_trackers") or [])
            source_entity = person_state.attributes.get("source")
            if isinstance(source_entity, str):
                tracker_entities.insert(0, source_entity)
            for entity_id in dict.fromkeys(
                str(item).strip()
                for item in tracker_entities
                if str(item).strip()
            ):
                if self._zone_tokens(entity_id) & channel_tokens:
                    return person_state
        return None

    def _resolve_mobile_channel_tracker_state(self, channel: ChannelConfig):
        """Resolve one device_tracker state for a mobile_app channel when no person is known."""
        channel_tokens = self._mobile_channel_tokens(channel)
        if not channel_tokens:
            return None
        async_all = getattr(self._hass.states, "async_all", None)
        if async_all is not None:
            exact_matches = []
            fuzzy_matches = []
            for tracker_state in async_all("device_tracker"):
                entity_tokens = self._zone_tokens(tracker_state.entity_id)
                friendly_tokens = self._zone_tokens(tracker_state.attributes.get("friendly_name"))
                if entity_tokens & channel_tokens:
                    exact_matches.append(tracker_state)
                    continue
                if friendly_tokens & channel_tokens:
                    fuzzy_matches.append(tracker_state)
            if exact_matches:
                return exact_matches[0]
            if fuzzy_matches:
                return fuzzy_matches[0]
        for token in sorted(channel_tokens):
            if "." in token:
                continue
            if tracker_state := self._hass.states.get(f"device_tracker.{token}"):
                return tracker_state
        return None

    def _person_state_from_user(self, user_key: str | None):
        """Resolve one person state from a configured channel user slug/entity."""
        normalized = str(user_key or "").strip()
        if not normalized:
            return None
        candidates = [normalized]
        if "." not in normalized:
            candidates.append(f"person.{normalized}")
        for entity_id in candidates:
            state = self._hass.states.get(entity_id)
            if state is not None and str(state.entity_id).startswith("person."):
                return state
        return None

    def _mobile_channel_tokens(self, channel: ChannelConfig) -> set[str]:
        """Return channel-specific matching tokens for person/device_tracker lookups."""
        tokens = set(self._zone_tokens(channel.name))
        if channel.name.startswith("mobile_"):
            tokens |= self._zone_tokens(channel.name.removeprefix("mobile_"))
        service = str(channel.service or "").strip()
        tokens |= self._zone_tokens(service)
        if service.startswith("notify.mobile_app_"):
            tokens |= self._zone_tokens(service.removeprefix("notify.mobile_app_"))
        return tokens

    def _requested_mobile_zone(self, context: NotificationContext) -> str | None:
        """Return the requested Home Assistant zone filter for mobile channels."""
        zone = self._mobile_options(context).get("zone")
        text = str(zone or "").strip()
        return text or None

    def _state_matches_zone(self, state, requested_zone: str) -> bool:
        """Compare one person/device_tracker state against a requested HA zone."""
        zone_tokens = self._zone_tokens(requested_zone)
        if zone_state := self._hass.states.get(requested_zone):
            zone_tokens |= self._zone_tokens(zone_state.entity_id)
            zone_tokens |= self._zone_tokens(zone_state.attributes.get("friendly_name"))
        if not zone_tokens:
            return False
        state_tokens = self._zone_tokens(getattr(state, "state", ""))
        state_tokens |= self._zone_tokens(getattr(state, "entity_id", ""))
        state_tokens |= self._zone_tokens(getattr(state, "attributes", {}).get("friendly_name"))
        return bool(zone_tokens & state_tokens)

    @staticmethod
    def _zone_tokens(value: Any) -> set[str]:
        """Build simple comparison tokens for entity ids, slugs, and human labels."""
        text = str(value or "").strip().lower()
        if not text:
            return set()
        normalized = text.replace("-", "_")
        collapsed = "_".join(normalized.split())
        tokens = {text, normalized, collapsed}
        if "." in collapsed:
            tail = collapsed.split(".", maxsplit=1)[1]
            tokens.add(tail)
        return {item for item in tokens if item}

    def _resolve_language(
        self,
        user_key: str | None,
        context: NotificationContext,
        presence: PresenceSnapshot,
    ) -> str:
        if user_key is not None:
            return self._controls.user_language(user_key, default="ru")

        for user in list(context.users) + list(presence.people_home):
            slug = user.split(".", maxsplit=1)[1] if "." in user else user
            return self._controls.user_language(slug, default="ru")
        return "ru"

    def _resolve_character(
        self,
        user_key: str | None,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
    ) -> str:
        if context.character:
            return context.character
        if context.personality:
            return context.personality
        if user_key is not None:
            return self._controls.user_character(user_key, default=flow.personality or DEFAULT_PERSONALITY)
        for user in list(context.users) + list(presence.people_home):
            slug = user.split(".", maxsplit=1)[1] if "." in user else user
            return self._controls.user_character(slug, default=flow.personality or DEFAULT_PERSONALITY)
        return flow.personality or DEFAULT_PERSONALITY

    def _build_render_context(
        self,
        *,
        context: NotificationContext,
        presence: PresenceSnapshot,
        language: str,
        character: str | None,
        room: str | None,
    ) -> dict[str, Any]:
        people = list(context.users) or list(presence.people_home)
        return {
            "message": context.message,
            "event": context.event or context.title,
            "level": context.level,
            "person": people[0] if people else None,
            "people": people,
            "room": room or context.room or presence.primary_room,
            "entities": list(context.entities),
            "context": dict(context.context_data),
            "ai": {
                "character": character,
                "context": dict(context.ai_context),
            },
            "ai_context": dict(context.ai_context),
            "time": dt_util.now().isoformat(),
            "language": language,
            "character": character,
        }

    def _resolve_delivery_room(
        self,
        user_key: str | None,
        context: NotificationContext,
        presence: PresenceSnapshot,
    ) -> str | None:
        explicit_room = self._normalize_room_preference(context.room)
        if explicit_room not in {None, "auto", "all"}:
            return explicit_room

        users = list(context.context_data.get("users", []))
        if user_key:
            for item in users:
                if user_key in {item.get("slug"), item.get("person_entity_id")}:
                    return self._normalize_room_preference(item.get("current_room"))

        if context.user:
            normalized_user = context.user.split(".", maxsplit=1)[1] if "." in context.user else context.user
            for item in users:
                if normalized_user in {item.get("slug"), item.get("person_entity_id")}:
                    return self._normalize_room_preference(item.get("current_room"))

        return self._normalize_room_preference(presence.primary_room)

    def _channel_allowed_in_quiet_hours(self, channel: ChannelConfig) -> bool:
        """Evaluate the effective quiet-hours behavior for a channel."""
        if channel.quiet_hours_policy == QUIET_HOURS_POLICY_ALLOW:
            return True
        if channel.quiet_hours_policy == QUIET_HOURS_POLICY_BLOCK:
            return False
        if channel.quiet_hours_policy != QUIET_HOURS_POLICY_DEFAULT:
            return channel.channel_type not in {"tts", "tts_hume", "tv"}
        return channel.channel_type not in {"tts", "tts_hume", "tv"}

    def _channel_type_enabled(self, channel: ChannelConfig) -> bool:
        return self._controls.is_channel_type_enabled(channel.channel_type)

    def _should_bypass_channel_policy(self, context: NotificationContext) -> bool:
        """Return True when control-plane notifications should bypass channel availability checks."""
        if bool(context.metadata.get("bypass_channel_policy")):
            return True
        return self._is_direct_channel_test(context)

    def _is_direct_channel_test(self, context: NotificationContext) -> bool:
        """Return True for explicit channel test messages triggered from Herald controls."""
        return bool(str(context.metadata.get("control_test_channel", "")).strip())

    def _is_direct_channel_test_target(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
    ) -> bool:
        """Return True when the current channel matches the explicit control-plane test target."""
        target = str(context.metadata.get("control_test_channel", "")).strip()
        return bool(target) and channel.name == target

    def _channel_available_for_context(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
    ) -> bool:
        """Allow explicit channel tests to route even when the channel is currently disabled."""
        if channel.enabled:
            return True
        return self._should_bypass_channel_policy(context)

    def _preview_channel_delivery(
        self,
        *,
        channel: ChannelConfig,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
        language: str,
        character: str,
        delivery_room: str | None,
    ) -> dict[str, Any]:
        """Return one dry-run delivery plan for the channel."""
        preview: dict[str, Any] = {
            "channel": channel.name,
            "flow": flow.name,
            "room": delivery_room or presence.primary_room,
            "user": channel.user,
            "type": channel.channel_type,
            "language": language,
            "character": character,
            "enabled": channel.enabled,
            "min_level": channel.min_level,
        }
        if (
            not self._should_bypass_channel_policy(context)
            and not severity_allowed(context.level, channel.min_level)
        ):
            return {
                **preview,
                "status": "dropped",
                "reason": "channel_min_level",
            }

        if channel.channel_type == "tts":
            desired_room = delivery_room or self._normalize_room_preference(context.room)
            audio_target = self._resolve_room_audio_target(
                channel,
                context,
                delivery_room=delivery_room,
            )
            if audio_target is not None:
                target_service = str(audio_target.get("service") or channel.service or "tts.yandex_station_say")
                target_entity_id = str(audio_target.get("entity_id") or "").strip() or None
                return {
                    **preview,
                    "status": "planned",
                    "service": target_service,
                    "target_entity_id": target_entity_id,
                    "target_kind": audio_target.get("kind"),
                    "requested_room": desired_room,
                }
            room_audio_targets = channel.data.get("audio_targets", {}).get(desired_room, [])
            if isinstance(room_audio_targets, list) and room_audio_targets:
                return {
                    **preview,
                    "status": "dropped",
                    "reason": "room_audio_unavailable",
                    "requested_room": desired_room,
                }
            target_entity_id = self._resolve_tts_entity_id(channel, context, delivery_room=delivery_room)
            return {
                **preview,
                "status": "planned",
                "service": channel.service or "tts.yandex_station_say",
                "target_entity_id": target_entity_id,
                "requested_room": desired_room,
            }

        if channel.channel_type == "tv":
            target_entity_id = self._resolve_tts_entity_id(channel, context, delivery_room=delivery_room)
            if target_entity_id is None or isinstance(target_entity_id, list):
                return {
                    **preview,
                    "status": "error",
                    "reason": "tv_target_missing",
                }
            target_state = self._hass.states.get(target_entity_id)
            target_state_value = str(target_state.state).strip().lower() if target_state is not None else "unknown"
            active_only = bool(channel.data.get("active_only", True))
            if active_only and target_state_value in INACTIVE_MEDIA_STATES:
                return {
                    **preview,
                    "status": "dropped",
                    "reason": "tv_inactive",
                    "target_entity_id": target_entity_id,
                    "target_state": target_state_value,
                }
            service = self._resolve_tv_service(channel, context, delivery_room=delivery_room)
            return {
                **preview,
                "status": "planned",
                "service": service,
                "target_entity_id": target_entity_id,
                "target_state": target_state_value,
                "requested_room": delivery_room or self._normalize_room_preference(context.room),
                "delivery": "overlay" if isinstance(service, str) and service.startswith("notify.") else "tts",
            }

        if channel.channel_type == "mobile_app":
            return {
                **preview,
                "status": "planned",
                "service": channel.service,
                "notification_id": context.notification_id,
            }

        if channel.channel_type == "telegram":
            return {
                **preview,
                "status": "planned",
                "service": channel.service or "telegram_bot.send_message",
                "chat_id": channel.chat_id,
                "thread_id": channel.thread_id,
            }

        if channel.channel_type == "dashboard":
            return {
                **preview,
                "status": "planned",
                "service": "dashboard.feed",
            }

        if channel.channel_type == "persistent_notification":
            return {
                **preview,
                "status": "planned",
                "service": "persistent_notification.create",
            }

        if channel.channel_type == "logbook":
            return {
                **preview,
                "status": "planned",
                "service": "logbook.log",
            }

        return {
            **preview,
            "status": "planned",
            "service": channel.service or "system_log.write",
        }

    async def _async_send_channel(
        self,
        *,
        channel: ChannelConfig,
        title: str,
        message: str,
        language: str,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
        delivery_room: str | None,
    ) -> dict[str, Any]:
        """Send one notification to a concrete channel."""
        title_to_send = f"{channel.title_prefix} {title}".strip() if channel.title_prefix else title
        delivery_meta: dict[str, Any] = {}
        if (
            not self._should_bypass_channel_policy(context)
            and not severity_allowed(context.level, channel.min_level)
        ):
            return {
                "channel": channel.name,
                "status": "dropped",
                "reason": "channel_min_level",
                "min_level": channel.min_level,
                "flow": flow.name,
                "room": delivery_room or presence.primary_room,
                "user": channel.user,
                "type": channel.channel_type,
                "language": language,
            }
        try:
            if channel.channel_type == "tts":
                delivery_meta = await self._async_send_tts(
                    channel,
                    title_to_send,
                    message,
                    context,
                    delivery_room=delivery_room,
                )
            elif channel.channel_type == "tv":
                delivery_meta = await self._async_send_tv(
                    channel,
                    title_to_send,
                    message,
                    context,
                    language=language,
                    delivery_room=delivery_room,
                )
            elif channel.channel_type == "tts_hume":
                delivery_meta = await self._hume_tts.async_deliver(
                    channel=channel,
                    text=message,
                    context=context,
                )
            elif channel.channel_type == "mobile_app":
                delivery_meta = await self._async_send_notify_service(
                    channel,
                    title_to_send,
                    message,
                    context,
                    language,
                )
            elif channel.channel_type == "telegram":
                delivery_meta = await self._async_send_telegram(
                    channel,
                    title_to_send,
                    message,
                    context,
                    presence,
                    language,
                )
            elif channel.channel_type == "dashboard":
                delivery_meta = {"service": "dashboard.feed"}
                if self._dashboard_recorder is not None:
                    delivery_meta.update(
                        self._dashboard_recorder(
                            channel=channel,
                            title=title_to_send,
                            message=message,
                            language=language,
                            context=context,
                            presence=presence,
                        )
                    )
            elif channel.channel_type == "persistent_notification":
                notification_message = self._format_persistent_notification_message(
                    title=title_to_send,
                    message=message,
                    context=context,
                    presence=presence,
                    channel=channel,
                )
                await self._hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": title_to_send,
                        "message": notification_message,
                        "notification_id": context.notification_id,
                    },
                    blocking=True,
                )
                delivery_meta = {"service": "persistent_notification.create"}
            elif channel.channel_type == "logbook":
                await self._hass.services.async_call(
                    "logbook",
                    "log",
                    {
                        "name": title_to_send,
                        "message": message,
                        "domain": "herald",
                    },
                    blocking=True,
                )
                delivery_meta = {"service": "logbook.log"}
            else:
                await self._hass.services.async_call(
                    "system_log",
                    "write",
                    {
                        "level": "warning" if SEVERITY_RANK.get(context.level, 0) >= 20 else "info",
                        "message": f"[{context.flow}] {title_to_send}: {message}",
                    },
                    blocking=True,
                )
                delivery_meta = {"service": "system_log.write"}
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Herald channel %s failed: %s", channel.name, err)
            return {
                "channel": channel.name,
                "status": "error",
                "error": str(err),
                "flow": flow.name,
            }

        if delivery_meta.get("status") == "dropped":
            return delivery_meta

        return {
            "channel": channel.name,
            "status": "sent",
            "flow": flow.name,
            "room": delivery_room or presence.primary_room,
            "user": channel.user,
            "type": channel.channel_type,
            "language": language,
            **delivery_meta,
        }

    async def _async_send_tts(
        self,
        channel: ChannelConfig,
        title: str,
        message: str,
        context: NotificationContext,
        *,
        delivery_room: str | None,
    ) -> dict[str, Any]:
        tts_options = dict(context.metadata.get("tts_options", {}))
        desired_room = delivery_room or self._normalize_room_preference(context.room)
        room_audio_targets = channel.data.get("audio_targets", {}).get(desired_room, [])
        audio_target = self._resolve_room_audio_target(
            channel,
            context,
            delivery_room=delivery_room,
        )
        if audio_target is not None:
            target_service = str(audio_target.get("service") or channel.service or "tts.yandex_station_say")
            target_entity_id = str(audio_target.get("entity_id") or "").strip() or None
            if target_entity_id is None:
                raise ValueError(f"Channel {channel.name} resolved an empty room audio target")
            if target_service == "tts.speak":
                return await self._async_send_media_tts_target(
                    channel=channel,
                    service=target_service,
                    target_entity_id=target_entity_id,
                    title=title,
                    message=message,
                    delivery_room=delivery_room,
                    context=context,
                    target_data=audio_target,
                )
            data = {**channel.data, "message": message}
            data.pop("audio_targets", None)
            if tts_options:
                data.update(tts_options)
            if target_entity_id is not None:
                data["entity_id"] = target_entity_id
            if title:
                data.setdefault("cache", False)
            await self._async_call_service(target_service, data)
            return {
                "service": target_service,
                "target_entity_id": target_entity_id,
                "requested_room": delivery_room or self._normalize_room_preference(context.room),
                "target_kind": audio_target.get("kind"),
            }

        if isinstance(room_audio_targets, list) and room_audio_targets:
            return {
                "channel": channel.name,
                "status": "dropped",
                "reason": "room_audio_unavailable",
                "requested_room": desired_room,
                "type": channel.channel_type,
            }

        service = channel.service or "tts.yandex_station_say"
        data = {**channel.data, "message": message}
        data.pop("audio_targets", None)
        if tts_options:
            data.update(tts_options)
        entity_id = self._resolve_tts_entity_id(channel, context, delivery_room=delivery_room)
        if entity_id is not None:
            data["entity_id"] = entity_id
        if title:
            data.setdefault("cache", False)
        await self._async_call_service(service, data)
        return {
            "service": service,
            "target_entity_id": entity_id,
            "requested_room": delivery_room or self._normalize_room_preference(context.room),
        }

    async def _async_send_tv(
        self,
        channel: ChannelConfig,
        title: str,
        message: str,
        context: NotificationContext,
        *,
        language: str,
        delivery_room: str | None,
    ) -> dict[str, Any]:
        """Deliver a TV notification through overlay notify services when available."""
        target_entity_id = self._resolve_tts_entity_id(channel, context, delivery_room=delivery_room)
        if target_entity_id is None:
            raise ValueError(f"Channel {channel.name} requires a TV media_player target")
        if isinstance(target_entity_id, list):
            raise ValueError(f"Channel {channel.name} requires a single TV media_player target")

        target_state = self._hass.states.get(target_entity_id)
        active_only = bool(channel.data.get("active_only", True))
        if active_only and (target_state is None or target_state.state in INACTIVE_MEDIA_STATES):
            return {
                "channel": channel.name,
                "status": "dropped",
                "reason": "tv_inactive",
                "flow": context.flow,
                "room": delivery_room or self._normalize_room_preference(context.room),
                "user": channel.user,
                "type": channel.channel_type,
                "language": language,
            }
        service = self._resolve_tv_service(channel, context, delivery_room=delivery_room)
        if service is None:
            raise ValueError(f"Channel {channel.name} requires a TV notify service")
        if service.startswith("notify."):
            payload = {
                "title": title,
                "message": message,
                "data": {
                    **dict(channel.data.get("data", {})),
                },
            }
            payload["data"].setdefault("interrupt", 0)
            await self._async_call_service(service, payload)
            return {
                "service": service,
                "target_entity_id": target_entity_id,
                "requested_room": delivery_room or self._normalize_room_preference(context.room),
                "active_only": active_only,
                "delivery": "overlay",
            }
        return await self._async_send_media_tts_target(
            channel=channel,
            service=service,
            target_entity_id=target_entity_id,
            title=title,
            message=message,
            delivery_room=delivery_room,
            context=context,
            target_data={
                "kind": "tv",
                "entity_id": target_entity_id,
                "active_only": active_only,
                "announce": bool(channel.data.get("announce", True)),
            },
        )

    def _resolve_tts_entity_id(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
        *,
        delivery_room: str | None,
    ) -> str | list[str] | None:
        """Resolve the target entity/group for a TTS channel."""
        metadata = dict(context.metadata)
        if target_group := str(metadata.get("legacy_target_group", "")).strip():
            return target_group
        if explicit_entity_id := self._resolve_explicit_channel_entity_id(channel, context):
            return explicit_entity_id

        desired_room = delivery_room or self._normalize_room_preference(context.room)
        if desired_room in {None, "auto", "all"}:
            return channel.entity_id

        room_targets = dict(channel.data.get("room_targets", {}))
        if desired_room in room_targets:
            return room_targets[desired_room]
        return channel.entity_id

    def _resolve_room_audio_target(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
        *,
        delivery_room: str | None,
    ) -> dict[str, Any] | None:
        """Resolve the best available room-local audio target for a TTS channel."""
        explicit_target = self._resolve_explicit_audio_target(channel, context)
        if explicit_target is not None:
            return explicit_target
        desired_room = delivery_room or self._normalize_room_preference(context.room)
        if desired_room in {None, "auto", "all"}:
            return None
        raw_targets = channel.data.get("audio_targets", {}).get(desired_room, [])
        if not isinstance(raw_targets, list) or not raw_targets:
            return None
        ordered_targets = self._ordered_room_audio_targets(desired_room, raw_targets)
        for target in ordered_targets:
            if self._audio_target_is_available(target):
                return target
        return None

    def _resolve_explicit_audio_target(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
    ) -> dict[str, Any] | None:
        """Return one concrete audio target when the request names a device explicitly."""
        device = str(context.device or "").strip().lower()
        if not device:
            return None
        for targets in dict(channel.data.get("audio_targets", {})).values():
            if not isinstance(targets, list):
                continue
            for target in targets:
                entity_id = str(target.get("entity_id") or "").strip().lower()
                service = str(target.get("service") or "").strip().lower()
                if device in {entity_id, service}:
                    return dict(target)
        return None

    def _resolve_explicit_channel_entity_id(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
    ) -> str | None:
        """Return one concrete entity id when the request names a device explicitly."""
        device = str(context.device or "").strip().lower()
        if not device:
            return None
        if isinstance(channel.entity_id, str) and channel.entity_id.strip().lower() == device:
            return channel.entity_id.strip()
        room_targets = dict(channel.data.get("room_targets", {}))
        for entity_id in room_targets.values():
            if str(entity_id).strip().lower() == device:
                return str(entity_id).strip()
        return None

    def _resolve_tv_service(
        self,
        channel: ChannelConfig,
        context: NotificationContext,
        *,
        delivery_room: str | None,
    ) -> str | None:
        """Resolve one TV notify service, respecting room- and device-local mappings."""
        device = str(context.device or "").strip().lower()
        notify_services = {
            str(room_name): str(service_name).strip()
            for room_name, service_name in dict(channel.data.get("notify_services", {})).items()
            if str(service_name).strip()
        }
        if device:
            if str(channel.service or "").strip().lower() == device:
                return str(channel.service).strip() or None
            room_targets = dict(channel.data.get("room_targets", {}))
            for room_name, entity_id in room_targets.items():
                if str(entity_id).strip().lower() != device:
                    continue
                return notify_services.get(str(room_name)) or channel.service

        desired_room = delivery_room or self._normalize_room_preference(context.room)
        if desired_room not in {None, "auto", "all"} and desired_room in notify_services:
            return notify_services[desired_room]
        return channel.service

    def _ordered_room_audio_targets(
        self,
        room_name: str,
        targets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Order room-local audio targets by explicit preference and default fallback priority."""
        preferred_kind = self._controls.room_audio_target(room_name, default="auto")
        kind_order = list(ROOM_AUDIO_PRIORITY)
        if preferred_kind in ROOM_AUDIO_PRIORITY:
            kind_order = [preferred_kind, *[kind for kind in ROOM_AUDIO_PRIORITY if kind != preferred_kind]]
        ranking = {kind: index for index, kind in enumerate(kind_order)}
        return sorted(
            (dict(item) for item in targets),
            key=lambda item: (
                ranking.get(str(item.get("kind", "")).strip().lower(), len(kind_order)),
                int(item.get("priority", 99)),
                str(item.get("entity_id", "")),
            ),
        )

    def _audio_target_is_available(self, target: dict[str, Any]) -> bool:
        """Return True when one room-local audio target can currently accept TTS."""
        entity_id = str(target.get("entity_id") or "").strip()
        if not entity_id:
            return False
        state = self._hass.states.get(entity_id)
        if state is None:
            return False
        state_value = str(state.state).strip().lower()
        if bool(target.get("active_only", False)):
            return state_value not in INACTIVE_MEDIA_STATES
        return state_value not in UNAVAILABLE_STATES

    async def _async_send_media_tts_target(
        self,
        *,
        channel: ChannelConfig,
        service: str,
        target_entity_id: str,
        title: str,
        message: str,
        delivery_room: str | None,
        context: NotificationContext,
        target_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Deliver TTS through a media player target such as HomePod or TV."""
        merged_data = {**channel.data, **target_data}
        tts_options = dict(context.metadata.get("tts_options", {}))
        if tts_options:
            if service == "tts.speak":
                options = dict(merged_data.get("options", {}))
                options.update(tts_options)
                merged_data["options"] = options
            else:
                merged_data.update(tts_options)
        if bool(merged_data.get("turn_on", False)):
            await self._hass.services.async_call(
                "media_player",
                "turn_on",
                {"entity_id": target_entity_id},
                blocking=True,
            )

        if (volume_level := merged_data.get("volume_level")) is not None:
            await self._hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": target_entity_id,
                    "volume_level": float(volume_level),
                },
                blocking=True,
            )

        spoken_message = message
        if title and title.strip() and title.strip().lower() not in message.strip().lower():
            spoken_message = f"{title}. {message}"
        if service == "tts.speak":
            tts_entity_id = str(merged_data.get("engine_entity_id", "")).strip()
            if not tts_entity_id:
                raise ValueError(f"Channel {channel.name} requires engine_entity_id for tts.speak")
            payload = {
                "entity_id": tts_entity_id,
                "media_player_entity_id": target_entity_id,
                "message": spoken_message,
                "cache": bool(merged_data.get("cache", False)),
                "options": dict(merged_data.get("options", {})),
            }
            if "language" in merged_data:
                payload["language"] = merged_data["language"]
            await self._async_call_service(service, payload)
            return {
                "service": service,
                "target_entity_id": target_entity_id,
                "tts_entity_id": tts_entity_id,
                "requested_room": delivery_room or self._normalize_room_preference(context.room),
                "active_only": bool(merged_data.get("active_only", False)),
                "announce": bool(merged_data.get("announce", True)),
                "target_kind": merged_data.get("kind"),
            }

        data = {
            **merged_data,
            "entity_id": target_entity_id,
            "message": spoken_message,
            "title": title,
        }
        for key in ("audio_targets", "kind", "priority", "engine_entity_id", "active_only"):
            data.pop(key, None)
        await self._async_call_service(service, data)
        return {
            "service": service,
            "target_entity_id": target_entity_id,
            "requested_room": delivery_room or self._normalize_room_preference(context.room),
            "active_only": bool(merged_data.get("active_only", False)),
            "target_kind": merged_data.get("kind"),
        }

    def _normalize_room_preference(self, room: str | None) -> str | None:
        """Normalize a room preference from current helper/UI labels."""
        if room is None:
            return None
        normalized = str(room).strip().lower()
        aliases = {
            "": None,
            "auto": "auto",
            "авто": "auto",
            "all": "all",
            "all rooms": "all",
            "все комнаты": "all",
            "living_room": "living_room",
            "living room": "living_room",
            "гостиная": "living_room",
            "bedroom": "bedroom",
            "спальня": "bedroom",
            "kitchen": "kitchen",
            "кухня": "kitchen",
            "bathroom": "bathroom",
            "ванная": "bathroom",
            "office": "office",
            "кабинет": "office",
        }
        return aliases.get(normalized, normalized)

    async def _async_send_notify_service(
        self,
        channel: ChannelConfig,
        title: str,
        message: str,
        context: NotificationContext,
        language: str,
    ) -> dict[str, Any]:
        if not channel.service:
            raise ValueError(f"Channel {channel.name} requires a notify service")
        data = {**channel.data, "title": title, "message": message}
        payload_data = dict(data.get("data", {}))
        payload_data = self._apply_mobile_options(payload_data, context)
        payload_data.setdefault("tag", context.notification_id)
        payload_data.setdefault("group", f"herald_{context.flow}")
        if context.include_actions:
            payload_data["actions"] = self._build_mobile_actions(context, language)
            payload_data["herald_notification_id"] = context.notification_id
            payload_data["herald_flow"] = context.flow
        data["data"] = payload_data
        await self._async_call_service(channel.service, data)
        return {
            "service": channel.service,
        }

    def _apply_mobile_options(
        self,
        payload_data: dict[str, Any],
        context: NotificationContext,
    ) -> dict[str, Any]:
        """Merge mobile app delivery overrides from the Herald request metadata."""
        merged = dict(payload_data)
        options = self._mobile_options(context)
        if not options:
            return merged

        push_data = dict(merged.get("push", {}))
        interruption_level = str(options.get("interruption_level", "")).strip()
        if interruption_level:
            push_data["interruption-level"] = interruption_level
        sound = str(options.get("sound", "")).strip()
        if sound:
            push_data["sound"] = sound
        if push_data:
            merged["push"] = push_data

        if self._coerce_bool(options.get("high_priority")):
            merged["ttl"] = 0
            merged["priority"] = "high"
        if self._coerce_bool(options.get("sticky")):
            merged["sticky"] = "true"
        channel_name = str(options.get("channel", "")).strip()
        if channel_name:
            merged["channel"] = channel_name
        icon = str(options.get("icon", "")).strip()
        if icon:
            merged["notification_icon"] = icon
        if color := self._normalize_mobile_color(options.get("color")):
            merged["color"] = color
        tag = str(options.get("tag", "")).strip()
        if tag:
            merged["tag"] = tag
        return merged

    @staticmethod
    def _normalize_mobile_color(value: Any) -> str | None:
        """Normalize HA color selector payloads into the mobile_app expected string."""
        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                red, green, blue = (max(0, min(255, int(item))) for item in value)
            except (TypeError, ValueError):
                return None
            return f"#{red:02x}{green:02x}{blue:02x}"
        text = str(value or "").strip()
        return text or None

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        """Interpret object payload booleans from YAML/service data safely."""
        if isinstance(value, bool):
            return value
        return str(value or "").strip().lower() in {"1", "true", "yes", "on", "enabled"}

    @staticmethod
    def _mobile_options(context: NotificationContext) -> dict[str, Any]:
        """Return parsed mobile override metadata from the Herald request."""
        raw = context.metadata.get("mobile_options", {})
        return dict(raw) if isinstance(raw, dict) else {}

    def _format_persistent_notification_message(
        self,
        *,
        title: str,
        message: str,
        context: NotificationContext,
        presence: PresenceSnapshot,
        channel: ChannelConfig,
    ) -> str:
        """Append compact pretty JSON metadata for maintenance tray debugging."""
        if not bool(context.metadata.get("maintenance_tray_debug")):
            return message
        context_excerpt = {
            key: context.context_data.get(key)
            for key in (
                "home_mode",
                "quiet_hours",
                "activity",
                "primary_room",
                "occupied_rooms",
                "people_home",
                "user_rooms",
            )
            if key in context.context_data
        }
        metadata = {
            key: value
            for key, value in dict(context.metadata).items()
            if key not in {"bypass_channel_policy", "maintenance_tray_debug"}
        }
        payload = {
            "notification_id": context.notification_id,
            "event": context.event or title,
            "flow": context.flow,
            "level": context.level,
            "source": context.source,
            "timestamp": context.timestamp,
            "room": context.room or presence.primary_room,
            "users": list(context.users),
            "entities": list(context.entities),
            "group": context.group,
            "rewrite": context.rewrite,
            "summarize": context.summarize,
            "delivery_channel": channel.name,
            "presence": {
                "home_mode": presence.home_mode,
                "quiet_hours": presence.quiet_hours,
                "occupied_rooms": list(presence.occupied_rooms),
                "people_home": list(presence.people_home),
            },
            "context": context_excerpt,
            "ai_context": dict(context.ai_context),
            "metadata": metadata,
        }
        pretty = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if not message.strip():
            return f"```json\n{pretty}\n```"
        return f"{message}\n\nMetadata:\n```json\n{pretty}\n```"

    async def _async_send_telegram(
        self,
        channel: ChannelConfig,
        title: str,
        message: str,
        context: NotificationContext,
        presence: PresenceSnapshot,
        language: str,
    ) -> dict[str, Any]:
        service = channel.service or "telegram_bot.send_message"
        payload = {
            **channel.data,
            "title": title,
            "message": message,
            "disable_notification": not presence.nobody_home,
        }
        if context.include_actions:
            payload["inline_keyboard"] = self._build_telegram_inline_keyboard(context, language)
        if channel.chat_id is not None:
            payload["chat_id"] = [channel.chat_id] if not isinstance(channel.chat_id, list) else channel.chat_id
        if channel.thread_id is not None:
            payload["message_thread_id"] = channel.thread_id
        await self._async_call_service(service, payload)
        return {
            "service": service,
            "chat_id": channel.chat_id,
            "thread_id": channel.thread_id,
            "config_entry_id": channel.data.get("config_entry_id"),
        }

    def _build_mobile_actions(self, context: NotificationContext, language: str) -> list[dict[str, str]]:
        labels = ACTION_LABELS.get(language, ACTION_LABELS["en"])
        return [
            {
                "action": build_ack_action(context.notification_id),
                "title": labels["ack"],
            },
            {
                "action": build_snooze_action(
                    context.flow,
                    minutes=DEFAULT_SNOOZE_MINUTES,
                    notification_id=context.notification_id,
                ),
                "title": labels["snooze"],
            },
        ]

    def _build_telegram_inline_keyboard(
        self,
        context: NotificationContext,
        language: str,
    ) -> list[str]:
        labels = ACTION_LABELS.get(language, ACTION_LABELS["en"])
        ack = build_ack_action(context.notification_id)
        snooze = build_snooze_action(
            context.flow,
            minutes=DEFAULT_SNOOZE_MINUTES,
            notification_id=context.notification_id,
        )
        return [f"{labels['ack']}:/{ack}, {labels['snooze']}:/{snooze}"]

    async def _async_call_service(self, service_name: str, data: dict[str, Any]) -> None:
        if "." not in service_name:
            raise ValueError(f"Invalid service name: {service_name}")
        domain, service = service_name.split(".", maxsplit=1)
        await self._hass.services.async_call(domain, service, data, blocking=True)
