"""Constants for the Herald notification center integration."""

from __future__ import annotations

import enum

try:
    StrEnum = enum.StrEnum
except AttributeError:
    class StrEnum(str, enum.Enum):
        pass

DOMAIN = "herald"
NAME = "Herald Notification Center"
VERSION = "0.4.0"  # x-release-please-version
PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch", "select", "number", "button"]

DATA_YAML_CONFIG = "yaml_config"
DATA_SERVICE_REGISTERED = "service_registered"
DATA_COORDINATORS = "coordinators"
DATA_FRONTEND_REGISTERED = "frontend_registered"
DATA_FRONTEND_REGISTRATION = "frontend_registration"

STORAGE_VERSION = 2
STORAGE_KEY = f"{DOMAIN}.runtime"

SERVICE_NOTIFY = "notify"
SERVICE_GENERATE_DASHBOARD = "generate_dashboard"
SERVICE_SET_FLOW_STATE = "set_flow_state"
SERVICE_TRACE_SNAPSHOT = "trace_snapshot"
SERVICE_ACKNOWLEDGE = "acknowledge"
SERVICE_SNOOZE_FLOW = "snooze_flow"

EVENT_MOBILE_ACTION = "mobile_app_notification_action"
EVENT_MOBILE_CLEARED = "mobile_app_notification_cleared"
EVENT_TELEGRAM_CALLBACK = "telegram_callback"
ACTION_ACK = "HERALD_ACK"
ACTION_SNOOZE = "HERALD_SNOOZE"

CONF_OLLAMA = "ollama"
CONF_HOST = "host"
CONF_MODEL = "model"
CONF_ENABLED = "enabled"
CONF_CHANNELS = "channels"
CONF_FLOWS = "flows"
CONF_CONDITIONS = "conditions"
CONF_USERS = "users"
CONF_PERSONALITIES = "personalities"
CONF_PERSONALITY = "personality"
CONF_SUMMARY_PERSONALITY = "summary_personality"
CONF_MIN_LEVEL = "min_level"
CONF_DEDUP_WINDOW = "dedup_window_seconds"
CONF_COOLDOWN = "cooldown_seconds"
CONF_QUIET_HOURS = "quiet_hours"
CONF_QUIET_HOURS_POLICY = "quiet_hours_policy"
CONF_PRESENCE = "presence"
CONF_ROUTER = "router"
CONF_MAINTENANCE_MODE_ENTITY = "maintenance_mode_entity"
CONF_MAINTENANCE_MIN_LEVEL = "maintenance_min_level"
CONF_LANGUAGE_HELPER = "language_helper"
CONF_ROOM = "room"
CONF_ROOM_ENTITY = "room_entity"
CONF_ROOM_SENSORS = "room_sensors"
CONF_PREFERRED_CHANNELS = "preferred_channels"
CONF_PREFERRED_TTS_CHANNEL = "preferred_tts_channel"
CONF_AWAY_CHANNELS = "away_channels"
CONF_FAMILY_GROUP = "family_group"
CONF_NOBODY_HOME_ENTITY = "nobody_home_entity"
CONF_HOME_MODE_ENTITY = "home_mode_entity"
CONF_CHANNEL_TYPE = "type"
CONF_ENTITY_ID = "entity_id"
CONF_SERVICE = "service"
CONF_CHAT_ID = "chat_id"
CONF_THREAD_ID = "thread_id"
CONF_TITLE_PREFIX = "title_prefix"
CONF_DATA = "data"
CONF_USER = "user"
CONF_SEVERITY = "severity"
CONF_SUMMARY_WINDOW = "summary_window_seconds"
CONF_ALLOW_SUMMARY = "allow_summary"
CONF_START = "start"
CONF_END = "end"
CONF_NAME = "name"
CONF_NOTIFICATION_ID = "notification_id"
CONF_INCLUDE_ACTIONS = "include_actions"
CONF_MINUTES = "minutes"
CONF_PRESET = "preset"

