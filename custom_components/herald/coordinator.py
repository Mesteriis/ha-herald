"""Coordinator for Herald notification state and dispatch."""

from __future__ import annotations

import hashlib
import logging
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .actions import ensure_notification_id, parse_action_token
from .ai import HeraldAIClient
from .characters import CharacterManager
from .const import (
    CONF_COOLDOWN,
    CONF_DEDUP_WINDOW,
    CONF_MAINTENANCE_MIN_LEVEL,
    CONF_MAINTENANCE_MODE_ENTITY,
    DATA_FRONTEND_REGISTRATION,
    DEFAULT_DASHBOARD_PRESET,
    DEFAULT_MAINTENANCE_MIN_LEVEL,
    DEFAULT_PERSONALITY,
    DOMAIN,
    EVENT_MOBILE_ACTION,
    EVENT_MOBILE_CLEARED,
    EVENT_TELEGRAM_CALLBACK,
    FRONTEND_DASHBOARD_TITLE,
    FRONTEND_MODULE_URL,
    STORAGE_KEY,
    STORAGE_VERSION,
    topology_signal,
)
from .context_builder import HeraldContextBuilder
from .controls import (
    HeraldControlManager,
    dashboard_sidebar_control_key,
    flow_enabled_control_key,
    maintenance_mode_control_key,
    room_audio_target_entity_id,
    room_presence_entity_id,
    room_presence_sensor_entity_id,
)
from .discovery import discover_runtime_channels
from .flows import async_flow_matches, resolve_requested_flow, severity_rank
from .models import ChannelConfig, FlowConfig, HeraldConfig, NotificationContext, RuntimeState
from .plugins import HeraldPluginManager
from .presence import PresenceResolver
from .queue import NotificationQueueManager
from .request import HeraldRequest
from .router import HeraldRouter
from .translations import action_feedback_text, normalize_language, runtime_control_change_text

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
        self._raw_config = deepcopy(raw_config)
        self.config = HeraldConfig.from_raw(self._raw_config)
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY}.{entry.entry_id}",
        )
        self._state = RuntimeState(current_day=dt_util.now().date().isoformat())
        self._session = async_get_clientsession(hass)
        self.presence = PresenceResolver(hass, self.config)
        self.characters = CharacterManager(hass)
        self.plugins = HeraldPluginManager(hass)
        self.controls = HeraldControlManager(
            hass,
            self.config,
            self.presence,
            self.characters,
            lambda: self._state,
        )
        self.presence.attach_controls(self.controls)
        self.context_builder = HeraldContextBuilder(hass, self.config, self.presence, self.controls)
        self.ai_client = HeraldAIClient(hass, self._session, self.config, self.characters, self.controls)
        self.router = HeraldRouter(
            hass,
            self.config,
            self.ai_client,
            self.presence,
            self.controls,
            self._record_dashboard_delivery,
        )
        self.queue = NotificationQueueManager(self)
        self._event_unsubs: list[Any] = []
        self._control_snapshot: dict[str, Any] = {}
        self._topology_snapshot: dict[str, Any] = {}

    async def _async_setup(self) -> None:
        """Load persistent state and augment autodiscovered channels."""
        if stored := await self._store.async_load():
            self._state = RuntimeState.from_dict(stored)
        queue_state_reset = self._reset_queue_runtime_state()
        self._reset_daily_counters_if_needed()
        await self._async_refresh_runtime_sources()
        self._augment_runtime_config()
        if self._sync_controls() or queue_state_reset:
            await self._store.async_save(self._state.to_dict())
        self._register_event_listeners()

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the coordinator snapshot consumed by sensors."""
        await self._async_refresh_runtime_sources()
        self._augment_runtime_config()
        if self._sync_controls():
            await self._store.async_save(self._state.to_dict())
        presence = await self.presence.async_resolve(
            NotificationContext(
                flow="system_events",
                event="snapshot",
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
        await self._async_refresh_runtime_sources()
        self._augment_runtime_config()
        self._sync_controls()
        request = HeraldRequest.from_service_data(data)
        runtime_context = await self.context_builder.async_build(request)
        level = request.level
        requested_flow = request.legacy_flow
        flow_name = resolve_requested_flow(self.config.flows, requested_flow, level)
        flow = self.config.flows[flow_name]
        self._append_trace(
            {
                "stage": "event",
                "event": request.event,
                "level": request.level,
                "group": request.group,
                "immediately": request.immediately,
            }
        )
        self._append_trace(
            {
                "stage": "context_builder",
                "event": request.event,
                "context": runtime_context.to_dict(),
            }
        )
        self._append_trace(
            {
                "stage": "flow_resolver",
                "event": request.event,
                "requested_flow": requested_flow,
                "resolved_flow": flow_name,
                "level": level,
            }
        )
        if not request.force and not self._level_enabled(level):
            self._record_drop_metric(
                reason="level_disabled",
                flow=flow_name,
                level=level,
            )
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "level_disabled",
                    "flow": flow_name,
                    "level": level,
                    "message": request.message,
                }
            )
            await self._async_persist_and_publish()
            return
        if not self.is_flow_enabled(flow_name) and not request.force:
            self._record_drop_metric(
                reason="flow_disabled",
                flow=flow_name,
                level=level,
            )
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "flow_disabled",
                    "flow": flow_name,
                    "level": level,
                    "message": request.message,
                }
            )
            await self._async_persist_and_publish()
            return

        now_iso = dt_util.now().isoformat()
        audience_users = request.legacy_users or [
            user.person_entity_id
            for user in runtime_context.users
            if user.home and not user.silent
        ]
        resolved_user = request.legacy_user or (audience_users[0] if audience_users else None)
        resolved_room = request.legacy_room or (
            runtime_context.room_for_user(resolved_user)
            if resolved_user and len(audience_users) <= 1
            else runtime_context.primary_room
        )
        context_payload = dict(request.context or {})
        ai_context = dict(request.ai.context) if request.ai and request.ai.context else {}
        if ai_context:
            context_payload["ai_context"] = dict(ai_context)
        context_payload.update(runtime_context.to_dict())
        context = NotificationContext(
            flow=flow_name,
            event=request.event,
            title=request.event,
            message=request.message,
            level=level,
            source=request.source,
            timestamp=now_iso,
            notification_id=ensure_notification_id(request.notification_id, flow_name, now_iso),
            automation_id=request.metadata.get("automation_id"),
            device=(request.entities[0] if request.entities else None),
            room=resolved_room,
            user=resolved_user,
            users=audience_users,
            channels=list(request.legacy_channels),
            entities=list(request.entities or []),
            context_data=context_payload,
            ai_context=ai_context,
            metadata=dict(request.metadata),
            character=request.ai.character if request.ai else None,
            personality=request.ai.character if request.ai else None,
            group=request.group,
            suppress_seconds=request.suppress,
            immediately=request.immediately,
            rewrite=request.rewrite,
            summarize=request.summarize,
            force=request.force,
            include_actions=bool(request.include_actions or severity_rank(level) >= severity_rank("warning")),
        )

        if not context.users and context.user:
            context.users = [context.user]
        self._append_trace(
            {
                "stage": "ai_decision",
                "event": context.event,
                "flow": flow_name,
                "level": level,
                "character": context.character or DEFAULT_PERSONALITY,
                "ai_enabled": self.ai_client.should_use_ai(level),
            }
        )

        matches = await async_flow_matches(
            self.hass,
            flow,
            context,
            home_mode_entity=self.config.presence.get("home_mode_entity"),
        )
        if not matches and not context.force:
            self._record_drop_metric(
                reason="conditions_not_met",
                flow=flow_name,
                level=context.level,
            )
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

        if not context.force and self._drop_for_maintenance(context):
            self._record_drop_metric(
                reason="maintenance_mode",
                flow=flow_name,
                level=context.level,
            )
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "maintenance_mode",
                    "flow": flow_name,
                    "level": context.level,
                    "message": context.message,
                }
            )
            await self._async_persist_and_publish()
            return

        if not context.force and self._drop_for_mute_all(context):
            self._record_drop_metric(
                reason="mute_all",
                flow=flow_name,
                level=context.level,
            )
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "mute_all",
                    "flow": flow_name,
                    "level": context.level,
                    "message": context.message,
                }
            )
            await self._async_persist_and_publish()
            return

        if not context.force and self._drop_for_dedup(flow, context):
            self._record_drop_metric(
                reason="deduplicated",
                flow=flow_name,
                level=context.level,
            )
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "deduplicated",
                    "flow": flow_name,
                    "level": context.level,
                    "message": context.message,
                    "window_seconds": flow.dedup_window_seconds,
                }
            )
            await self._async_persist_and_publish()
            return

        if not context.force and self._drop_for_cooldown(flow_name, flow):
            self._record_drop_metric(
                reason="flow_cooldown",
                flow=flow_name,
                level=context.level,
            )
            self._append_trace(
                {
                    "stage": "drop",
                    "reason": "flow_cooldown",
                    "flow": flow_name,
                    "level": context.level,
                    "message": context.message,
                    "cooldown_seconds": flow.cooldown_seconds,
                }
            )
            await self._async_persist_and_publish()
            return

        self._append_trace(
            {
                "stage": "queue",
                "event": context.event,
                "flow": flow_name,
                "notification_id": context.notification_id,
                "group": context.group,
                "immediately": context.immediately,
                "summary_window_seconds": 0
                if context.immediately
                else flow.summary_window_seconds if context.summarize else 0,
            }
        )
        self._append_trace(
            {
                "stage": "enqueue",
                "flow": flow_name,
                "level": context.level,
                "event": context.event,
                "title": context.title,
                "message": context.message,
                "notification_id": context.notification_id,
                "channels": context.channels,
            }
        )
        await self.queue.async_enqueue(
            context,
            summary_window_seconds=(
                0 if context.immediately else flow.summary_window_seconds if context.summarize else 0
            ),
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
        content = yaml.safe_dump(
            self.build_dashboard_config(title=title, preset=preset),
            allow_unicode=True,
            sort_keys=False,
        )
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
        self.controls.set_value(flow_enabled_control_key(flow_name), enabled)
        self._append_trace(
            {
                "stage": "flow_override",
                "flow": flow_name,
                "enabled": enabled,
            }
        )
        await self._async_persist_and_publish()
        message = runtime_control_change_text(
            language=self._preferred_announcement_language(),
            key=flow_enabled_control_key(flow_name),
            value=enabled,
        )
        if message:
            await self._async_announce_self_action(
                message=message,
                level="info",
                event="Herald",
                metadata={"herald_runtime_key": flow_enabled_control_key(flow_name)},
            )

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
        for item in self._state.dashboard_feed:
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
        await self._async_announce_self_action(
            message=action_feedback_text(
                language=self._preferred_announcement_language(),
                kind="ack",
            ),
            level="info",
            event="Herald",
            metadata={"herald_runtime_action": "acknowledge"},
        )

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
        await self._async_announce_self_action(
            message=action_feedback_text(
                language=self._preferred_announcement_language(),
                kind="snooze",
                minutes=minutes,
            ),
            level="info",
            event="Herald",
            metadata={
                "herald_runtime_action": "snooze",
                "flow": flow_name,
                "minutes": minutes,
            },
        )

    def trace_snapshot(self) -> dict[str, Any]:
        """Return recent traces for service responses and diagnostics."""
        return {
            "entry_id": self.entry.entry_id,
            "characters": self.characters.list_character_keys(),
            "plugins": self.plugins.diagnostic_summary(),
            "control_entities": self._control_summary(),
            "helper_bootstrap": self._control_summary(),
            "control_values": dict(self._state.control_values),
            "room_presence_sensors": {
                room_name: room_presence_sensor_entity_id(room_name)
                for room_name in sorted(self.presence.room_sensors())
            },
            "snoozed_flows": dict(self._state.snoozed_flows),
            "acknowledged_notifications": dict(self._state.acknowledged_notifications),
            "traces": list(self._state.traces),
            "recent_notifications": list(self._state.recent_notifications),
            "dashboard_feed": list(self._state.dashboard_feed),
            "queued_notifications": list(self._state.queued_notifications),
            "analytics": {
                "deliveries_today": self._state.deliveries_today,
                "dropped_today": self._state.dropped_today,
                "errors_today": self._state.errors_today,
                "ai_requests_today": self._state.ai_requests_today,
                "channel_delivery_counts": dict(self._state.channel_delivery_counts),
                "channel_error_counts": dict(self._state.channel_error_counts),
                "drop_reasons": dict(self._state.drop_reasons),
                "ai_character_counts": dict(self._state.ai_character_counts),
            },
        }

    def async_set_queue_state(self, items: list[dict[str, Any]]) -> None:
        """Update queued-notification diagnostics and publish them immediately."""
        self._state.queued_notifications = list(items)
        self._state.queue_size = len(items)
        payload = dict(self.data or {})
        payload.update(
            {
                "queue_size": self._state.queue_size,
                "queued_notifications": list(self._state.queued_notifications),
                "status": payload.get("status", "busy" if self._state.queue_size else "ready"),
            }
        )
        self.async_set_updated_data(payload)

    def async_set_queue_size(self, size: int) -> None:
        """Backwards-compatible wrapper for queue-size-only updates."""
        if size <= 0:
            self.async_set_queue_state([])
            return
        self._state.queue_size = size
        payload = dict(self.data or {})
        payload.update(
            {
                "queue_size": size,
                "queued_notifications": list(self._state.queued_notifications),
                "status": payload.get("status", "busy"),
            }
        )
        self.async_set_updated_data(payload)

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

    async def async_set_control_value(self, key: str, value: Any) -> None:
        """Update one Herald-owned runtime control value."""
        previous_value = self.controls.value(key)
        if not self.controls.set_value(key, value):
            return
        if key == maintenance_mode_control_key():
            await self._async_sync_external_maintenance_entity(bool(value))
        if key == dashboard_sidebar_control_key():
            await self._async_sync_dashboard_sidebar(bool(value))
        self._append_trace(
            {
                "stage": "control",
                "key": key,
                "value": value,
            }
        )
        await self._async_persist_and_publish()
        await self._async_announce_control_change(
            key,
            previous_value=previous_value,
            value=self.controls.value(key),
        )

    async def async_press_control_button(self, key: str) -> None:
        """Execute one Herald-owned button action."""
        spec = self.controls.spec(key)
        if spec is None or spec.platform != "button":
            return
        self._append_trace(
            {
                "stage": "control_button",
                "key": key,
                "entity_id": spec.entity_id,
            }
        )
        if key.startswith("test_channel:"):
            await self.async_run_channel_test(key.split(":", maxsplit=1)[1])
            return
        if key.startswith("test_level:"):
            await self.async_run_level_test(key.split(":", maxsplit=1)[1])
            return
        await self._async_persist_and_publish()

    async def async_run_channel_test(self, channel_name: str) -> None:
        """Send an explicit control-plane test message to one concrete channel."""
        channel = self.config.channels.get(channel_name)
        level = "info"
        if channel is not None and channel.min_level in {"warning", "critical"}:
            level = channel.min_level
        await self.async_handle_service_notify(
            {
                "event": f"channel_test_{channel_name}",
                "message": f"Herald control-plane test for channel {channel_name}",
                "level": level,
                "channels": [channel_name],
                "source": "herald.control_test.channel",
                "group": "control_tests",
                "force": True,
                "rewrite": False,
                "summarize": False,
                "include_actions": False,
                "metadata": {
                    "control_test": "channel",
                    "control_test_channel": channel_name,
                },
            }
        )

    async def async_run_level_test(self, level: str) -> None:
        """Send a routing test for one severity level through the normal flow pipeline."""
        await self.async_handle_service_notify(
            {
                "event": f"level_test_{level}",
                "message": f"Herald control-plane test for level {level}",
                "level": level,
                "flow": "system_events",
                "source": "herald.control_test.level",
                "group": "control_tests",
                "force": True,
                "rewrite": False,
                "summarize": False,
                "include_actions": False,
                "metadata": {
                    "control_test": "level",
                    "control_test_level": level,
                },
            }
        )

    async def _async_announce_control_change(
        self,
        key: str,
        *,
        previous_value: Any,
        value: Any,
    ) -> None:
        """Announce Herald control-plane changes over voice-capable channels."""
        if previous_value == value:
            return
        language = self._preferred_announcement_language()
        message = runtime_control_change_text(
            language=language,
            key=key,
            value=value,
        )
        if not message:
            return
        await self._async_announce_self_action(
            message=message,
            level="info",
            event="Herald",
            metadata={"herald_runtime_key": key},
        )

    async def async_shutdown(self) -> None:
        """Release runtime resources on unload."""
        for unsubscribe in self._event_unsubs:
            unsubscribe()
        self._event_unsubs.clear()
        await self.queue.async_flush_now()
        await self._store.async_save(self._state.to_dict())

    async def _async_refresh_runtime_sources(self) -> None:
        """Refresh filesystem-backed topology inputs before routing or snapshots."""
        await self.characters.async_initialize()
        await self.plugins.async_initialize()

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
            character=personality,
            render_context={
                "event": flow.name,
                "room": notifications[0].room,
                "people": notifications[0].users,
                "context": notifications[0].context_data,
            },
        )
        return NotificationContext(
            flow=flow.name,
            event=flow.name,
            title=summary_payload["title"],
            message=summary_payload["message"],
            level=flow.severity,
            source="queue_summary",
            timestamp=now_iso,
            notification_id=ensure_notification_id(None, flow.name, now_iso),
            users=list(notifications[0].users),
            room=notifications[0].room,
            entities=list(notifications[0].entities),
            context_data=dict(notifications[0].context_data),
            metadata={"grouped": len(notifications)},
            character=personality,
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
        self._record_result_metrics(context, results)
        self._state.notifications_today += 1
        if delivered_channels:
            self._state.last_flow_delivery[context.flow] = dt_util.now().isoformat()
        last_notification = {
            "event": context.event,
            "title": context.title,
            "message": context.message,
            "level": context.level,
            "flow": context.flow,
            "notification_id": context.notification_id,
            "timestamp": context.timestamp,
            "source": context.source,
            "character": context.character or context.personality,
            "group": context.group,
            "entities": list(context.entities),
            "context": dict(context.context_data),
            "ai_context": dict(context.ai_context),
            "channels": delivered_channels,
            "grouped_count": grouped_count,
            "acknowledged": context.notification_id in self._state.acknowledged_notifications,
            "results": results,
        }
        self._state.last_notification = last_notification
        self._state.recent_notifications = (
            [last_notification] + self._state.recent_notifications
        )[: self._history_limit()]
        self._append_trace(
            {
                "stage": "delivered",
                "flow": context.flow,
                "event": context.event,
                "level": context.level,
                "notification_id": context.notification_id,
                "channels": delivered_channels,
                "grouped_count": grouped_count,
            }
        )
        self.hass.async_create_task(self._async_persist_and_publish())

    def _record_result_metrics(
        self,
        context: NotificationContext,
        results: list[dict[str, Any]],
    ) -> None:
        """Update analytics counters from routing results."""
        if context.rewrite and self.ai_client.should_use_ai(context.level):
            self._state.ai_requests_today += 1
            character_key = str(context.character or context.personality or DEFAULT_PERSONALITY)
            self._state.ai_character_counts[character_key] = (
                self._state.ai_character_counts.get(character_key, 0) + 1
            )

        for result in results:
            channel_name = str(result.get("channel", "unknown"))
            status = str(result.get("status", "unknown"))
            if status == "sent":
                self._state.deliveries_today += 1
                self._state.channel_delivery_counts[channel_name] = (
                    self._state.channel_delivery_counts.get(channel_name, 0) + 1
                )
                continue
            if status == "error":
                self._state.errors_today += 1
                self._state.channel_error_counts[channel_name] = (
                    self._state.channel_error_counts.get(channel_name, 0) + 1
                )
                continue
            if status == "dropped":
                self._state.dropped_today += 1
                reason = str(result.get("reason", "channel_dropped"))
                self._state.drop_reasons[reason] = self._state.drop_reasons.get(reason, 0) + 1

    def _record_drop_metric(self, *, reason: str, flow: str, level: str) -> None:
        """Track drops that happen before routing starts."""
        self._reset_daily_counters_if_needed()
        self._state.dropped_today += 1
        self._state.drop_reasons[reason] = self._state.drop_reasons.get(reason, 0) + 1
        self._append_trace(
            {
                "stage": "analytics_drop",
                "reason": reason,
                "flow": flow,
                "level": level,
            }
        )

    def _record_dashboard_delivery(
        self,
        *,
        channel,
        title: str,
        message: str,
        language: str,
        context: NotificationContext,
        presence,
    ) -> dict[str, Any]:
        """Persist one dashboard-feed item for a dashboard channel delivery."""
        raw = "\x1f".join(
            (
                channel.name,
                context.notification_id,
                context.timestamp,
                title,
                message,
            )
        )
        entry_id = hashlib.sha1(raw.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
        feed_item = {
            "entry_id": entry_id,
            "channel": channel.name,
            "event": context.event,
            "title": title,
            "message": message,
            "level": context.level,
            "flow": context.flow,
            "notification_id": context.notification_id,
            "timestamp": context.timestamp,
            "source": context.source,
            "language": language,
            "character": context.character or context.personality,
            "group": context.group,
            "room": context.room or presence.primary_room,
            "user": channel.user or context.user,
            "users": list(context.users),
            "entities": list(context.entities),
            "context": dict(context.context_data),
            "ai_context": dict(context.ai_context),
            "acknowledged": context.notification_id in self._state.acknowledged_notifications,
            "cleared": False,
        }
        self._state.dashboard_feed = [feed_item] + self._state.dashboard_feed[: self._history_limit() - 1]
        self._append_trace(
            {
                "stage": "dashboard_feed",
                "channel": channel.name,
                "event": context.event,
                "notification_id": context.notification_id,
                "entry_id": entry_id,
            }
        )
        return {"feed_entry_id": entry_id}

    async def _async_persist_and_publish(self) -> None:
        """Persist runtime state and publish an updated coordinator snapshot."""
        await self._store.async_save(self._state.to_dict())
        await self.async_request_refresh()

    def _build_snapshot(self, presence) -> dict[str, Any]:
        """Build the sensor snapshot payload."""
        return {
            "notifications_today": self._state.notifications_today,
            "deliveries_today": self._state.deliveries_today,
            "dropped_today": self._state.dropped_today,
            "errors_today": self._state.errors_today,
            "ai_requests_today": self._state.ai_requests_today,
            "queue_size": self._state.queue_size,
            "queued_notifications": list(self._state.queued_notifications),
            "last_notification": self._state.last_notification,
            "recent_notifications": self._state.recent_notifications,
            "dashboard_feed": list(self._state.dashboard_feed),
            "flow_states": {
                name: self.is_flow_enabled(name)
                for name in self.config.flows
            },
            "snoozed_flows": dict(self._state.snoozed_flows),
            "acknowledged_count": len(self._state.acknowledged_notifications),
            "quiet_hours": presence.quiet_hours,
            "home_mode": presence.home_mode,
            "people_home": presence.people_home,
            "maintenance_mode": self._maintenance_mode_active(),
            "mute_all": self.controls.is_mute_all_enabled(),
            "maintenance_min_level": self.config.router.get(
                CONF_MAINTENANCE_MIN_LEVEL,
                DEFAULT_MAINTENANCE_MIN_LEVEL,
            ),
            "characters": self.characters.list_character_keys(),
            "plugins": self.plugins.diagnostic_summary(),
            "control_entities": self._control_summary(),
            "helper_bootstrap": self._control_summary(),
            "control_values": dict(self._state.control_values),
            "room_presence_sensors": {
                room_name: room_presence_sensor_entity_id(room_name)
                for room_name in sorted(self.presence.room_sensors())
            },
            "channel_policies": {
                name: {
                    "type": channel.channel_type,
                    "enabled": channel.enabled,
                    "min_level": channel.min_level,
                    "quiet_hours_policy": channel.quiet_hours_policy,
                }
                for name, channel in self.config.channels.items()
            },
            "flow_policies": {
                name: {
                    "enabled": flow.enabled,
                    "effective_enabled": self.is_flow_enabled(name),
                    "severity": flow.severity,
                    "allow_summary": flow.allow_summary,
                    "summary_window_seconds": flow.summary_window_seconds,
                    "dedup_window_seconds": flow.dedup_window_seconds,
                    "cooldown_seconds": flow.cooldown_seconds,
                }
                for name, flow in self.config.flows.items()
            },
            "analytics": {
                "deliveries_today": self._state.deliveries_today,
                "dropped_today": self._state.dropped_today,
                "errors_today": self._state.errors_today,
                "ai_requests_today": self._state.ai_requests_today,
                "channel_delivery_counts": dict(self._state.channel_delivery_counts),
                "channel_error_counts": dict(self._state.channel_error_counts),
                "drop_reasons": dict(self._state.drop_reasons),
                "ai_character_counts": dict(self._state.ai_character_counts),
            },
            "pipeline_trace": self._state.traces[:20],
            "status": self._runtime_status(presence),
        }

    def _reset_daily_counters_if_needed(self) -> None:
        """Reset the daily counter when the date changes."""
        today = dt_util.now().date().isoformat()
        if self._state.current_day != today:
            self._state.current_day = today
            self._state.notifications_today = 0
            self._state.deliveries_today = 0
            self._state.dropped_today = 0
            self._state.errors_today = 0
            self._state.ai_requests_today = 0
            self._state.channel_delivery_counts = {}
            self._state.channel_error_counts = {}
            self._state.drop_reasons = {}
            self._state.ai_character_counts = {}

    def _reset_queue_runtime_state(self) -> bool:
        """Clear ephemeral queue state restored from storage."""
        if not self._state.queue_size and not self._state.queued_notifications:
            return False
        self._state.queue_size = 0
        self._state.queued_notifications = []
        return True

    def _history_limit(self) -> int:
        """Return the bounded history length used by UI-facing lists."""
        return max(1, int(self.config.router.get("recent_limit", 20)))

    def _augment_runtime_config(self) -> None:
        """Autodiscover a few legacy channels to ease migration."""
        self._reset_runtime_config()

        for channel_name, payload in discover_runtime_channels(self.hass).items():
            if channel_name in self.config.channels:
                continue
            self.config.channels[channel_name] = ChannelConfig.from_dict(channel_name, payload)

        self.config.channels.setdefault(
            "dashboard_default",
            ChannelConfig(name="dashboard_default", channel_type="dashboard"),
        )
        self._apply_plugin_extensions()
        self._apply_default_tv_routing_rules()

    def _reset_runtime_config(self) -> None:
        """Restore the mutable config object from entry data before runtime augmentation."""
        fresh = HeraldConfig.from_raw(self._raw_config)
        self.config.name = fresh.name
        self.config.ollama = fresh.ollama
        self.config.channels = fresh.channels
        self.config.flows = fresh.flows
        self.config.users = fresh.users
        self.config.personalities = fresh.personalities
        self.config.quiet_hours = fresh.quiet_hours
        self.config.presence = fresh.presence
        self.config.router = fresh.router

    def _apply_plugin_extensions(self) -> None:
        """Merge plugin-defined channels, flows, prompts, and cards into runtime config."""
        for plugin in self.plugins.active_plugins():
            for channel_name, payload in plugin.channels.items():
                if channel_name in self.config.channels and not plugin.override_existing:
                    continue
                self.config.channels[channel_name] = ChannelConfig.from_dict(channel_name, payload)
            for flow_name, payload in plugin.flows.items():
                if flow_name in self.config.flows and not plugin.override_existing:
                    continue
                self.config.flows[flow_name] = FlowConfig.from_dict(flow_name, payload)
            for prompt_key, prompt in plugin.ai_prompts.items():
                if prompt_key in self.config.personalities and not plugin.override_existing:
                    continue
                self.config.personalities[prompt_key] = prompt

    def _apply_default_tv_routing_rules(self) -> None:
        """Add TV delivery to a small set of high-value flows when TV channels exist."""
        if "tv_auto" not in self.config.channels:
            return
        for flow_name in ("security_alerts", "camera_alerts", "timer_notifications"):
            flow = self.config.flows.get(flow_name)
            if flow is None or "tv_auto" in flow.channels:
                continue
            flow.channels.append("tv_auto")

    def _sync_controls(self) -> bool:
        """Ensure Herald-owned control state exists and is reflected in config."""
        changed = self.controls.ensure_defaults()
        payload = self._control_summary()
        if payload != self._control_snapshot:
            self._control_snapshot = payload
            self._append_trace(
                {
                    "stage": "controls",
                    "entities": payload,
                }
            )
            changed = True
        topology = self._topology_summary(payload)
        if topology != self._topology_snapshot:
            self._topology_snapshot = topology
            self._append_trace(
                {
                    "stage": "topology",
                    "summary": topology,
                }
            )
            async_dispatcher_send(self.hass, topology_signal(self.entry.entry_id))
            changed = True
        return changed

    def _control_summary(self) -> dict[str, list[str]]:
        """Return Herald-owned control entity ids for diagnostics and UI."""
        return self.controls.summary()

    def _topology_summary(self, control_payload: dict[str, list[str]]) -> dict[str, Any]:
        """Return the dynamic topology signature used for live entity materialization."""
        return {
            "controls": control_payload,
            "characters": self.characters.list_character_keys(),
            "plugins": self.plugins.list_plugin_keys(include_disabled=True),
        }

    def _level_enabled(self, level: str) -> bool:
        """Return whether a severity level is enabled by Herald helpers."""
        return self.controls.is_level_enabled(level)

    def _append_trace(self, item: dict[str, Any]) -> None:
        """Append a trace item to the bounded trace buffer."""
        payload = {"timestamp": dt_util.now().isoformat(), **item}
        self._state.traces = (
            [payload] + self._state.traces
        )[: int(self.config.router.get("trace_limit", 100))]

    def _maintenance_mode_active(self) -> bool:
        """Return True when maintenance mode is currently enabled."""
        if self.controls.maintenance_mode_enabled():
            return True
        return self._external_maintenance_mode_active()

    def _external_maintenance_mode_active(self) -> bool:
        """Return True when the legacy external maintenance entity is enabled."""
        entity_id = str(self.config.router.get(CONF_MAINTENANCE_MODE_ENTITY, "")).strip()
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        return state is not None and state.state == "on"

    def _drop_for_maintenance(self, context: NotificationContext) -> bool:
        """Check if the event should be suppressed during maintenance mode."""
        if not self._maintenance_mode_active():
            return False
        minimum = str(
            self.config.router.get(
                CONF_MAINTENANCE_MIN_LEVEL,
                DEFAULT_MAINTENANCE_MIN_LEVEL,
            )
        )
        return severity_rank(context.level) < severity_rank(minimum)

    def _drop_for_mute_all(self, context: NotificationContext) -> bool:
        """Check if the event should be suppressed by the global mute toggle."""
        if not self.controls.is_mute_all_enabled():
            return False
        return severity_rank(context.level) < severity_rank("critical")

    async def _async_sync_external_maintenance_entity(self, enabled: bool) -> None:
        """Best-effort sync to a legacy external maintenance helper when configured."""
        entity_id = str(self.config.router.get(CONF_MAINTENANCE_MODE_ENTITY, "")).strip()
        if not entity_id or entity_id == "switch.herald_maintenance_mode":
            return
        domain = entity_id.split(".", maxsplit=1)[0]
        if domain not in {"input_boolean", "switch"}:
            return
        service = "turn_on" if enabled else "turn_off"
        try:
            await self.hass.services.async_call(
                domain,
                service,
                {"entity_id": entity_id},
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Unable to sync external maintenance entity %s: %s", entity_id, err)

    def _voice_announcement_channels(self) -> list[str]:
        """Return all currently known voice-capable channels for whole-home runtime speech."""
        supported_types = {"tts", "tts_hume", "tv"}
        return [
            name
            for name, channel in self.config.channels.items()
            if channel.channel_type in supported_types
        ]

    def _preferred_announcement_language(self) -> str:
        """Return the preferred household language for runtime self-announcements."""
        async_all = getattr(self.hass.states, "async_all", None)
        if async_all is None:
            return "ru"
        for state in async_all("person"):
            if state.state != "home":
                continue
            slug = state.entity_id.split(".", maxsplit=1)[1]
            return normalize_language(self.controls.user_language(slug, default="ru"))
        return "ru"

    async def _async_sync_dashboard_sidebar(self, visible: bool) -> None:
        """Sync the Herald dashboard sidebar visibility into Lovelace storage/runtime."""
        registration = self.hass.data.get(DOMAIN, {}).get(DATA_FRONTEND_REGISTRATION)
        if registration is None:
            return
        async_set_sidebar_visibility = getattr(registration, "async_set_sidebar_visibility", None)
        if async_set_sidebar_visibility is None:
            return
        await async_set_sidebar_visibility(visible)

    def _someone_home_for_self_action(self) -> bool:
        """Return True when there is someone home to hear Herald self-announcements."""
        async_all = getattr(self.hass.states, "async_all", None)
        if async_all is None:
            return False
        return any(state.state == "home" for state in async_all("person"))

    async def _async_announce_self_action(
        self,
        *,
        message: str,
        level: str,
        event: str = "Herald",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send one voice-only Herald self-action announcement when somebody is home."""
        if not self._someone_home_for_self_action():
            return
        voice_channels = self._voice_announcement_channels()
        if not voice_channels:
            return
        payload_metadata = {
            "bypass_channel_policy": True,
            **dict(metadata or {}),
        }
        await self.async_handle_service_notify(
            {
                "event": event,
                "message": message,
                "level": level,
                "channels": voice_channels,
                "source": "herald.runtime",
                "group": "herald_runtime",
                "force": True,
                "rewrite": False,
                "summarize": False,
                "include_actions": False,
                "metadata": payload_metadata,
            }
        )

    def _drop_for_cooldown(self, flow_name: str, flow) -> bool:
        """Drop flow notifications while the delivery cooldown is active."""
        cooldown_seconds = max(0, int(getattr(flow, CONF_COOLDOWN, flow.cooldown_seconds)))
        if cooldown_seconds <= 0:
            return False
        last_delivery = self._state.last_flow_delivery.get(flow_name)
        if not last_delivery:
            return False
        last_delivery_dt = dt_util.parse_datetime(last_delivery)
        if last_delivery_dt is None:
            return False
        return (dt_util.now() - last_delivery_dt).total_seconds() < cooldown_seconds

    def _drop_for_dedup(self, flow, context: NotificationContext) -> bool:
        """Drop duplicate events inside the configured deduplication window."""
        dedup_window_seconds = (
            max(0, int(context.suppress_seconds))
            if context.suppress_seconds is not None
            else max(
                0,
                int(getattr(flow, CONF_DEDUP_WINDOW, flow.dedup_window_seconds)),
            )
        )
        if dedup_window_seconds <= 0:
            return False

        fingerprint = self._notification_fingerprint(context)
        now = dt_util.now()
        previous = self._state.dedup_cache.get(fingerprint)
        if previous:
            previous_dt = dt_util.parse_datetime(previous)
            if previous_dt is not None and (now - previous_dt).total_seconds() < dedup_window_seconds:
                return True
        self._state.dedup_cache[fingerprint] = now.isoformat()
        self._prune_dedup_cache(now)
        return False

    def _notification_fingerprint(self, context: NotificationContext) -> str:
        """Build a stable fingerprint for deduplication."""
        users = sorted({*context.users, *( [context.user] if context.user else [] )})
        raw = "\x1f".join(
            (
                context.flow,
                context.group or "",
                context.event,
                context.level,
                context.source,
                context.title.strip(),
                context.message.strip(),
                ",".join(users),
                ",".join(sorted(context.channels)),
            )
        )
        return hashlib.sha1(raw.encode("utf-8"), usedforsecurity=False).hexdigest()

    def _prune_dedup_cache(self, now) -> None:
        """Prune stale deduplication fingerprints from runtime state."""
        max_window = max(
            [int(flow.dedup_window_seconds) for flow in self.config.flows.values()] or [0]
        )
        if max_window <= 0:
            self._state.dedup_cache.clear()
            return
        cutoff = now - timedelta(seconds=max_window)
        self._state.dedup_cache = {
            fingerprint: stamp
            for fingerprint, stamp in self._state.dedup_cache.items()
            if (parsed := dt_util.parse_datetime(stamp)) is not None and parsed >= cutoff
        }

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
        for item in self._state.dashboard_feed:
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
        for item in self._state.dashboard_feed:
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
        if self.controls.is_mute_all_enabled():
            return "muted"
        if self._maintenance_mode_active():
            return "maintenance"
        if presence.quiet_hours:
            return "quiet_hours"
        if not presence.people_home:
            return "away"
        return "ready"

    def _build_dashboard_payload(self, *, title: str, preset: str) -> dict[str, Any]:
        """Render a storage-backed Lovelace dashboard payload."""
        control_summary = self._control_summary()
        room_definitions = [
            (
                room_name,
                room_presence_sensor_entity_id(room_name),
                room_presence_entity_id(room_name),
                room_audio_target_entity_id(room_name),
            )
            for room_name in sorted(self.presence.room_sensors())
        ]
        room_control_entities = set(control_summary.get("rooms", []))
        room_cards = [
            {
                "type": "entities",
                "title": HeraldCoordinator._room_label(room_name),
                "show_header_toggle": False,
                "state_color": True,
                "entities": [
                    {"entity": sensor_entity, "name": "Присутствие"},
                    {"entity": switch_entity, "name": "Fallback override"},
                    *(
                        [{"entity": target_entity, "name": "Устройство уведомлений"}]
                        if target_entity in room_control_entities
                        else []
                    ),
                ],
            }
            for room_name, sensor_entity, switch_entity, target_entity in room_definitions
        ]
        user_cards = HeraldCoordinator._dashboard_user_cards(control_summary.get("users", []))
        channel_family_entities = [
            "switch.herald_channel_voice",
            "switch.herald_channel_push",
            "switch.herald_channel_tv",
        ]
        channel_cards = HeraldCoordinator._dashboard_channel_cards(control_summary.get("channels", []))
        flow_cards = HeraldCoordinator._dashboard_flow_cards(control_summary.get("flows", []))
        test_entities = sorted(control_summary.get("tests", []))

        overview_cards: list[dict[str, Any]] = [
            {
                "type": "markdown",
                "title": "Сводка",
                "content": HeraldCoordinator._dashboard_summary_markdown(title),
            },
            {
                "type": "grid",
                "columns": 4,
                "square": False,
                "cards": [
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_status",
                        "name": "Статус",
                        "icon": "mdi:shield-home-outline",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_notifications_today",
                        "name": "Сегодня",
                        "icon": "mdi:bell-badge",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_deliveries_today",
                        "name": "Доставлено",
                        "icon": "mdi:send-check-outline",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_queue_size",
                        "name": "Очередь",
                        "icon": "mdi:playlist-clock",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_dropped_today",
                        "name": "Отброшено",
                        "icon": "mdi:bell-remove-outline",
                    },
                ],
            },
            {
                "type": "grid",
                "columns": 4,
                "square": False,
                "cards": [
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_errors_today",
                        "name": "Ошибки",
                        "icon": "mdi:alert-circle-outline",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_ai_requests_today",
                        "name": "AI",
                        "icon": "mdi:brain",
                    },
                    {
                        "type": "tile",
                        "entity": "update.herald_notification_center_update",
                        "name": "Обновления",
                        "icon": "mdi:update",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_last_notification",
                        "name": "Последнее",
                        "icon": "mdi:bell-ring-outline",
                    },
                ],
            },
            {
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": [
                    {
                        "type": "entities",
                        "title": "Операции",
                        "show_header_toggle": False,
                        "state_color": True,
                        "entities": [
                            "sensor.herald_notification_center_status",
                            "sensor.herald_notification_center_last_notification",
                            "sensor.herald_notification_center_queue_size",
                            "update.herald_notification_center_update",
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Быстрые переключатели",
                        "show_header_toggle": False,
                        "state_color": True,
                        "entities": [
                            "switch.herald_ai_enabled",
                            "switch.herald_maintenance_mode",
                            "switch.herald_mute_all",
                            "switch.herald_dashboard_sidebar",
                            "switch.herald_channel_push",
                            "switch.herald_channel_voice",
                            "switch.herald_level_warning",
                            "switch.herald_level_critical",
                            "select.herald_maintenance_min_level",
                        ],
                    },
                ],
            },
            {
                "type": "markdown",
                "title": "Очередь",
                "content": HeraldCoordinator._dashboard_queue_markdown(),
            },
            {
                "type": "markdown",
                "title": "Последние уведомления",
                "content": HeraldCoordinator._dashboard_recent_markdown(),
            },
        ]

        analytics_cards: list[dict[str, Any]] = [
            {
                "type": "markdown",
                "title": "Сводка аналитики",
                "content": HeraldCoordinator._dashboard_analytics_summary_markdown(),
            },
            {
                "type": "grid",
                "columns": 4,
                "square": False,
                "cards": [
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_deliveries_today",
                        "name": "Доставлено",
                        "icon": "mdi:send-check-outline",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_dropped_today",
                        "name": "Отброшено",
                        "icon": "mdi:bell-remove-outline",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_errors_today",
                        "name": "Ошибки",
                        "icon": "mdi:alert-circle-outline",
                    },
                    {
                        "type": "tile",
                        "entity": "sensor.herald_notification_center_ai_requests_today",
                        "name": "AI-запросы",
                        "icon": "mdi:brain",
                    },
                ],
            },
            {
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": [
                    {
                        "type": "markdown",
                        "title": "Доставка по каналам",
                        "content": HeraldCoordinator._dashboard_channel_delivery_markdown(),
                    },
                    {
                        "type": "markdown",
                        "title": "Ошибки по каналам",
                        "content": HeraldCoordinator._dashboard_channel_errors_markdown(),
                    },
                    {
                        "type": "markdown",
                        "title": "Причины отброса",
                        "content": HeraldCoordinator._dashboard_drop_reasons_markdown(),
                    },
                    {
                        "type": "markdown",
                        "title": "AI-персонажи",
                        "content": HeraldCoordinator._dashboard_ai_characters_markdown(),
                    },
                ],
            },
            {
                "type": "markdown",
                "title": "Dashboard Feed",
                "content": HeraldCoordinator._dashboard_feed_markdown(),
            },
        ]

        controls_cards: list[dict[str, Any]] = [
            {
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": [
                    {
                        "type": "entities",
                        "title": "Система",
                        "show_header_toggle": False,
                        "state_color": True,
                        "entities": [
                            "switch.herald_ai_enabled",
                            "switch.herald_maintenance_mode",
                            "switch.herald_mute_all",
                            "switch.herald_dashboard_sidebar",
                            "switch.herald_ai_info",
                            "switch.herald_ai_warning",
                            "switch.herald_ai_critical",
                            "switch.herald_level_info",
                            "switch.herald_level_warning",
                            "switch.herald_level_critical",
                            "select.herald_maintenance_min_level",
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Семейства каналов",
                        "show_header_toggle": False,
                        "state_color": True,
                        "entities": channel_family_entities,
                    },
                ],
            },
        ]
        if user_cards:
            controls_cards.append(
                {
                    "type": "grid",
                    "columns": 2,
                    "square": False,
                    "cards": user_cards,
                }
            )
        if test_entities:
            controls_cards.append(
                {
                    "type": "entities",
                    "title": "Проверка",
                    "show_header_toggle": False,
                    "entities": test_entities,
                }
            )
        if channel_cards:
            controls_cards.append(
                {
                    "type": "grid",
                    "columns": 2,
                    "square": False,
                    "cards": channel_cards,
                }
            )
        if flow_cards:
            controls_cards.append(
                {
                    "type": "grid",
                    "columns": 2,
                    "square": False,
                    "cards": flow_cards,
                }
            )

        diagnostics_cards: list[dict[str, Any]] = [
            {
                "type": "entities",
                "title": "Диагностика",
                "show_header_toggle": False,
                "state_color": True,
                "entities": [
                    "sensor.herald_notification_center_status",
                    "sensor.herald_notification_center_queue_size",
                    "sensor.herald_notification_center_notifications_today",
                    "update.herald_notification_center_update",
                ],
            },
            {
                "type": "markdown",
                "title": "Pipeline Trace",
                "content": HeraldCoordinator._dashboard_trace_markdown(),
            },
            {
                "type": "markdown",
                "title": "Frontend",
                "content": (
                    "Ресурс карточки регистрируется автоматически как "
                    f"`{FRONTEND_MODULE_URL}`. Основной dashboard не зависит от кастомной карты, "
                    "поэтому остаётся рабочим даже если браузер ещё не перечитал frontend bundle."
                ),
            },
        ]
        diagnostics_cards.extend(HeraldCoordinator._render_plugin_dashboard_cards(self))

        views: list[dict[str, Any]] = [
            {
                "title": "Обзор",
                "path": "herald",
                "icon": "mdi:bell-badge",
                "cards": overview_cards,
            },
            {
                "title": "Аналитика",
                "path": "herald-analytics",
                "icon": "mdi:chart-box-outline",
                "cards": analytics_cards,
            },
            {
                "title": "Управление",
                "path": "herald-controls",
                "icon": "mdi:tune-variant",
                "cards": controls_cards,
            },
            {
                "title": "Диагностика",
                "path": "herald-diagnostics",
                "icon": "mdi:stethoscope",
                "cards": diagnostics_cards,
            },
        ]
        if preset in {"overview", "rooms"} and room_definitions:
            views.insert(
                1,
                {
                    "title": "Комнаты",
                    "path": "herald-rooms",
                    "icon": "mdi:floor-plan",
                    "cards": [
                        {
                            "type": "grid",
                            "columns": 2,
                            "square": False,
                            "cards": [
                                *room_cards
                            ],
                        }
                    ],
                },
            )

        return {"title": title, "views": views}

    def _build_dashboard_yaml(self, *, title: str, preset: str) -> str:
        """Serialize the Lovelace dashboard payload as YAML."""
        return yaml.safe_dump(
            HeraldCoordinator._build_dashboard_payload(self, title=title, preset=preset),
            allow_unicode=True,
            sort_keys=False,
        )

    def build_dashboard_config(
        self,
        *,
        title: str = FRONTEND_DASHBOARD_TITLE,
        preset: str = DEFAULT_DASHBOARD_PRESET,
    ) -> dict[str, Any]:
        """Return the Herald Control Center as a Lovelace config dict."""
        return dict(HeraldCoordinator._build_dashboard_payload(self, title=title, preset=preset))

    def _render_plugin_dashboard_cards(self) -> list[dict[str, Any]]:
        """Return plugin-provided Lovelace cards without further transformation."""
        return [dict(card) for card in self.plugins.dashboard_cards()]

    @staticmethod
    def _humanize_slug(value: str) -> str:
        """Turn internal slugs into user-facing titles."""
        return value.replace("_", " ").strip().title()

    @staticmethod
    def _room_label(value: str) -> str:
        """Return a user-facing room label with a few localized defaults."""
        labels = {
            "living_room": "Гостиная",
            "bedroom": "Спальня",
            "kitchen": "Кухня",
            "bathroom": "Ванная",
            "office": "Кабинет",
            "tualet": "Туалет",
            "gostinaia": "Гостиная",
            "spalnia": "Спальня",
            "kukhnia": "Кухня",
            "vannaia": "Ванная",
            "kabinet": "Кабинет",
        }
        return labels.get(value, HeraldCoordinator._humanize_slug(value))

    @staticmethod
    def _dashboard_user_cards(user_entities: list[str]) -> list[dict[str, Any]]:
        """Group dynamic user controls into one card per user."""
        grouped: dict[str, list[str]] = {}
        for entity_id in user_entities:
            object_id = entity_id.split(".", maxsplit=1)[-1]
            if not object_id.startswith("herald_user_"):
                continue
            for suffix in ("_language", "_character", "_silent"):
                if object_id.endswith(suffix):
                    user_slug = object_id[len("herald_user_") : -len(suffix)]
                    grouped.setdefault(user_slug, []).append(entity_id)
                    break

        order = {"_language": 0, "_character": 1, "_silent": 2}
        return [
            {
                "type": "entities",
                "title": HeraldCoordinator._humanize_slug(user_slug),
                "show_header_toggle": False,
                "state_color": True,
                "entities": sorted(
                    entities,
                    key=lambda entity_id: next(
                        (
                            rank
                            for suffix, rank in order.items()
                            if entity_id.endswith(suffix)
                        ),
                        99,
                    ),
                ),
            }
            for user_slug, entities in sorted(grouped.items())
        ]

    @staticmethod
    def _dashboard_channel_cards(channel_entities: list[str]) -> list[dict[str, Any]]:
        """Group per-channel controls into one card per delivery channel."""
        grouped: dict[str, list[str]] = {}
        family_entities = {
            "switch.herald_channel_voice",
            "switch.herald_channel_push",
            "switch.herald_channel_tv",
        }
        for entity_id in channel_entities:
            if entity_id in family_entities:
                continue
            object_id = entity_id.split(".", maxsplit=1)[-1]
            if not object_id.startswith("herald_channel_"):
                continue
            for suffix in ("_enabled", "_min_level"):
                if object_id.endswith(suffix):
                    channel_name = object_id[len("herald_channel_") : -len(suffix)]
                    grouped.setdefault(channel_name, []).append(entity_id)
                    break

        order = {"_enabled": 0, "_min_level": 1}
        return [
            {
                "type": "entities",
                "title": HeraldCoordinator._humanize_slug(channel_name),
                "show_header_toggle": False,
                "state_color": True,
                "entities": sorted(
                    entities,
                    key=lambda entity_id: next(
                        (
                            rank
                            for suffix, rank in order.items()
                            if entity_id.endswith(suffix)
                        ),
                        99,
                    ),
                ),
            }
            for channel_name, entities in sorted(grouped.items())
        ]

    @staticmethod
    def _dashboard_flow_cards(flow_entities: list[str]) -> list[dict[str, Any]]:
        """Group flow controls into one card per flow."""
        grouped: dict[str, list[str]] = {}
        for entity_id in flow_entities:
            object_id = entity_id.split(".", maxsplit=1)[-1]
            if not object_id.startswith("herald_flow_"):
                continue
            for suffix in ("_enabled", "_summary_window", "_dedup_window", "_cooldown"):
                if object_id.endswith(suffix):
                    flow_name = object_id[len("herald_flow_") : -len(suffix)]
                    grouped.setdefault(flow_name, []).append(entity_id)
                    break

        order = {
            "_enabled": 0,
            "_summary_window": 1,
            "_dedup_window": 2,
            "_cooldown": 3,
        }
        return [
            {
                "type": "entities",
                "title": HeraldCoordinator._humanize_slug(flow_name),
                "show_header_toggle": False,
                "state_color": True,
                "entities": sorted(
                    entities,
                    key=lambda entity_id: next(
                        (
                            rank
                            for suffix, rank in order.items()
                            if entity_id.endswith(suffix)
                        ),
                        99,
                    ),
                ),
            }
            for flow_name, entities in sorted(grouped.items())
        ]

    @staticmethod
    def _dashboard_summary_markdown(title: str) -> str:
        """Render a compact runtime summary for the overview page."""
        return f"""# {title}
{{% set status_entity = 'sensor.herald_notification_center_status' %}}
{{% set status = states(status_entity) %}}
{{% set home_mode = state_attr(status_entity, 'home_mode') or 'unknown' %}}
{{% set people = state_attr(status_entity, 'people_home') or [] %}}
{{% set quiet_hours = state_attr(status_entity, 'quiet_hours') %}}
{{% set maintenance = state_attr(status_entity, 'maintenance_mode') %}}
{{% set queue_size = states('sensor.herald_notification_center_queue_size') %}}
- **Статус:** `{{{{ status }}}}`
- **Домашний режим:** `{{{{ home_mode }}}}`
- **Люди дома:** `{{{{ people|count }}}}`
- **Quiet hours:** `{{{{ 'on' if quiet_hours else 'off' }}}}`
- **Maintenance mode:** `{{{{ 'on' if maintenance else 'off' }}}}`
- **Очередь:** `{{{{ queue_size }}}}`"""

    @staticmethod
    def _dashboard_analytics_summary_markdown() -> str:
        """Render a compact analytics summary."""
        return """{% set delivered = states('sensor.herald_notification_center_deliveries_today') %}
{% set dropped = states('sensor.herald_notification_center_dropped_today') %}
{% set errors = states('sensor.herald_notification_center_errors_today') %}
{% set ai = states('sensor.herald_notification_center_ai_requests_today') %}
Herald считает доставку и потери в runtime. Этот экран нужен, чтобы быстро понять, что происходит с потоком уведомлений без похода в trace.

- **Доставлено:** `{{ delivered }}`
- **Отброшено:** `{{ dropped }}`
- **Ошибки:** `{{ errors }}`
- **AI-запросы:** `{{ ai }}`"""

    @staticmethod
    def _dashboard_recent_markdown() -> str:
        """Render recent notifications with standard markdown."""
        return """{% set items = state_attr('sensor.herald_notification_center_notifications_today', 'recent_notifications') or [] %}
{% if items %}
{% for item in items[:6] %}
- **{{ item.title or item.event or 'Herald' }}**: {{ item.message or '' }}
  `{{ item.level or 'info' }}` · {{ item.timestamp or '' }}
{% endfor %}
{% else %}
_За сегодня ещё нет доставленных уведомлений._
{% endif %}"""

    @staticmethod
    def _dashboard_feed_markdown() -> str:
        """Render dashboard feed entries with standard markdown."""
        return """{% set items = state_attr('sensor.herald_notification_center_notifications_today', 'dashboard_feed') or [] %}
{% if items %}
{% for item in items[:6] %}
- **{{ item.title or item.event or 'Dashboard feed' }}**: {{ item.message or '' }}
  `{{ item.level or 'info' }}` · `{{ item.channel or 'dashboard' }}` · {{ item.timestamp or '' }}
{% endfor %}
{% else %}
_Dashboard feed пока пуст._
{% endif %}"""

    @staticmethod
    def _dashboard_queue_markdown() -> str:
        """Render queued notifications with standard markdown."""
        return """{% set items = state_attr('sensor.herald_notification_center_queue_size', 'queued_notifications') or [] %}
{% if items %}
{% for item in items[:8] %}
- **{{ item.title or item.event or 'Queued notification' }}**: {{ item.message or '' }}
  `{{ item.level or 'info' }}` · окно `{{ item.summary_window_seconds or 0 }}s` · {{ item.enqueued_at or item.timestamp or '' }}
{% endfor %}
{% else %}
_Очередь сейчас пуста._
{% endif %}"""

    @staticmethod
    def _dashboard_channel_delivery_markdown() -> str:
        """Render delivery counters grouped by channel."""
        return """{% set data = state_attr('sensor.herald_notification_center_status', 'analytics') or {} %}
{% set items = data.channel_delivery_counts or {} %}
{% if items %}
{% for key, value in items|dictsort(by='value', reverse=True) %}
- **{{ key }}**: {{ value }}
{% endfor %}
{% else %}
_Пока нет данных по доставке._
{% endif %}"""

    @staticmethod
    def _dashboard_channel_errors_markdown() -> str:
        """Render channel error counters."""
        return """{% set data = state_attr('sensor.herald_notification_center_status', 'analytics') or {} %}
{% set items = data.channel_error_counts or {} %}
{% if items %}
{% for key, value in items|dictsort(by='value', reverse=True) %}
- **{{ key }}**: {{ value }}
{% endfor %}
{% else %}
_Ошибок по каналам пока нет._
{% endif %}"""

    @staticmethod
    def _dashboard_drop_reasons_markdown() -> str:
        """Render drop reasons counters."""
        return """{% set data = state_attr('sensor.herald_notification_center_status', 'analytics') or {} %}
{% set items = data.drop_reasons or {} %}
{% if items %}
{% for key, value in items|dictsort(by='value', reverse=True) %}
- **{{ key }}**: {{ value }}
{% endfor %}
{% else %}
_Отброшенных уведомлений по причинам пока нет._
{% endif %}"""

    @staticmethod
    def _dashboard_ai_characters_markdown() -> str:
        """Render AI character usage counters."""
        return """{% set data = state_attr('sensor.herald_notification_center_status', 'analytics') or {} %}
{% set items = data.ai_character_counts or {} %}
{% if items %}
{% for key, value in items|dictsort(by='value', reverse=True) %}
- **{{ key }}**: {{ value }}
{% endfor %}
{% else %}
_AI-персонажи сегодня ещё не использовались._
{% endif %}"""

    @staticmethod
    def _dashboard_trace_markdown() -> str:
        """Render a compact pipeline trace timeline."""
        return """{% set items = state_attr('sensor.herald_notification_center_status', 'pipeline_trace') or [] %}
{% if items %}
{% for item in items[:8] %}
- **{{ item.stage or 'stage' }}**{% if item.flow %} · `{{ item.flow }}`{% endif %}{% if item.event %}: {{ item.event }}{% endif %}
  {{ item.timestamp or '' }}
{% endfor %}
{% else %}
_Pipeline trace пока пуст._
{% endif %}"""

    @staticmethod
    def _write_text_file(path: str, content: str) -> None:
        """Write a UTF-8 text file, creating missing parent directories."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
