"""Dynamic Herald-owned control entities and runtime state helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

try:
    from homeassistant.helpers.entity import EntityCategory
except Exception:  # pragma: no cover - lightweight test stubs may not expose helpers.entity
    class EntityCategory:
        CONFIG = "config"

from .const import (
    CONF_MAINTENANCE_MIN_LEVEL,
    DEFAULT_MAINTENANCE_MIN_LEVEL,
    DEFAULT_PERSONALITY,
)
from .translations import normalize_language

if TYPE_CHECKING:
    from .characters import CharacterManager
    from .models import HeraldConfig
    from .presence import PresenceResolver

DEFAULT_LANGUAGE_OPTIONS: tuple[str, ...] = ("ru", "en", "es", "fr")
SEVERITY_OPTIONS: tuple[str, ...] = ("info", "warning", "critical")
CONTROL_PLATFORM = Literal["switch", "select", "number", "button"]
CHANNEL_FAMILY_TYPES: dict[str, set[str]] = {
    "voice": {"tts", "tts_hume"},
    "push": {"mobile_app", "telegram"},
    "tv": {"tv"},
}


@dataclass(slots=True)
class HeraldControlSpec:
    """One Herald-owned runtime control entity."""

    key: str
    platform: CONTROL_PLATFORM
    object_id: str
    name: str
    group: str
    default: bool | str | float | int
    icon: str | None = None
    entity_category: EntityCategory | None = EntityCategory.CONFIG
    translation_key: str | None = None
    translation_placeholders: dict[str, str] = field(default_factory=dict)
    options: tuple[str, ...] = field(default_factory=tuple)
    min_value: float = 0.0
    max_value: float = 3600.0
    step: float = 1.0
    mode: str = "box"

    @property
    def entity_id(self) -> str:
        """Return the full entity id for the control."""
        return f"{self.platform}.{self.object_id}"


def room_presence_control_key(room_name: str) -> str:
    return f"room_presence:{room_name}"


def room_presence_entity_id(room_name: str) -> str:
    return f"switch.herald_room_{room_name}_presence"


def room_presence_sensor_entity_id(room_name: str) -> str:
    return f"binary_sensor.herald_room_{room_name}_presence"


def room_audio_target_control_key(room_name: str) -> str:
    return f"room_audio_target:{room_name}"


def room_audio_target_entity_id(room_name: str) -> str:
    return f"select.herald_room_{room_name}_audio_target"


def user_language_control_key(user_slug: str) -> str:
    return f"user_language:{user_slug}"


def user_character_control_key(user_slug: str) -> str:
    return f"user_character:{user_slug}"


def user_silent_control_key(user_slug: str) -> str:
    return f"user_silent:{user_slug}"


def channel_family_control_key(family: str) -> str:
    return f"channel_family:{family}"


def channel_enabled_control_key(channel_name: str) -> str:
    return f"channel_enabled:{channel_name}"


def channel_min_level_control_key(channel_name: str) -> str:
    return f"channel_min_level:{channel_name}"


def flow_enabled_control_key(flow_name: str) -> str:
    return f"flow_enabled:{flow_name}"


def flow_summary_window_control_key(flow_name: str) -> str:
    return f"flow_summary_window:{flow_name}"


def flow_dedup_window_control_key(flow_name: str) -> str:
    return f"flow_dedup_window:{flow_name}"


def flow_cooldown_control_key(flow_name: str) -> str:
    return f"flow_cooldown:{flow_name}"


def ai_enabled_control_key() -> str:
    return "ai_enabled"


def ai_level_control_key(level: str) -> str:
    return f"ai_level:{level}"


def level_enabled_control_key(level: str) -> str:
    return f"level_enabled:{level}"


def maintenance_min_level_control_key() -> str:
    return "maintenance_min_level"


def maintenance_mode_control_key() -> str:
    return "maintenance_mode"


def mute_all_control_key() -> str:
    return "mute_all"


def dashboard_sidebar_control_key() -> str:
    return "dashboard_sidebar"


def level_test_button_key(level: str) -> str:
    return f"test_level:{level}"


def channel_test_button_key(channel_name: str) -> str:
    return f"test_channel:{channel_name}"


class HeraldControlManager:
    """Build, migrate, read, and write Herald-owned runtime controls."""

    def __init__(
        self,
        hass,
        config: HeraldConfig,
        presence: PresenceResolver,
        characters: CharacterManager,
        state_getter,
    ) -> None:
        self._hass = hass
        self._config = config
        self._presence = presence
        self._characters = characters
        self._state_getter = state_getter

    def build_specs(self) -> list[HeraldControlSpec]:
        """Return the complete dynamic control topology."""
        specs: list[HeraldControlSpec] = [
            HeraldControlSpec(
                key=ai_enabled_control_key(),
                platform="switch",
                object_id="herald_ai_enabled",
                name="Herald AI Enabled",
                group="ai",
                default=True,
                icon="mdi:brain",
                translation_key="ai_enabled",
            ),
            HeraldControlSpec(
                key=level_enabled_control_key("info"),
                platform="switch",
                object_id="herald_level_info",
                name="Herald Level Info",
                group="levels",
                default=True,
                icon="mdi:bell-outline",
                translation_key="level_info",
            ),
            HeraldControlSpec(
                key=level_enabled_control_key("warning"),
                platform="switch",
                object_id="herald_level_warning",
                name="Herald Level Warning",
                group="levels",
                default=True,
                icon="mdi:bell-alert-outline",
                translation_key="level_warning",
            ),
            HeraldControlSpec(
                key=level_enabled_control_key("critical"),
                platform="switch",
                object_id="herald_level_critical",
                name="Herald Level Critical",
                group="levels",
                default=True,
                icon="mdi:alarm-light-outline",
                translation_key="level_critical",
            ),
            HeraldControlSpec(
                key=maintenance_mode_control_key(),
                platform="switch",
                object_id="herald_maintenance_mode",
                name="Herald Maintenance Mode",
                group="router",
                default=False,
                icon="mdi:wrench-clock",
                translation_key="maintenance_mode",
            ),
            HeraldControlSpec(
                key=mute_all_control_key(),
                platform="switch",
                object_id="herald_mute_all",
                name="Herald Mute All",
                group="router",
                default=False,
                icon="mdi:bell-cancel-outline",
                translation_key="mute_all",
            ),
            HeraldControlSpec(
                key=dashboard_sidebar_control_key(),
                platform="switch",
                object_id="herald_dashboard_sidebar",
                name="Herald Dashboard Sidebar",
                group="router",
                default=True,
                icon="mdi:view-dashboard-outline",
                translation_key="dashboard_sidebar",
            ),
            HeraldControlSpec(
                key=ai_level_control_key("info"),
                platform="switch",
                object_id="herald_ai_info",
                name="Herald AI Info",
                group="ai",
                default=False,
                icon="mdi:brain",
                translation_key="ai_info",
            ),
            HeraldControlSpec(
                key=ai_level_control_key("warning"),
                platform="switch",
                object_id="herald_ai_warning",
                name="Herald AI Warning",
                group="ai",
                default=True,
                icon="mdi:brain",
                translation_key="ai_warning",
            ),
            HeraldControlSpec(
                key=ai_level_control_key("critical"),
                platform="switch",
                object_id="herald_ai_critical",
                name="Herald AI Critical",
                group="ai",
                default=True,
                icon="mdi:brain",
                translation_key="ai_critical",
            ),
            HeraldControlSpec(
                key=channel_family_control_key("voice"),
                platform="switch",
                object_id="herald_channel_voice",
                name="Herald Channel Voice",
                group="channels",
                default=True,
                icon="mdi:speaker-wireless",
                translation_key="channel_voice",
            ),
            HeraldControlSpec(
                key=channel_family_control_key("push"),
                platform="switch",
                object_id="herald_channel_push",
                name="Herald Channel Push",
                group="channels",
                default=True,
                icon="mdi:cellphone-badge",
                translation_key="channel_push",
            ),
            HeraldControlSpec(
                key=channel_family_control_key("tv"),
                platform="switch",
                object_id="herald_channel_tv",
                name="Herald Channel TV",
                group="channels",
                default=True,
                icon="mdi:television",
                translation_key="channel_tv",
            ),
            HeraldControlSpec(
                key=maintenance_min_level_control_key(),
                platform="select",
                object_id="herald_maintenance_min_level",
                name="Herald Maintenance Min Level",
                group="router",
                default=str(
                    self._config.router.get(
                        CONF_MAINTENANCE_MIN_LEVEL,
                        DEFAULT_MAINTENANCE_MIN_LEVEL,
                    )
                ),
                options=SEVERITY_OPTIONS,
                icon="mdi:shield-wrench-outline",
                translation_key="maintenance_min_level",
            ),
            HeraldControlSpec(
                key=level_test_button_key("info"),
                platform="button",
                object_id="herald_test_level_info",
                name="Herald Test Level Info",
                group="tests",
                default=0,
                icon="mdi:flask-outline",
                translation_key="test_level_info",
            ),
            HeraldControlSpec(
                key=level_test_button_key("warning"),
                platform="button",
                object_id="herald_test_level_warning",
                name="Herald Test Level Warning",
                group="tests",
                default=0,
                icon="mdi:flask-outline",
                translation_key="test_level_warning",
            ),
            HeraldControlSpec(
                key=level_test_button_key("critical"),
                platform="button",
                object_id="herald_test_level_critical",
                name="Herald Test Level Critical",
                group="tests",
                default=0,
                icon="mdi:flask-outline",
                translation_key="test_level_critical",
            ),
        ]

        for room_name in sorted(self._presence.room_sensors()):
            specs.append(
                HeraldControlSpec(
                    key=room_presence_control_key(room_name),
                    platform="switch",
                    object_id=f"herald_room_{room_name}_presence",
                    name=f"Herald Room {_humanize(room_name)} Presence",
                    group="rooms",
                    default=False,
                    icon="mdi:floor-plan",
                    translation_key="room_presence_switch",
                    translation_placeholders={"room_name": _humanize(room_name)},
                )
            )
        for room_name, options in sorted(self._room_audio_target_options().items()):
            specs.append(
                HeraldControlSpec(
                    key=room_audio_target_control_key(room_name),
                    platform="select",
                    object_id=f"herald_room_{room_name}_audio_target",
                    name=f"Herald Room {_humanize(room_name)} Audio Target",
                    group="rooms",
                    default="auto",
                    options=options,
                    icon="mdi:speaker-multiple",
                    translation_key="room_audio_target",
                    translation_placeholders={"room_name": _humanize(room_name)},
                )
            )

        character_options = self._character_options()
        default_character = self._default_character()
        for user_slug, user_name in self._person_specs():
            specs.extend(
                (
                    HeraldControlSpec(
                        key=user_language_control_key(user_slug),
                        platform="select",
                        object_id=f"herald_user_{user_slug}_language",
                        name=f"Herald User {user_name} Language",
                        group="users",
                        default=self._legacy_user_language(user_slug),
                        options=DEFAULT_LANGUAGE_OPTIONS,
                        icon="mdi:translate",
                        translation_key="user_language",
                        translation_placeholders={"user_name": user_name},
                    ),
                    HeraldControlSpec(
                        key=user_character_control_key(user_slug),
                        platform="select",
                        object_id=f"herald_user_{user_slug}_character",
                        name=f"Herald User {user_name} Character",
                        group="users",
                        default=default_character,
                        options=character_options,
                        icon="mdi:account-voice",
                        translation_key="user_character",
                        translation_placeholders={"user_name": user_name},
                    ),
                    HeraldControlSpec(
                        key=user_silent_control_key(user_slug),
                        platform="switch",
                        object_id=f"herald_user_{user_slug}_silent",
                        name=f"Herald User {user_name} Silent",
                        group="users",
                        default=False,
                        icon="mdi:bell-off-outline",
                        translation_key="user_silent",
                        translation_placeholders={"user_name": user_name},
                    ),
                )
            )

        for flow_name, flow in sorted(self._config.flows.items()):
            label = _humanize(flow_name)
            specs.extend(
                (
                    HeraldControlSpec(
                        key=flow_enabled_control_key(flow_name),
                        platform="switch",
                        object_id=f"herald_flow_{flow_name}_enabled",
                        name=f"Herald Flow {label} Enabled",
                        group="flows",
                        default=bool(flow.enabled),
                        icon="mdi:source-branch",
                        translation_key="flow_enabled",
                        translation_placeholders={"flow_name": label},
                    ),
                    HeraldControlSpec(
                        key=flow_summary_window_control_key(flow_name),
                        platform="number",
                        object_id=f"herald_flow_{flow_name}_summary_window",
                        name=f"Herald Flow {label} Summary Window",
                        group="flows",
                        default=int(flow.summary_window_seconds),
                        icon="mdi:timeline-clock-outline",
                        min_value=0,
                        max_value=3600,
                        step=5,
                        translation_key="flow_summary_window",
                        translation_placeholders={"flow_name": label},
                    ),
                    HeraldControlSpec(
                        key=flow_dedup_window_control_key(flow_name),
                        platform="number",
                        object_id=f"herald_flow_{flow_name}_dedup_window",
                        name=f"Herald Flow {label} Dedup Window",
                        group="flows",
                        default=int(flow.dedup_window_seconds),
                        icon="mdi:content-duplicate",
                        min_value=0,
                        max_value=3600,
                        step=5,
                        translation_key="flow_dedup_window",
                        translation_placeholders={"flow_name": label},
                    ),
                    HeraldControlSpec(
                        key=flow_cooldown_control_key(flow_name),
                        platform="number",
                        object_id=f"herald_flow_{flow_name}_cooldown",
                        name=f"Herald Flow {label} Cooldown",
                        group="flows",
                        default=int(flow.cooldown_seconds),
                        icon="mdi:timer-cog-outline",
                        min_value=0,
                        max_value=3600,
                        step=5,
                        translation_key="flow_cooldown",
                        translation_placeholders={"flow_name": label},
                    ),
                )
            )

        for channel_name, channel in sorted(self._config.channels.items()):
            label = _humanize(channel_name)
            specs.extend(
                (
                    HeraldControlSpec(
                        key=channel_enabled_control_key(channel_name),
                        platform="switch",
                        object_id=f"herald_channel_{channel_name}_enabled",
                        name=f"Herald Channel {label} Enabled",
                        group="channels",
                        default=bool(channel.enabled),
                        icon="mdi:transit-connection-variant",
                        translation_key="channel_enabled",
                        translation_placeholders={"channel_name": label},
                    ),
                    HeraldControlSpec(
                        key=channel_min_level_control_key(channel_name),
                        platform="select",
                        object_id=f"herald_channel_{channel_name}_min_level",
                        name=f"Herald Channel {label} Min Level",
                        group="channels",
                        default=str(channel.min_level),
                        options=SEVERITY_OPTIONS,
                        icon="mdi:signal-cellular-outline",
                        translation_key="channel_min_level",
                        translation_placeholders={"channel_name": label},
                    ),
                    HeraldControlSpec(
                        key=channel_test_button_key(channel_name),
                        platform="button",
                        object_id=f"herald_test_channel_{channel_name}",
                        name=f"Herald Test Channel {label}",
                        group="tests",
                        default=0,
                        icon="mdi:flask-outline",
                        translation_key="channel_test",
                        translation_placeholders={"channel_name": label},
                    ),
                )
            )

        return specs

    def build_specs_for_platform(self, platform: CONTROL_PLATFORM) -> list[HeraldControlSpec]:
        """Return all specs for one entity platform."""
        return [spec for spec in self.build_specs() if spec.platform == platform]

    def spec(self, key: str) -> HeraldControlSpec | None:
        """Return the current control spec for one runtime key."""
        return next((spec for spec in self.build_specs() if spec.key == key), None)

    def summary(self) -> dict[str, list[str]]:
        """Return control entity ids grouped for diagnostics and dashboard generation."""
        summary: dict[str, list[str]] = {
            "ai": [],
            "levels": [],
            "rooms": [],
            "users": [],
            "channels": [],
            "flows": [],
            "router": [],
            "tests": [],
        }
        for spec in self.build_specs():
            summary.setdefault(spec.group, []).append(spec.entity_id)
        return {key: sorted(values) for key, values in summary.items()}

    def ensure_defaults(self) -> bool:
        """Seed missing control values, migrating legacy helper state when present."""
        state = self._state_getter()
        changed = False
        known_keys = {spec.key: spec for spec in self.build_specs()}

        for spec in known_keys.values():
            if spec.platform == "button":
                continue
            current = state.control_values.get(spec.key)
            if current is None:
                state.control_values[spec.key] = self._legacy_value_for_spec(spec)
                changed = True
                continue
            coerced = self._coerce_spec_value(spec, current)
            if coerced != current:
                state.control_values[spec.key] = coerced
                changed = True

        for flow_name, enabled in list(state.flow_overrides.items()):
            key = flow_enabled_control_key(flow_name)
            if key not in state.control_values:
                state.control_values[key] = bool(enabled)
                changed = True

        if self._prune_stale_values(known_keys):
            changed = True
        if self.sync_runtime_config():
            changed = True
        return changed

    def sync_runtime_config(self) -> bool:
        """Apply control state to runtime config objects used by the pipeline."""
        changed = False
        for flow_name, flow in self._config.flows.items():
            enabled = bool(self.value(flow_enabled_control_key(flow_name), flow.enabled))
            if flow.enabled != enabled:
                flow.enabled = enabled
                changed = True
            summary_window = int(self.value(flow_summary_window_control_key(flow_name), flow.summary_window_seconds))
            if flow.summary_window_seconds != summary_window:
                flow.summary_window_seconds = summary_window
                changed = True
            dedup_window = int(self.value(flow_dedup_window_control_key(flow_name), flow.dedup_window_seconds))
            if flow.dedup_window_seconds != dedup_window:
                flow.dedup_window_seconds = dedup_window
                changed = True
            cooldown = int(self.value(flow_cooldown_control_key(flow_name), flow.cooldown_seconds))
            if flow.cooldown_seconds != cooldown:
                flow.cooldown_seconds = cooldown
                changed = True

        for channel_name, channel in self._config.channels.items():
            enabled = bool(self.value(channel_enabled_control_key(channel_name), channel.enabled))
            if channel.enabled != enabled:
                channel.enabled = enabled
                changed = True
            min_level = str(self.value(channel_min_level_control_key(channel_name), channel.min_level))
            if channel.min_level != min_level:
                channel.min_level = min_level
                changed = True

        maintenance_level = str(
            self.value(
                maintenance_min_level_control_key(),
                self._config.router.get(CONF_MAINTENANCE_MIN_LEVEL, DEFAULT_MAINTENANCE_MIN_LEVEL),
            )
        )
        if self._config.router.get(CONF_MAINTENANCE_MIN_LEVEL) != maintenance_level:
            self._config.router[CONF_MAINTENANCE_MIN_LEVEL] = maintenance_level
            changed = True
        return changed

    def value(self, key: str, default: Any = None) -> Any:
        """Return a control value from runtime state."""
        return self._state_getter().control_values.get(key, default)

    def set_value(self, key: str, value: Any) -> bool:
        """Persist a control value into runtime state."""
        specs = {spec.key: spec for spec in self.build_specs()}
        spec = specs.get(key)
        if spec is None or spec.platform == "button":
            return False
        coerced = self._coerce_spec_value(spec, value)
        state = self._state_getter()
        if state.control_values.get(key) == coerced:
            return False
        state.control_values[key] = coerced
        if key.startswith("flow_enabled:"):
            flow_name = key.split(":", maxsplit=1)[1]
            state.flow_overrides[flow_name] = bool(coerced)
        self.sync_runtime_config()
        return True

    def is_level_enabled(self, level: str) -> bool:
        """Return whether notifications of the requested level are enabled."""
        mapping = {
            "debug": level_enabled_control_key("info"),
            "info": level_enabled_control_key("info"),
            "notice": level_enabled_control_key("info"),
            "warning": level_enabled_control_key("warning"),
            "ai": level_enabled_control_key("warning"),
            "system": level_enabled_control_key("warning"),
            "critical": level_enabled_control_key("critical"),
            "security": level_enabled_control_key("critical"),
        }
        key = mapping.get(level)
        if key is None:
            return True
        return bool(self.value(key, True))

    def is_ai_enabled(self, level: str | None = None) -> bool:
        """Return whether AI is enabled globally or for one level."""
        if not bool(self.value(ai_enabled_control_key(), True)):
            return False
        if level is None:
            return True
        if level in {"critical", "security"}:
            return bool(self.value(ai_level_control_key("critical"), True))
        if level in {"warning", "ai", "system"}:
            return bool(self.value(ai_level_control_key("warning"), True))
        return bool(self.value(ai_level_control_key("info"), False))

    def is_channel_type_enabled(self, channel_type: str) -> bool:
        """Return whether a channel family is globally enabled."""
        for family, supported_types in CHANNEL_FAMILY_TYPES.items():
            if channel_type in supported_types:
                return bool(self.value(channel_family_control_key(family), True))
        return True

    def user_language(self, user_slug: str, *, default: str = "ru") -> str:
        """Return the selected user language."""
        value = self.value(user_language_control_key(user_slug))
        if isinstance(value, str) and value:
            return normalize_language(value)
        return normalize_language(self._legacy_user_language(user_slug) or default)

    def user_character(self, user_slug: str, *, default: str | None = None) -> str:
        """Return the selected user character."""
        value = self.value(user_character_control_key(user_slug))
        if isinstance(value, str) and value:
            return value
        return default or self._default_character()

    def user_silent(self, user_slug: str) -> bool:
        """Return whether the user is muted for Herald delivery."""
        return bool(self.value(user_silent_control_key(user_slug), False))

    def maintenance_mode_enabled(self) -> bool:
        """Return whether Herald-owned maintenance mode is enabled."""
        return bool(self.value(maintenance_mode_control_key(), False))

    def is_mute_all_enabled(self) -> bool:
        """Return whether Herald global mute is enabled."""
        return bool(self.value(mute_all_control_key(), False))

    def dashboard_sidebar_enabled(self) -> bool:
        """Return whether Herald dashboard should be shown in the sidebar."""
        return bool(self.value(dashboard_sidebar_control_key(), True))

    def room_audio_target(self, room_name: str, *, default: str = "auto") -> str:
        """Return the preferred audio target type for one room."""
        value = self.value(room_audio_target_control_key(room_name), default)
        text = str(value).strip().lower()
        if text:
            return text
        return default

    def room_presence(self, room_name: str) -> bool:
        """Return the Herald fallback room-presence state."""
        return bool(self.value(room_presence_control_key(room_name), False))

    def _prune_stale_values(self, known_keys: dict[str, HeraldControlSpec]) -> bool:
        state = self._state_getter()
        stale = [
            key
            for key in state.control_values
            if key not in known_keys or known_keys[key].platform == "button"
        ]
        if not stale:
            return False
        for key in stale:
            state.control_values.pop(key, None)
        return True

    def _legacy_value_for_spec(self, spec: HeraldControlSpec) -> bool | str | float | int:
        if spec.key.startswith("flow_enabled:"):
            flow_name = spec.key.split(":", maxsplit=1)[1]
            if flow_name in self._state_getter().flow_overrides:
                return bool(self._state_getter().flow_overrides[flow_name])
        entity_id = self._legacy_helper_entity_id(spec.key)
        if entity_id:
            migrated = self._state_from_entity(entity_id, spec)
            if migrated is not None:
                return migrated
        return self._coerce_spec_value(spec, spec.default)

    def _legacy_helper_entity_id(self, key: str) -> str | None:
        if key == ai_enabled_control_key():
            return "input_boolean.herald_ai_enabled"
        if key == maintenance_mode_control_key():
            entity_id = str(self._config.router.get("maintenance_mode_entity", "")).strip()
            return entity_id or "input_boolean.herald_maintenance_mode_sync"
        if key == mute_all_control_key():
            return "input_boolean.herald_mute_all"
        if key == dashboard_sidebar_control_key():
            return "input_boolean.herald_dashboard_sidebar"
        if key == ai_level_control_key("info"):
            return "input_boolean.herald_ai_info"
        if key == ai_level_control_key("warning"):
            return "input_boolean.herald_ai_warning"
        if key == ai_level_control_key("critical"):
            return "input_boolean.herald_ai_critical"
        if key == level_enabled_control_key("info"):
            return "input_boolean.herald_level_info"
        if key == level_enabled_control_key("warning"):
            return "input_boolean.herald_level_warning"
        if key == level_enabled_control_key("critical"):
            return "input_boolean.herald_level_critical"
        if key == channel_family_control_key("voice"):
            return "input_boolean.herald_channel_voice"
        if key == channel_family_control_key("push"):
            return "input_boolean.herald_channel_push"
        if key == channel_family_control_key("tv"):
            return "input_boolean.herald_channel_tv"
        if key.startswith("room_presence:"):
            room_name = key.split(":", maxsplit=1)[1]
            return f"input_boolean.herald_room_{room_name}_presence"
        if key.startswith("room_audio_target:"):
            room_name = key.split(":", maxsplit=1)[1]
            return f"input_select.herald_room_{room_name}_audio_target"
        if key.startswith("user_language:"):
            user_slug = key.split(":", maxsplit=1)[1]
            return f"input_select.herald_user_{user_slug}_language"
        if key.startswith("user_character:"):
            user_slug = key.split(":", maxsplit=1)[1]
            return f"input_select.herald_user_{user_slug}_character"
        if key.startswith("user_silent:"):
            user_slug = key.split(":", maxsplit=1)[1]
            return f"input_boolean.herald_user_{user_slug}_silent"
        return None

    def _state_from_entity(self, entity_id: str, spec: HeraldControlSpec) -> bool | str | int | None:
        state = self._hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable", "none"}:
            return None
        if spec.platform == "button":
            return None
        if spec.platform == "switch":
            return state.state == "on"
        if spec.platform == "number":
            try:
                return int(float(state.state))
            except (TypeError, ValueError):
                return None
        return self._coerce_spec_value(spec, state.state)

    def _coerce_spec_value(self, spec: HeraldControlSpec, value: Any) -> bool | str | float | int:
        if spec.platform == "button":
            return 0
        if spec.platform == "switch":
            if isinstance(value, str):
                return value.lower() in {"on", "true", "1", "yes"}
            return bool(value)
        if spec.platform == "number":
            try:
                numeric = int(float(value))
            except (TypeError, ValueError):
                numeric = int(float(spec.default))
            return max(int(spec.min_value), min(int(spec.max_value), numeric))
        text = str(value) if value is not None else str(spec.default)
        if spec.options and text not in spec.options:
            return str(spec.default)
        return text

    def _person_specs(self) -> list[tuple[str, str]]:
        async_all = getattr(self._hass.states, "async_all", None)
        if async_all is None:
            return []
        people = []
        for state in async_all("person"):
            slug = state.entity_id.split(".", maxsplit=1)[1]
            name = str(state.attributes.get("friendly_name") or _humanize(slug))
            people.append((slug, name))
        return sorted(people)

    def _character_options(self) -> tuple[str, ...]:
        keys = tuple(self._characters.list_character_keys())
        if keys:
            return keys
        return (DEFAULT_PERSONALITY.lower(),)

    def _default_character(self) -> str:
        profile = self._characters.get(None)
        if profile is not None:
            return profile.key
        options = self._character_options()
        return options[0]

    def _legacy_user_language(self, user_slug: str) -> str:
        user_config = self._config.users.get(user_slug)
        if user_config and user_config.language_helper:
            state = self._hass.states.get(user_config.language_helper)
            if state is not None and state.state not in {"unknown", "unavailable"}:
                return normalize_language(state.state)
        legacy_state = self._hass.states.get(f"input_select.herald_user_{user_slug}_language")
        if legacy_state is not None and legacy_state.state not in {"unknown", "unavailable"}:
            return normalize_language(legacy_state.state)
        return "ru"

    def _room_audio_target_options(self) -> dict[str, tuple[str, ...]]:
        """Return room-level selectable output target types when several device families exist."""
        channel = self._config.channels.get("voice_auto")
        if channel is None:
            return {}
        audio_targets = dict(channel.data.get("audio_targets", {}))
        options_by_room: dict[str, tuple[str, ...]] = {}
        for room_name, targets in audio_targets.items():
            kinds = [
                kind
                for kind in ("alisa", "homepod")
                if any(str(item.get("kind", "")).strip().lower() == kind for item in targets)
            ]
            if len(kinds) <= 1:
                continue
            options_by_room[str(room_name)] = tuple(["auto", *kinds])
        return options_by_room


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()
