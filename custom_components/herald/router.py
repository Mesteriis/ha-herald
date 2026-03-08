"""Channel routing for Herald notifications."""

from __future__ import annotations

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

ROOM_AUDIO_PRIORITY: tuple[str, ...] = ("alisa", "homepod", "tv")
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
                results.append(result)
        return results

    def _resolve_channel_names(
        self,
        context: NotificationContext,
        flow: FlowConfig,
        presence: PresenceSnapshot,
    ) -> list[str]:
        explicit = list(context.channels)
        if explicit and self._should_bypass_channel_policy(context):
            return [
                name
                for name in dict.fromkeys(explicit)
                if name in self._config.channels
            ]
        candidate_names = explicit or list(flow.channels) or list(self._config.channels)
        candidate_names = self._apply_presence_based_strategy(candidate_names, presence)
        candidate_names = self._apply_time_based_strategy(candidate_names, context, presence)
        candidate_names = self._apply_severity_based_strategy(candidate_names, context)
        candidate_names = self._apply_activity_based_strategy(candidate_names, context)
        candidate_names = self._apply_room_based_strategy(candidate_names, context, presence)

        filtered: list[str] = []
        for name in candidate_names:
            channel = self._config.channels.get(name)
            if channel is None:
                continue
            if not self._should_bypass_channel_policy(context) and not self._channel_type_enabled(channel):
                continue
            if channel.user and context.users and not self._should_bypass_channel_policy(context):
                allowed_users = {
                    user.split(".", maxsplit=1)[1] if "." in user else user
                    for user in context.users
                } | set(context.users)
                if channel.user not in allowed_users:
                    continue
            filtered.append(name)
        return list(dict.fromkeys(filtered))

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

    def _channel_matches_room(self, channel: ChannelConfig | None, room: str) -> bool:
        if channel is None:
            return False
        if channel.room == room:
            return True
        if room in dict(channel.data.get("room_targets", {})):
            return True
        return False

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
                await self._hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": title_to_send,
                        "message": message,
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

        service = channel.service or "tts.yandex_station_say"
        data = {**channel.data, "message": message}
        data.pop("audio_targets", None)
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
        """Deliver a TV notification through the existing HA TTS/media_player stack."""
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
        return await self._async_send_media_tts_target(
            channel=channel,
            service=channel.service or "tts.speak",
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
