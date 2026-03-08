"""Dataclasses used by the Herald integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .const import (
    CONF_ALLOW_SUMMARY,
    CONF_AWAY_CHANNELS,
    CONF_CHANNEL_TYPE,
    CONF_CHANNELS,
    CONF_CHAT_ID,
    CONF_CONDITIONS,
    CONF_COOLDOWN,
    CONF_DATA,
    CONF_DEDUP_WINDOW,
    CONF_ENABLED,
    CONF_END,
    CONF_ENTITY_ID,
    CONF_FAMILY_GROUP,
    CONF_FLOWS,
    CONF_HOME_MODE_ENTITY,
    CONF_HOST,
    CONF_INCLUDE_ACTIONS,
    CONF_LANGUAGE_HELPER,
    CONF_MAINTENANCE_MIN_LEVEL,
    CONF_MAINTENANCE_MODE_ENTITY,
    CONF_MIN_LEVEL,
    CONF_MINUTES,
    CONF_MODEL,
    CONF_NAME,
    CONF_NOBODY_HOME_ENTITY,
    CONF_NOTIFICATION_ID,
    CONF_OLLAMA,
    CONF_PERSONALITIES,
    CONF_PERSONALITY,
    CONF_PREFERRED_CHANNELS,
    CONF_PREFERRED_TTS_CHANNEL,
    CONF_PRESENCE,
    CONF_QUIET_HOURS,
    CONF_QUIET_HOURS_POLICY,
    CONF_ROOM,
    CONF_ROOM_ENTITY,
    CONF_ROOM_SENSORS,
    CONF_ROUTER,
    CONF_SERVICE,
    CONF_SEVERITY,
    CONF_START,
    CONF_SUMMARY_PERSONALITY,
    CONF_SUMMARY_WINDOW,
    CONF_THREAD_ID,
    CONF_TITLE_PREFIX,
    CONF_USER,
    CONF_USERS,
    DEFAULT_CHANNEL_MIN_LEVEL,
    DEFAULT_FLOW_COOLDOWN_SECONDS,
    DEFAULT_FLOW_DEDUP_WINDOW_SECONDS,
    DEFAULT_FLOWS,
    DEFAULT_MAINTENANCE_MIN_LEVEL,
    DEFAULT_MAINTENANCE_MODE_ENTITY,
    DEFAULT_NAME,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_PERSONALITIES,
    DEFAULT_QUIET_HOURS_END,
    DEFAULT_QUIET_HOURS_START,
    DEFAULT_RECENT_LIMIT,
    DEFAULT_ROOM_SENSORS,
    DEFAULT_SNOOZE_MINUTES,
    DEFAULT_SUMMARY_WINDOW_SECONDS,
    DEFAULT_TRACE_LIMIT,
    QUIET_HOURS_POLICY_DEFAULT,
)


@dataclass(slots=True)
class QuietHoursConfig:
    """Quiet hours configuration."""

    start: str = DEFAULT_QUIET_HOURS_START
    end: str = DEFAULT_QUIET_HOURS_END


@dataclass(slots=True)
class ChannelConfig:
    """Configured notification channel."""

    name: str
    channel_type: str
    enabled: bool = True
    entity_id: str | list[str] | None = None
    service: str | None = None
    chat_id: int | str | None = None
    thread_id: int | str | None = None
    room: str | None = None
    user: str | None = None
    title_prefix: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    min_level: str = DEFAULT_CHANNEL_MIN_LEVEL
    quiet_hours_policy: str = QUIET_HOURS_POLICY_DEFAULT

    @classmethod
    def from_dict(cls, name: str, raw: dict[str, Any]) -> "ChannelConfig":
        """Build a typed channel configuration from raw YAML/UI data."""
        payload = dict(raw)
        return cls(
            name=name,
            channel_type=str(payload.get(CONF_CHANNEL_TYPE, "persistent_notification")),
            enabled=bool(payload.get(CONF_ENABLED, True)),
            entity_id=payload.get(CONF_ENTITY_ID),
            service=payload.get(CONF_SERVICE),
            chat_id=payload.get(CONF_CHAT_ID),
            thread_id=payload.get(CONF_THREAD_ID),
            room=payload.get(CONF_ROOM),
            user=payload.get(CONF_USER),
            title_prefix=payload.get(CONF_TITLE_PREFIX),
            data=dict(payload.get(CONF_DATA, {})),
            min_level=str(payload.get(CONF_MIN_LEVEL, DEFAULT_CHANNEL_MIN_LEVEL)),
            quiet_hours_policy=str(
                payload.get(CONF_QUIET_HOURS_POLICY, QUIET_HOURS_POLICY_DEFAULT)
            ),
        )


@dataclass(slots=True)
class FlowConfig:
    """Notification flow configuration."""

    name: str
    enabled: bool = True
    severity: str = "info"
    channels: list[str] = field(default_factory=list)
    conditions: dict[str, Any] = field(default_factory=dict)
    personality: str | None = None
    summary_personality: str | None = None
    allow_summary: bool = True
    summary_window_seconds: int = DEFAULT_SUMMARY_WINDOW_SECONDS
    dedup_window_seconds: int = DEFAULT_FLOW_DEDUP_WINDOW_SECONDS
    cooldown_seconds: int = DEFAULT_FLOW_COOLDOWN_SECONDS

    @classmethod
    def from_dict(cls, name: str, raw: dict[str, Any]) -> "FlowConfig":
        """Build a flow config from raw YAML/UI data."""
        payload = dict(raw)
        return cls(
            name=name,
            enabled=bool(payload.get(CONF_ENABLED, True)),
            severity=str(payload.get(CONF_SEVERITY, "info")),
            channels=list(payload.get(CONF_CHANNELS, [])),
            conditions=dict(payload.get(CONF_CONDITIONS, {})),
            personality=payload.get(CONF_PERSONALITY),
            summary_personality=payload.get(CONF_SUMMARY_PERSONALITY),
            allow_summary=bool(payload.get(CONF_ALLOW_SUMMARY, True)),
            summary_window_seconds=int(
                payload.get(CONF_SUMMARY_WINDOW, DEFAULT_SUMMARY_WINDOW_SECONDS)
            ),
            dedup_window_seconds=int(
                payload.get(CONF_DEDUP_WINDOW, DEFAULT_FLOW_DEDUP_WINDOW_SECONDS)
            ),
            cooldown_seconds=int(
                payload.get(CONF_COOLDOWN, DEFAULT_FLOW_COOLDOWN_SECONDS)
            ),
        )


@dataclass(slots=True)
class UserConfig:
    """Per-user language and routing preferences."""

    key: str
    name: str
    language_helper: str | None = None
    presence_entity: str | None = None
    room_entity: str | None = None
    preferred_channels: list[str] = field(default_factory=list)
    preferred_tts_channel: str | None = None

    @classmethod
    def from_dict(cls, key: str, raw: dict[str, Any]) -> "UserConfig":
        """Build a user config from raw YAML/UI data."""
        payload = dict(raw)
        return cls(
            key=key,
            name=str(payload.get(CONF_NAME, key)),
            language_helper=payload.get(CONF_LANGUAGE_HELPER),
            presence_entity=payload.get("presence_entity"),
            room_entity=payload.get(CONF_ROOM_ENTITY),
            preferred_channels=list(payload.get(CONF_PREFERRED_CHANNELS, [])),
            preferred_tts_channel=payload.get(CONF_PREFERRED_TTS_CHANNEL),
        )


@dataclass(slots=True)
class HeraldConfig:
    """Complete runtime configuration for Herald."""

    name: str = DEFAULT_NAME
    ollama: dict[str, Any] = field(
        default_factory=lambda: {
            CONF_ENABLED: True,
            CONF_HOST: DEFAULT_OLLAMA_HOST,
            CONF_MODEL: DEFAULT_OLLAMA_MODEL,
        }
    )
    channels: dict[str, ChannelConfig] = field(default_factory=dict)
    flows: dict[str, FlowConfig] = field(default_factory=dict)
    users: dict[str, UserConfig] = field(default_factory=dict)
    personalities: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_PERSONALITIES))
    quiet_hours: QuietHoursConfig = field(default_factory=QuietHoursConfig)
    presence: dict[str, Any] = field(
        default_factory=lambda: {
            CONF_FAMILY_GROUP: "group.family",
            CONF_NOBODY_HOME_ENTITY: "binary_sensor.nobody_home",
            CONF_HOME_MODE_ENTITY: "sensor.home_mode",
            CONF_ROOM_SENSORS: dict(DEFAULT_ROOM_SENSORS),
            CONF_AWAY_CHANNELS: [],
        }
    )
    router: dict[str, Any] = field(
        default_factory=lambda: {
            CONF_SUMMARY_WINDOW: DEFAULT_SUMMARY_WINDOW_SECONDS,
            "trace_limit": DEFAULT_TRACE_LIMIT,
            "recent_limit": DEFAULT_RECENT_LIMIT,
            CONF_MAINTENANCE_MODE_ENTITY: DEFAULT_MAINTENANCE_MODE_ENTITY,
            CONF_MAINTENANCE_MIN_LEVEL: DEFAULT_MAINTENANCE_MIN_LEVEL,
        }
    )

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | None) -> "HeraldConfig":
        """Build the runtime configuration from YAML or config-entry data."""
        payload = dict(raw or {})
        quiet_raw = dict(payload.get(CONF_QUIET_HOURS, {}))
        quiet_hours = QuietHoursConfig(
            start=str(quiet_raw.get(CONF_START, DEFAULT_QUIET_HOURS_START)),
            end=str(quiet_raw.get(CONF_END, DEFAULT_QUIET_HOURS_END)),
        )

        ollama = {
            CONF_ENABLED: bool(payload.get(CONF_OLLAMA, {}).get(CONF_ENABLED, True)),
            CONF_HOST: str(payload.get(CONF_OLLAMA, {}).get(CONF_HOST, DEFAULT_OLLAMA_HOST)),
            CONF_MODEL: str(payload.get(CONF_OLLAMA, {}).get(CONF_MODEL, DEFAULT_OLLAMA_MODEL)),
        }

        channels = {
            name: ChannelConfig.from_dict(name, channel)
            for name, channel in dict(payload.get(CONF_CHANNELS, {})).items()
        }
        if not channels:
            channels = {
                "persistent_default": ChannelConfig(
                    name="persistent_default",
                    channel_type="persistent_notification",
                ),
                "system_log_default": ChannelConfig(
                    name="system_log_default",
                    channel_type="system_log",
                ),
            }

        flow_payload = {name: dict(value) for name, value in DEFAULT_FLOWS.items()}
        flow_payload.update(dict(payload.get(CONF_FLOWS, {})))
        flows = {
            name: FlowConfig.from_dict(name, value)
            for name, value in flow_payload.items()
        }
        for flow in flows.values():
            if not flow.channels:
                flow.channels = list(channels.keys())[:2]

        users = {
            name: UserConfig.from_dict(name, user)
            for name, user in dict(payload.get(CONF_USERS, {})).items()
        }

        personalities = dict(DEFAULT_PERSONALITIES)
        personalities.update(dict(payload.get(CONF_PERSONALITIES, {})))

        presence = {
            CONF_FAMILY_GROUP: "group.family",
            CONF_NOBODY_HOME_ENTITY: "binary_sensor.nobody_home",
            CONF_HOME_MODE_ENTITY: "sensor.home_mode",
            CONF_ROOM_SENSORS: dict(DEFAULT_ROOM_SENSORS),
            CONF_AWAY_CHANNELS: [],
        }
        presence.update(dict(payload.get(CONF_PRESENCE, {})))
        presence[CONF_ROOM_SENSORS] = {
            **dict(DEFAULT_ROOM_SENSORS),
            **dict(presence.get(CONF_ROOM_SENSORS, {})),
        }

        router = {
            CONF_SUMMARY_WINDOW: DEFAULT_SUMMARY_WINDOW_SECONDS,
            "trace_limit": DEFAULT_TRACE_LIMIT,
            "recent_limit": DEFAULT_RECENT_LIMIT,
            CONF_MAINTENANCE_MODE_ENTITY: DEFAULT_MAINTENANCE_MODE_ENTITY,
            CONF_MAINTENANCE_MIN_LEVEL: DEFAULT_MAINTENANCE_MIN_LEVEL,
        }
        router.update(dict(payload.get(CONF_ROUTER, {})))

        return cls(
            name=str(payload.get(CONF_NAME, DEFAULT_NAME)),
            ollama=ollama,
            channels=channels,
            flows=flows,
            users=users,
            personalities=personalities,
            quiet_hours=quiet_hours,
            presence=presence,
            router=router,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the typed configuration to a plain dictionary."""
        return {
            CONF_NAME: self.name,
            CONF_OLLAMA: dict(self.ollama),
            CONF_CHANNELS: {key: asdict(channel) for key, channel in self.channels.items()},
            CONF_FLOWS: {key: asdict(flow) for key, flow in self.flows.items()},
            CONF_USERS: {key: asdict(user) for key, user in self.users.items()},
            CONF_PERSONALITIES: dict(self.personalities),
            CONF_QUIET_HOURS: asdict(self.quiet_hours),
            CONF_PRESENCE: dict(self.presence),
            CONF_ROUTER: dict(self.router),
        }


