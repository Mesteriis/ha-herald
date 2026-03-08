"""Herald notification center integration."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DATA_COORDINATORS,
    DATA_FRONTEND_REGISTERED,
    DATA_YAML_CONFIG,
    DOMAIN,
    FRONTEND_BASE_URL,
    FRONTEND_DIR,
    PLATFORMS,
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: dict}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Herald from YAML and trigger import flow when needed."""
    hass.data.setdefault(DOMAIN, {})
    yaml_config = dict(config.get(DOMAIN, {}))
    hass.data[DOMAIN][DATA_YAML_CONFIG] = yaml_config

    if yaml_config and not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=yaml_config,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Herald from a config entry."""
    from .coordinator import HeraldCoordinator
    from .services import async_setup_services

    hass.data.setdefault(DOMAIN, {})
    coordinators = hass.data[DOMAIN].setdefault(DATA_COORDINATORS, {})
    raw_config = dict(entry.data)
    if yaml_config := dict(hass.data[DOMAIN].get(DATA_YAML_CONFIG, {})):
        raw_config = {**yaml_config, **raw_config}
    if entry.options:
        raw_config = {**raw_config, **dict(entry.options)}
        if "ollama" in entry.options:
            raw_config["ollama"] = {**dict(raw_config.get("ollama", {})), **dict(entry.options["ollama"])}
        if "quiet_hours" in entry.options:
            raw_config["quiet_hours"] = {**dict(raw_config.get("quiet_hours", {})), **dict(entry.options["quiet_hours"])}
    coordinator = HeraldCoordinator(hass, entry, raw_config)
    coordinators[entry.entry_id] = coordinator

    await _async_register_frontend(hass)
    await coordinator.async_config_entry_first_refresh()
    await async_setup_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Herald config entry."""
    from .services import async_unload_services

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    coordinator = hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id)
    await coordinator.async_shutdown()
    await async_unload_services(hass)
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Expose the bundled Herald frontend files under a local URL."""
    if hass.data[DOMAIN].get(DATA_FRONTEND_REGISTERED):
        return

    from homeassistant.components.http import StaticPathConfig

    frontend_dir = Path(__file__).resolve().parent / FRONTEND_DIR
    if not frontend_dir.exists():
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_BASE_URL, str(frontend_dir), cache_headers=False)]
    )
    hass.data[DOMAIN][DATA_FRONTEND_REGISTERED] = True
