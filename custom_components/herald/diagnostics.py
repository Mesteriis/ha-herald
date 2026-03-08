"""Diagnostics support for Herald."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATORS, DOMAIN, REDACT_CONFIG


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a Herald config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    return {
        "entry": async_redact_data(dict(entry.data), REDACT_CONFIG),
        "config": async_redact_data(coordinator.config.to_dict(), REDACT_CONFIG),
        "runtime": coordinator.trace_snapshot(),
        "snapshot": coordinator.data,
    }
