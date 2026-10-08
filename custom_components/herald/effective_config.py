"""Effective settings and sparse Options updates shared with runtime controls."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from uuid import uuid4

from homeassistant.helpers.storage import Store

from . import _merge_config
from .const import DATA_COORDINATORS, DATA_YAML_CONFIG, DOMAIN, STORAGE_KEY, STORAGE_VERSION
from .models import HeraldConfig

OPTIONS_CONTROL_UPDATES = "_herald_control_updates"
CONTROL_LEVEL_OPTIONS = ("debug", "info", "notice", "ai", "warning", "system", "critical", "security")
Path = tuple[str, ...]
_MISSING = object()


def control_config_path(key: str) -> Path | None:
    """Map only controls which share an actual configuration setting."""
    if key == "ai_enabled":
        return ("ollama", "enabled")
    if key == "maintenance_min_level":
        return ("router", "maintenance_min_level")
    family, separator, name = key.partition(":")
    if not separator:
        return None
    fields = {
        "channel_enabled": ("channels", "enabled"),
        "channel_min_level": ("channels", "min_level"),
        "flow_enabled": ("flows", "enabled"),
        "flow_summary_window": ("flows", "summary_window_seconds"),
        "flow_dedup_window": ("flows", "dedup_window_seconds"),
        "flow_cooldown": ("flows", "cooldown_seconds"),
    }
    if family not in fields:
        return None
    section, field = fields[family]
    return section, name, field


def path_value(config: Mapping[str, Any], path: Path, default: Any = None) -> Any:
    value: Any = config
    for part in path:
        if not isinstance(value, Mapping) or part not in value:
            return default
        value = value[part]
    return value


def set_path(config: dict[str, Any], path: Path, value: Any) -> None:
    current = config
    for part in path[:-1]:
        current = current.setdefault(part, {})
    current[path[-1]] = deepcopy(value)


def configuration_defaults(
    layers: Mapping[str, Mapping[str, Any]], fallback: Mapping[str, Any]
) -> dict[str, Any]:
    """Recompute typed defaults from current raw layers without retaining deleted overrides."""
    if not layers:
        return deepcopy(dict(fallback))
    raw = _merge_config(*(layers.get(source, {}) for source in ("yaml", "entry", "options")))
    return HeraldConfig.from_raw(raw).to_dict()


def inherited_setting(
    key: str, layers: Mapping[str, Mapping[str, Any]], defaults: Mapping[str, Any], fallback: Any
) -> tuple[Any, str]:
    """Resolve inheritance from immutable configuration layers, never mutated runtime config."""
    path = control_config_path(key)
    if path is None:
        return fallback, "default"
    for source in ("options", "entry", "yaml"):
        value = path_value(layers.get(source, {}), path, _MISSING)
        if value is not _MISSING:
            return value, source
    return path_value(defaults, path, fallback), "default"


def options_field_bindings(config: Mapping[str, Any]) -> dict[str, tuple[Path, str | None]]:
    """Return the editable fields, their config paths and optional runtime control keys."""
    fields: dict[str, tuple[Path, str | None]] = {
        "host": (("ollama", "host"), None),
        "model": (("ollama", "model"), None),
        "provider": (("ollama", "provider"), None),
        "start": (("quiet_hours", "start"), None),
        "end": (("quiet_hours", "end"), None),
        "maintenance_mode_entity": (("router", "maintenance_mode_entity"), None),
        "maintenance_min_level": (("router", "maintenance_min_level"), "maintenance_min_level"),
    }
    for channel in config.get("channels", {}):
        fields[f"channel_enabled__{channel}"] = (("channels", channel, "enabled"), f"channel_enabled:{channel}")
        fields[f"channel_min_level__{channel}"] = (("channels", channel, "min_level"), f"channel_min_level:{channel}")
    for flow in config.get("flows", {}):
        fields[f"summary_personality__{flow}"] = (("flows", flow, "summary_personality"), None)
        fields[f"cooldown_seconds__{flow}"] = (("flows", flow, "cooldown_seconds"), f"flow_cooldown:{flow}")
        fields[f"dedup_window_seconds__{flow}"] = (("flows", flow, "dedup_window_seconds"), f"flow_dedup_window:{flow}")
    return fields


def normalize_option_value(field: str, value: Any) -> Any:
    if field == "host":
        return str(value).strip()
    if field.startswith("summary_personality__"):
        return str(value or "").strip() or None
    if field.startswith(("cooldown_seconds__", "dedup_window_seconds__")):
        return int(value)
    if field == "maintenance_mode_entity":
        return str(value).strip()
    return value


def options_form_values(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        field: normalize_option_value(field, path_value(config, path))
        for field, (path, _) in options_field_bindings(config).items()
    }


def edited_options(
    latest_options: Mapping[str, Any],
    displayed: Mapping[str, Any],
    submitted: Mapping[str, Any],
    bindings: Mapping[str, tuple[Path, str | None]],
) -> dict[str, Any]:
    """Patch only explicit edits into the latest options, preserving concurrent other changes."""
    result = deepcopy(dict(latest_options))
    for field, value in submitted.items():
        if field not in bindings:
            continue
        value = normalize_option_value(field, value)
        if field in displayed and value == normalize_option_value(field, displayed[field]):
            continue
        path, control = bindings[field]
        set_path(result, path, value)
        if control is not None:
            result.setdefault(OPTIONS_CONTROL_UPDATES, {})[control] = {
                "revision": uuid4().hex,
                "value": deepcopy(value),
            }
    return result


async def async_options_config(hass, entry) -> dict[str, Any]:
    """Read current settings without writing the runtime Store or freezing discovery in options."""
    domain_data = getattr(hass, "data", {}).get(DOMAIN, {}) if hass is not None else {}
    coordinator = domain_data.get(DATA_COORDINATORS, {}).get(getattr(entry, "entry_id", ""))
    if coordinator is not None:
        config = deepcopy(coordinator.config.to_dict())
        for key, setting in coordinator.controls.effective_settings().items():
            if path := control_config_path(key):
                set_path(config, path, setting["value"])
        return config

    raw = _merge_config(domain_data.get(DATA_YAML_CONFIG, {}), entry.data, entry.options)
    config = HeraldConfig.from_raw(raw).to_dict()
    stored = await Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}").async_load() if hass is not None else None
    stored = stored or {}
    metadata = stored.get("control_metadata", {})
    for key, value in stored.get("control_values", {}).items():
        provenance = metadata.get(key, {})
        if provenance.get("source") in {"yaml", "entry", "options", "default"} and not provenance.get("option_revision"):
            continue
        if path := control_config_path(key):
            if len(path) == 3 and path[1] not in config.get(path[0], {}):
                continue
            if key == "ai_enabled" and key not in metadata:
                value = bool(value) and bool(path_value(config, path, True))
            set_path(config, path, value)
    for key, update in entry.options.get(OPTIONS_CONTROL_UPDATES, {}).items():
        if not isinstance(update, Mapping) or not update.get("revision"):
            continue
        if metadata.get(key, {}).get("option_revision") == update["revision"]:
            continue
        if path := control_config_path(key):
            if len(path) == 3 and path[1] not in config.get(path[0], {}):
                continue
            set_path(config, path, update.get("value"))
    return config