@dataclass(slots=True)
class NotificationContext:
    """A single notification request that will move through the pipeline."""

    flow: str
    title: str
    message: str
    level: str
    source: str
    timestamp: str
    event: str = ""
    notification_id: str = ""
    automation_id: str | None = None
    device: str | None = None
    room: str | None = None
    user: str | None = None
    users: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    context_data: dict[str, Any] = field(default_factory=dict)
    ai_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    character: str | None = None
    personality: str | None = None
    group: str | None = None
    suppress_seconds: int | None = None
    immediately: bool = True
    rewrite: bool = True
    summarize: bool = True
    force: bool = False
    include_actions: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the context for traces and diagnostics."""
        return asdict(self)


@dataclass(slots=True)
class PresenceSnapshot:
    """Resolved presence and quiet-hours state."""

    people_home: list[str] = field(default_factory=list)
    nobody_home: bool = False
    home_mode: str = "home"
    occupied_rooms: list[str] = field(default_factory=list)
    primary_room: str | None = None
    quiet_hours: bool = False


@dataclass(slots=True)
class RuntimeState:
    """Persistent runtime state used by sensors and diagnostics."""

    current_day: str
    notifications_today: int = 0
    deliveries_today: int = 0
    dropped_today: int = 0
    errors_today: int = 0
    ai_requests_today: int = 0
    queue_size: int = 0
    queued_notifications: list[dict[str, Any]] = field(default_factory=list)
    last_notification: dict[str, Any] = field(default_factory=dict)
    recent_notifications: list[dict[str, Any]] = field(default_factory=list)
    dashboard_feed: list[dict[str, Any]] = field(default_factory=list)
    flow_overrides: dict[str, bool] = field(default_factory=dict)
    snoozed_flows: dict[str, str] = field(default_factory=dict)
    acknowledged_notifications: dict[str, dict[str, Any]] = field(default_factory=dict)
    dedup_cache: dict[str, str] = field(default_factory=dict)
    last_flow_delivery: dict[str, str] = field(default_factory=dict)
    channel_delivery_counts: dict[str, int] = field(default_factory=dict)
    channel_error_counts: dict[str, int] = field(default_factory=dict)
    drop_reasons: dict[str, int] = field(default_factory=dict)
    ai_character_counts: dict[str, int] = field(default_factory=dict)
    traces: list[dict[str, Any]] = field(default_factory=list)
    control_values: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RuntimeState":
        """Restore persisted runtime state."""
        payload = dict(raw)
        return cls(
            current_day=str(payload.get("current_day", "1970-01-01")),
            notifications_today=int(payload.get("notifications_today", 0)),
            deliveries_today=int(payload.get("deliveries_today", 0)),
            dropped_today=int(payload.get("dropped_today", 0)),
            errors_today=int(payload.get("errors_today", 0)),
            ai_requests_today=int(payload.get("ai_requests_today", 0)),
            queue_size=int(payload.get("queue_size", 0)),
            queued_notifications=list(payload.get("queued_notifications", [])),
            last_notification=dict(payload.get("last_notification", {})),
            recent_notifications=list(payload.get("recent_notifications", [])),
            dashboard_feed=list(payload.get("dashboard_feed", [])),
            flow_overrides=dict(payload.get("flow_overrides", {})),
            snoozed_flows=dict(payload.get("snoozed_flows", {})),
            acknowledged_notifications=dict(payload.get("acknowledged_notifications", {})),
            dedup_cache=dict(payload.get("dedup_cache", {})),
            last_flow_delivery=dict(payload.get("last_flow_delivery", {})),
            channel_delivery_counts=dict(payload.get("channel_delivery_counts", {})),
            channel_error_counts=dict(payload.get("channel_error_counts", {})),
            drop_reasons=dict(payload.get("drop_reasons", {})),
            ai_character_counts=dict(payload.get("ai_character_counts", {})),
            traces=list(payload.get("traces", [])),
            control_values=dict(payload.get("control_values", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime state for storage."""
        return asdict(self)


DEFAULT_ACTION_FIELDS: dict[str, Any] = {
    CONF_MINUTES: DEFAULT_SNOOZE_MINUTES,
    CONF_NOTIFICATION_ID: "",
    CONF_INCLUDE_ACTIONS: True,
}
