"""Coordinator for Herald notification state and dispatch."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .actions import ensure_notification_id, parse_action_token
from .ai import HeraldAIClient
from .const import (
    DEFAULT_DASHBOARD_PRESET,
    DEFAULT_PERSONALITY,
    DOMAIN,
    EVENT_MOBILE_ACTION,
    EVENT_MOBILE_CLEARED,
    EVENT_TELEGRAM_CALLBACK,
    FRONTEND_MODULE_URL,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .flows import async_flow_matches, resolve_requested_flow, severity_rank
from .models import HeraldConfig, NotificationContext, RuntimeState
from .presence import PresenceResolver
from .queue import NotificationQueueManager
from .router import HeraldRouter
from .translations import action_feedback_text, normalize_language

_LOGGER = logging.getLogger(__name__)


class HeraldCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Central runtime object for Herald."""

    config: HeraldConfig

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        raw_config: dict[str, Any],
    ) -> None:
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_{entry.entry_id}")
        self.entry = entry
        self.config = HeraldConfig.from_raw(raw_config)
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY}.{entry.entry_id}",
        )
        self._state = RuntimeState(current_day=dt_util.now().date().isoformat())
        self._session = async_get_clientsession(hass)
        self.ai_client = HeraldAIClient(self._session, self.config)
        self.presence = PresenceResolver(hass, self.config)
        self.router = HeraldRouter(hass, self.config, self.ai_client, self.presence)
        self.queue = NotificationQueueManager(self)
        self._event_unsubs: list[Any] = []

    async def _async_setup(self) -> None:
        """Load persistent state and augment autodiscovered channels."""
        if stored := await self._store.async_load():
            self._state = RuntimeState.from_dict(stored)
        self._reset_daily_counters_if_needed()
        self._augment_runtime_config()
        self._register_event_listeners()

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the coordinator snapshot consumed by sensors."""
        presence = await self.presence.async_resolve(
            NotificationContext(
                flow="system_events",
                title="snapshot",
                message="snapshot",
                level="info",
                source="coordinator",
                timestamp=dt_util.now().isoformat(),
                rewrite=False,
                summarize=False,
            )
        )
        return self._build_snapshot(presence)

    async def async_handle_service_notify(self, data: dict[str, Any]) -> None:
        """Handle the herald.notify service."""
        requested_flow = data.get("flow")
        level = str(data.get("level", "info"))
        flow_name = resolve_requested_flow(self.config.flows, requested_flow, level)
        flow = self.config.flows[flow_name]
        if not self.is_flow_enabled(flow_name) and not data.get("force", False):
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "flow_disabled",
                    "flow": flow_name,
                    "level": level,
                    "message": data["message"],
                }
            )
            await self._async_persist_and_publish()
            return

        now_iso = dt_util.now().isoformat()
        context = NotificationContext(
            flow=flow_name,
            title=str(data.get("title", "Herald")),
            message=str(data["message"]),
            level=level,
            source=str(data.get("source", "manual")),
            timestamp=now_iso,
            notification_id=ensure_notification_id(data.get("notification_id"), flow_name, now_iso),
            automation_id=data.get("automation_id"),
            device=data.get("device"),
            room=data.get("room"),
            user=data.get("user"),
            users=list(data.get("users", [])),
            channels=list(data.get("channels", [])),
            metadata=dict(data.get("metadata", {})),
            personality=data.get("personality"),
            rewrite=bool(data.get("rewrite", True)),
            summarize=bool(data.get("summarize", True)),
            force=bool(data.get("force", False)),
            include_actions=bool(data.get("include_actions", severity_rank(level) >= severity_rank("warning"))),
        )

        if not context.users and context.user:
            context.users = [context.user]

        matches = await async_flow_matches(
            self.hass,
            flow,
            context,
            home_mode_entity=self.config.presence.get("home_mode_entity"),
        )
        if not matches and not context.force:
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "conditions_not_met",
                    "flow": flow_name,
                    "level": level,
                    "message": context.message,
                }
            )
            await self._async_persist_and_publish()
            return

        self._append_trace(
            {
                "stage": "enqueue",
                "flow": flow_name,
                "level": context.level,
                "title": context.title,
                "message": context.message,
                "notification_id": context.notification_id,
                "channels": context.channels,
            }
        )
        await self.queue.async_enqueue(
            context,
            summary_window_seconds=flow.summary_window_seconds if context.summarize else 0,
        )
        await self._async_persist_and_publish()

    async def async_process_notifications(
        self,
        notifications: list[NotificationContext],
    ) -> None:
        """Process a queue group after the summary window expires."""
        if not notifications:
            return

        flow = self.config.flows[notifications[0].flow]
        if self._should_summarize(flow, notifications):
            summary_context = await self._async_build_summary_context(flow, notifications)
            results = await self.router.async_route(summary_context, flow)
            self._record_delivery(summary_context, results, grouped_count=len(notifications))
            return

        for context in notifications:
            results = await self.router.async_route(context, flow)
            self._record_delivery(context, results, grouped_count=1)

    async def async_generate_dashboard(
        self,
        *,
        path: str,
        title: str,
        preset: str = DEFAULT_DASHBOARD_PRESET,
    ) -> None:
        """Generate a YAML dashboard file for the Herald UI."""
        content = self._build_dashboard_yaml(title=title, preset=preset)
        destination = self.hass.config.path(path)
        await self.hass.async_add_executor_job(self._write_text_file, destination, content)
        self._append_trace(
            {
                "stage": "dashboard",
                "path": destination,
                "title": title,
                "preset": preset,
                "status": "generated",
            }
        )
        await self._async_persist_and_publish()

    async def async_set_flow_state(self, flow_name: str, enabled: bool) -> None:
        """Temporarily override a flow enabled state at runtime."""
        self._state.flow_overrides[flow_name] = enabled
        self._append_trace(
            {
                "stage": "flow_override",
                "flow": flow_name,
                "enabled": enabled,
            }
        )
        await self._async_persist_and_publish()

    async def async_acknowledge(
        self,
        notification_id: str,
        *,
        actor: str | None = None,
        source: str = "service",
    ) -> None:
        """Mark a notification as acknowledged."""
        stamp = dt_util.now().isoformat()
        self._state.acknowledged_notifications[notification_id] = {
            "actor": actor or "unknown",
            "source": source,
            "timestamp": stamp,
        }
        if self._state.last_notification.get("notification_id") == notification_id:
            self._state.last_notification["acknowledged"] = True
            self._state.last_notification["acknowledged_at"] = stamp
            self._state.last_notification["acknowledged_by"] = actor or "unknown"
        for item in self._state.recent_notifications:
            if item.get("notification_id") == notification_id:
                item["acknowledged"] = True
                item["acknowledged_at"] = stamp
                item["acknowledged_by"] = actor or "unknown"
        self._append_trace(
            {
                "stage": "acknowledge",
                "notification_id": notification_id,
                "actor": actor or "unknown",
                "source": source,
            }
        )
        await self._async_emit_action_feedback(notification_id, kind="ack")
        await self._async_persist_and_publish()

    async def async_snooze_flow(
        self,
        flow_name: str,
        *,
        minutes: int,
        actor: str | None = None,
        source: str = "service",
        notification_id: str | None = None,
    ) -> None:
        """Snooze a flow until a timestamp in the future."""
        until = dt_util.now() + timedelta(minutes=minutes)
        self._state.snoozed_flows[flow_name] = until.isoformat()
        self._append_trace(
            {
                "stage": "snooze",
                "flow": flow_name,
                "minutes": minutes,
                "until": until.isoformat(),
                "actor": actor or "unknown",
                "source": source,
                "notification_id": notification_id,
            }
        )
        if notification_id:
            await self._async_emit_action_feedback(
                notification_id,
                kind="snooze",
                minutes=minutes,
            )
        await self._async_persist_and_publish()

    def trace_snapshot(self) -> dict[str, Any]:
        """Return recent traces for service responses and diagnostics."""
        return {
            "entry_id": self.entry.entry_id,
            "snoozed_flows": dict(self._state.snoozed_flows),
            "acknowledged_notifications": dict(self._state.acknowledged_notifications),
            "traces": list(self._state.traces),
            "recent_notifications": list(self._state.recent_notifications),
        }

    def async_set_queue_size(self, size: int) -> None:
        """Update the queue-size metric and publish a new snapshot."""
        self._state.queue_size = size
        self.async_set_updated_data(self.data | {"queue_size": size} if self.data else {"queue_size": size})

    def is_flow_enabled(self, flow_name: str) -> bool:
        """Return the effective enabled state for a flow."""
        if snoozed_until := self._state.snoozed_flows.get(flow_name):
            until = dt_util.parse_datetime(snoozed_until)
            if until is not None and until > dt_util.now():
                return False
            if until is not None and until <= dt_util.now():
                self._state.snoozed_flows.pop(flow_name, None)
        if flow_name in self._state.flow_overrides:
            return self._state.flow_overrides[flow_name]
        return self.config.flows[flow_name].enabled

    async def async_shutdown(self) -> None:
        """Release runtime resources on unload."""
        for unsubscribe in self._event_unsubs:
            unsubscribe()
        self._event_unsubs.clear()
        await self.queue.async_flush_now()
        await self._store.async_save(self._state.to_dict())

    def _should_summarize(self, flow, notifications: list[NotificationContext]) -> bool:
        """Decide whether a queue group should be summarized."""
        if len(notifications) <= 1 or not flow.allow_summary:
            return False
        highest = max(severity_rank(item.level) for item in notifications)
        return highest < severity_rank("critical")

    async def _async_build_summary_context(
        self,
        flow,
        notifications: list[NotificationContext],
    ) -> NotificationContext:
        """Build a summary context from several queued notifications."""
        personality = (
            flow.summary_personality
            or notifications[0].personality
            or flow.personality
            or DEFAULT_PERSONALITY
        )
        now_iso = dt_util.now().isoformat()
        summary_payload = await self.ai_client.async_summarize_notifications(
            notifications,
            language="ru",
            personality=personality,
        )
        return NotificationContext(
            flow=flow.name,
            title=summary_payload["title"],
            message=summary_payload["message"],
            level=flow.severity,
            source="queue_summary",
            timestamp=now_iso,
            notification_id=ensure_notification_id(None, flow.name, now_iso),
            metadata={"grouped": len(notifications)},
            rewrite=True,
            summarize=False,
            personality=personality,
        )

    def _record_delivery(
        self,
        context: NotificationContext,
        results: list[dict[str, Any]],
        *,
        grouped_count: int,
    ) -> None:
        """Record one delivered notification for sensors and diagnostics."""
        self._reset_daily_counters_if_needed()
        delivered_channels = [result["channel"] for result in results if result["status"] == "sent"]
        self._state.notifications_today += 1
        last_notification = {
            "title": context.title,
            "message": context.message,
            "level": context.level,
            "flow": context.flow,
            "notification_id": context.notification_id,
            "timestamp": context.timestamp,
            "source": context.source,
            "channels": delivered_channels,
            "grouped_count": grouped_count,
            "acknowledged": context.notification_id in self._state.acknowledged_notifications,
            "results": results,
        }
        self._state.last_notification = last_notification
        self._state.recent_notifications = (
            [last_notification] + self._state.recent_notifications
        )[: int(self.config.router.get("recent_limit", 20))]
        self._append_trace(
            {
                "stage": "delivered",
                "flow": context.flow,
                "level": context.level,
                "notification_id": context.notification_id,
                "channels": delivered_channels,
                "grouped_count": grouped_count,
            }
        )
        self.hass.async_create_task(self._async_persist_and_publish())

    async def _async_persist_and_publish(self) -> None:
        """Persist runtime state and publish an updated coordinator snapshot."""
        await self._store.async_save(self._state.to_dict())
        await self.async_request_refresh()

    def _build_snapshot(self, presence) -> dict[str, Any]:
        """Build the sensor snapshot payload."""
        return {
            "notifications_today": self._state.notifications_today,
            "queue_size": self._state.queue_size,
            "last_notification": self._state.last_notification,
            "recent_notifications": self._state.recent_notifications,
            "flow_states": {
                name: self.is_flow_enabled(name)
                for name in self.config.flows
            },
            "snoozed_flows": dict(self._state.snoozed_flows),
            "acknowledged_count": len(self._state.acknowledged_notifications),
            "quiet_hours": presence.quiet_hours,
            "home_mode": presence.home_mode,
            "people_home": presence.people_home,
            "status": self._runtime_status(presence),
        }

    def _reset_daily_counters_if_needed(self) -> None:
        """Reset the daily counter when the date changes."""
        today = dt_util.now().date().isoformat()
        if self._state.current_day != today:
            self._state.current_day = today
            self._state.notifications_today = 0

    def _augment_runtime_config(self) -> None:
        """Autodiscover a few legacy channels to ease migration."""
        if (
            "voice_auto" not in self.config.channels
            and self.hass.states.get("group.voice_notification_targets") is not None
            and "yandex_station_say" in self.hass.services.async_services().get("tts", {})
        ):
            from .models import ChannelConfig

            self.config.channels["voice_auto"] = ChannelConfig(
                name="voice_auto",
                channel_type="tts",
                service="tts.yandex_station_say",
                entity_id="group.voice_notification_targets",
            )
            for flow in self.config.flows.values():
                if "voice_auto" not in flow.channels:
                    flow.channels.append("voice_auto")

    def _append_trace(self, item: dict[str, Any]) -> None:
        """Append a trace item to the bounded trace buffer."""
        payload = {"timestamp": dt_util.now().isoformat(), **item}
        self._state.traces = (
            [payload] + self._state.traces
        )[: int(self.config.router.get("trace_limit", 100))]

    def _register_event_listeners(self) -> None:
        """Listen for actionable-notification callbacks once."""
        if self._event_unsubs:
            return
        self._event_unsubs = [
            self.hass.bus.async_listen(EVENT_MOBILE_ACTION, self._async_handle_mobile_action_event),
            self.hass.bus.async_listen(EVENT_MOBILE_CLEARED, self._async_handle_mobile_cleared_event),
            self.hass.bus.async_listen(EVENT_TELEGRAM_CALLBACK, self._async_handle_telegram_callback_event),
        ]

    async def _async_handle_mobile_action_event(self, event: Event) -> None:
        """Process Home Assistant companion action events."""
        payload = parse_action_token(event.data.get("action"))
        if payload is None:
            return
        actor = event.context.user_id if event.context else None
        await self._async_apply_action_payload(payload, actor=actor, source=EVENT_MOBILE_ACTION)

    async def _async_handle_mobile_cleared_event(self, event: Event) -> None:
        """Track notification dismissals from the mobile app."""
        notification_id = (
            event.data.get("tag")
            or dict(event.data.get("data", {})).get("tag")
            or event.data.get("notification_id")
        )
        if not notification_id:
            return
        self._mark_notification_cleared(str(notification_id), source=EVENT_MOBILE_CLEARED)
        await self._async_persist_and_publish()

    async def _async_handle_telegram_callback_event(self, event: Event) -> None:
        """Process Telegram inline-keyboard callbacks."""
        payload = parse_action_token(event.data.get("command"))
        if payload is None:
            return
        actor = str(event.data.get("chat_id") or event.data.get("user_id") or "telegram")
        await self._async_apply_action_payload(payload, actor=actor, source=EVENT_TELEGRAM_CALLBACK)
        callback_id = event.data.get("id")
        if callback_id:
            try:
                await self.hass.services.async_call(
                    "telegram_bot",
                    "answer_callback_query",
                    {
                        "callback_query_id": callback_id,
                        "message": action_feedback_text(
                            language=self._resolve_action_language(
                                payload.get("notification_id"),
                                fallback=normalize_language(
                                    event.data.get("language") or event.data.get("language_code")
                                ),
                            ),
                            kind=str(payload["kind"]),
                            minutes=int(payload["minutes"]) if payload["kind"] == "snooze" else None,
                        ),
                    },
                    blocking=True,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Telegram callback acknowledgement failed: %s", err)

    async def _async_apply_action_payload(
        self,
        payload: dict[str, Any],
        *,
        actor: str | None,
        source: str,
    ) -> None:
        """Apply a parsed user action from mobile, Telegram, or direct services."""
        if payload["kind"] == "ack":
            notification_id = str(payload["notification_id"])
            await self.async_acknowledge(notification_id, actor=actor, source=source)
            return
        if payload["kind"] == "snooze":
            await self.async_snooze_flow(
                str(payload["flow"]),
                minutes=int(payload["minutes"]),
                actor=actor,
                source=source,
                notification_id=str(payload["notification_id"]),
            )

    async def _async_emit_action_feedback(
        self,
        notification_id: str,
        *,
        kind: str,
        minutes: int | None = None,
    ) -> None:
        """Clear or acknowledge notification artifacts on feedback-capable channels."""
        notification = self._find_notification(notification_id)
        if notification is None:
            return

        for result in notification.get("results", []):
            if result.get("status") != "sent":
                continue
            if result.get("type") != "mobile_app":
                continue
            channel = self.config.channels.get(result.get("channel", ""))
            if channel is None or not channel.service:
                continue
            try:
                await self.hass.services.async_call(
                    *channel.service.split(".", maxsplit=1),
                    {
                        "message": "clear_notification",
                        "data": {"tag": notification_id},
                    },
                    blocking=True,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Mobile feedback clear failed for %s: %s", channel.name, err)
        self._append_trace(
            {
                "stage": "feedback",
                "notification_id": notification_id,
                "kind": kind,
                "minutes": minutes,
            }
        )

    def _find_notification(self, notification_id: str) -> dict[str, Any] | None:
        """Return the latest known notification state by id."""
        if self._state.last_notification.get("notification_id") == notification_id:
            return self._state.last_notification
        for item in self._state.recent_notifications:
            if item.get("notification_id") == notification_id:
                return item
        return None

    def _resolve_action_language(self, notification_id: Any, *, fallback: str = "ru") -> str:
        """Resolve a user-facing language for action feedback."""
        if not notification_id:
            return fallback
        notification = self._find_notification(str(notification_id))
        if notification is None:
            return fallback
        for result in notification.get("results", []):
            language = result.get("language")
            if language:
                return str(language)
        return fallback

    def _mark_notification_cleared(self, notification_id: str, *, source: str) -> None:
        """Mark a delivered notification as dismissed from a device."""
        stamp = dt_util.now().isoformat()
        if self._state.last_notification.get("notification_id") == notification_id:
            self._state.last_notification["cleared"] = True
            self._state.last_notification["cleared_at"] = stamp
        for item in self._state.recent_notifications:
            if item.get("notification_id") == notification_id:
                item["cleared"] = True
                item["cleared_at"] = stamp
        self._append_trace(
            {
                "stage": "cleared",
                "notification_id": notification_id,
                "source": source,
            }
        )

    def _runtime_status(self, presence) -> str:
        """Return a compact runtime status label for status sensors and UI."""
        if self._state.queue_size:
            return "busy"
        if presence.quiet_hours:
            return "quiet_hours"
        if not presence.people_home:
            return "away"
        return "ready"

    def _build_dashboard_yaml(self, *, title: str, preset: str) -> str:
        """Render a starter dashboard based on the selected preset."""
        language_entities = [
            user.language_helper
            for user in self.config.users.values()
            if user.language_helper
        ]
        language_yaml = "\n".join(
            f"            - {entity}"
            for entity in language_entities
        ) or "            - input_select.herald_language_alex"

        cards: list[str] = [
            f"""      - type: custom:herald-card
        title: Herald Notification Center
        today_entity: sensor.herald_notifications_today
        last_entity: sensor.herald_last_notification
        queue_entity: sensor.herald_queue_size
        language_entities:
{language_yaml}""",
            """      - type: entities
        title: Statistics
        show_header_toggle: false
        entities:
          - sensor.herald_status
          - sensor.herald_notifications_today
          - sensor.herald_last_notification
          - sensor.herald_queue_size""",
        ]

        if preset == "rooms":
            room_cards = "\n".join(
                f"""          - type: tile
            entity: {entity_id}
            name: {room_name.replace('_', ' ').title()}"""
                for room_name, entity_id in sorted(self.config.presence.get("room_sensors", {}).items())
            ) or """          - type: markdown
            content: 'No room sensors configured yet.'"""
            cards.append(
                f"""      - type: grid
        title: Room Presence
        columns: 2
        square: false
        cards:
{room_cards}"""
            )
        elif preset == "roles":
            for user in self.config.users.values():
                entities = [
                    "sensor.herald_status",
                    "sensor.herald_queue_size",
                ]
                if user.language_helper:
                    entities.append(user.language_helper)
                cards.append(
                    """      - type: entities
        title: {title}
        show_header_toggle: false
        entities:
{entities}""".format(
                        title=f"User · {user.name}",
                        entities="\n".join(f"          - {entity}" for entity in entities),
                    )
                )

        cards.append(
            f"""      - type: markdown
        content: >
          Load the frontend resource from {FRONTEND_MODULE_URL}. Use `herald.set_flow_state`
          to mute flows, `herald.notify` for test events, `herald.acknowledge` for action
          loops, and `herald.snooze_flow` for temporary silencing."""
        )

        return """title: {title}
views:
  - title: Herald
    path: herald
    icon: mdi:bell-badge
    cards:
{cards}
""".format(title=title, cards="\n".join(cards))

    @staticmethod
    def _write_text_file(path: str, content: str) -> None:
        """Write a UTF-8 text file, creating missing parent directories."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
