"""Diagnostics support for Herald."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATORS, DOMAIN, REDACT_CONFIG

_COUNTERS = ("notifications_today", "deliveries_today", "dropped_today", "errors_today", "ai_requests_today")
_COLLECTIONS = ("traces", "recent_notifications", "dashboard_feed", "queued_notifications", "notification_policies")


def _redact_config(config: dict[str, Any]) -> dict[str, Any]:
    """Mask credential keys even when provider data uses different key casing."""
    sensitive_keys = set(REDACT_CONFIG)

    def collect_keys(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key).casefold().replace("-", "_") in REDACT_CONFIG:
                    sensitive_keys.add(key)
                collect_keys(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect_keys(child)

    collect_keys(config)
    return async_redact_data(config, sensitive_keys)


def _runtime_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Export aggregate health only, without messages, routes or presence context."""
    summary = {key: value for key in _COUNTERS if type(value := payload.get(key)) is int}
    summary.update(
        {f"{key}_count": len(value) for key in _COLLECTIONS
         if isinstance(value := payload.get(key), (dict, list, tuple))}
    )
    analytics = payload.get("analytics")
    if isinstance(analytics, Mapping):
        summary["analytics"] = {
            key: value for key in _COUNTERS if type(value := analytics.get(key)) is int
        }
    return summary


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return redacted configuration and minimal aggregate runtime diagnostics."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    return {
        "entry": _redact_config(dict(entry.data)),
        "options": _redact_config(dict(entry.options)),
        "config": _redact_config(coordinator.config.to_dict()),
        "runtime": _runtime_summary(coordinator.trace_snapshot()),
        "snapshot": _runtime_summary(coordinator.data or {}),
    }