DEFAULT_NAME = NAME
DEFAULT_OLLAMA_HOST = "http://ollama.local:11434"
DEFAULT_OLLAMA_MODEL = "llama3"
DEFAULT_QUIET_HOURS_START = "23:00"
DEFAULT_QUIET_HOURS_END = "08:00"
DEFAULT_DASHBOARD_PRESET = "overview"
DEFAULT_SUMMARY_WINDOW_SECONDS = 75
DEFAULT_TRACE_LIMIT = 100
DEFAULT_RECENT_LIMIT = 20
DEFAULT_PERSONALITY = "HESTIA"
DEFAULT_SNOOZE_MINUTES = 30
DEFAULT_CHANNEL_MIN_LEVEL = "info"
DEFAULT_FLOW_COOLDOWN_SECONDS = 0
DEFAULT_FLOW_DEDUP_WINDOW_SECONDS = 0
DEFAULT_MAINTENANCE_MODE_ENTITY = "input_boolean.maintenance_mode"
DEFAULT_MAINTENANCE_MIN_LEVEL = "critical"
FRONTEND_DIR = "frontend"
FRONTEND_BASE_URL = "/herald"
FRONTEND_MODULE_URL = "/herald/herald-card.js"
FRONTEND_DASHBOARD_TITLE = "Herald Control Center"
FRONTEND_DASHBOARD_URL_PATH = "herald-control-center"
FRONTEND_DASHBOARD_ICON = "mdi:bell-badge"

DEFAULT_ROOM_SENSORS: dict[str, str] = {
    "living_room": "binary_sensor.room_gostinaia_occupied",
    "bedroom": "binary_sensor.room_spalnia_occupied",
    "kitchen": "binary_sensor.room_kukhnia_occupied",
    "bathroom": "binary_sensor.room_vannaia_occupied",
    "office": "binary_sensor.room_kabinet_occupied",
}

DEFAULT_PERSONALITIES: dict[str, str] = {
    "Jarvis": (
        "You are Jarvis. Rewrite notifications with concise precision, calm confidence, "
        "and zero fluff. Preserve every factual detail."
    ),
    "Domovoy": (
        "You are Domovoy. Rewrite notifications with a warm, house-guardian tone, "
        "clear facts, and gentle confidence. Avoid theatrics."
    ),
    "HESTIA": (
        "You are HESTIA, the notification voice of a smart home. Be clear, warm, and direct. "
        "Keep important facts explicit and avoid unnecessary drama."
    ),
}

DEFAULT_SUMMARY_TITLES: dict[str, str] = {
    "ru": "Пока вас не было произошло несколько событий",
    "en": "Several events happened while you were away",
    "es": "Han ocurrido varios eventos mientras no estabas en casa",
    "fr": "Plusieurs événements se sont produits pendant votre absence",
}

DEFAULT_FLOW_CHANNELS: tuple[str, ...] = ("persistent_default", "system_log_default")
QUIET_HOURS_POLICY_DEFAULT = "default"
QUIET_HOURS_POLICY_ALLOW = "allow"
QUIET_HOURS_POLICY_BLOCK = "block"
SUPPORTED_DASHBOARD_PRESETS: tuple[str, ...] = ("overview", "rooms", "roles")

REDACT_CONFIG = {
    CONF_HOST,
    CONF_CHAT_ID,
    CONF_THREAD_ID,
}


def topology_signal(entry_id: str) -> str:
    """Return the dispatcher signal used for dynamic Herald topology updates."""
    return f"{DOMAIN}_topology_{entry_id}"


class Severity(StrEnum):
    """Supported notification severities."""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    CRITICAL = "critical"
    SECURITY = "security"
    AI = "ai"
    SYSTEM = "system"


SEVERITY_RANK: dict[str, int] = {
    Severity.DEBUG: 5,
    Severity.INFO: 10,
    Severity.NOTICE: 15,
    Severity.AI: 18,
    Severity.WARNING: 20,
    Severity.SYSTEM: 25,
    Severity.CRITICAL: 30,
    Severity.SECURITY: 40,
}


DEFAULT_FLOWS: dict[str, dict[str, object]] = {
    "security_alerts": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.SECURITY,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: False,
        CONF_SUMMARY_WINDOW: 15,
    },
    "system_events": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.SYSTEM,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: True,
        CONF_SUMMARY_WINDOW: 90,
    },
    "device_alerts": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.WARNING,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: True,
        CONF_SUMMARY_WINDOW: DEFAULT_SUMMARY_WINDOW_SECONDS,
    },
    "ai_events": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.AI,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: True,
        CONF_SUMMARY_WINDOW: DEFAULT_SUMMARY_WINDOW_SECONDS,
    },
    "energy_events": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.WARNING,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: True,
        CONF_SUMMARY_WINDOW: DEFAULT_SUMMARY_WINDOW_SECONDS,
    },
    "camera_alerts": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.WARNING,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: False,
        CONF_SUMMARY_WINDOW: 20,
    },
    "timer_notifications": {
        CONF_ENABLED: True,
        CONF_SEVERITY: Severity.INFO,
        CONF_CHANNELS: list(DEFAULT_FLOW_CHANNELS),
        CONF_ALLOW_SUMMARY: True,
        CONF_SUMMARY_WINDOW: 45,
    },
}
