"""Herald notification center integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DATA_COORDINATORS,
    DATA_FRONTEND_REGISTERED,
    DATA_FRONTEND_REGISTRATION,
    DATA_YAML_CONFIG,
    DOMAIN,
    PLATFORMS,
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: dict}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)


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
        for section in ("ollama", "quiet_hours", "router"):
            if section in entry.options:
                raw_config[section] = {
                    **dict(raw_config.get(section, {})),
                    **dict(entry.options[section]),
                }
        for section in ("channels", "flows"):
            if section not in entry.options:
                continue
            merged = {
                key: dict(value)
                for key, value in dict(raw_config.get(section, {})).items()
            }
            for key, value in dict(entry.options[section]).items():
                merged[key] = {
                    **dict(merged.get(key, {})),
                    **dict(value),
                }
            raw_config[section] = merged
    try:
        coordinator = HeraldCoordinator(hass, entry, raw_config)
        coordinators[entry.entry_id] = coordinator

        await coordinator.async_config_entry_first_refresh()
        try:
            await _async_register_frontend(hass, coordinator)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Herald frontend registration failed; continuing with core setup")
        await async_setup_services(hass)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Herald setup failed")
        raise


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Herald config entry."""
    from .services import async_unload_services

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    coordinator = hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id)
    hass.data[DOMAIN].pop(DATA_FRONTEND_REGISTRATION, None)
    hass.data[DOMAIN].pop(DATA_FRONTEND_REGISTERED, None)
    await coordinator.async_shutdown()
    await async_unload_services(hass)
    return True


async def _async_register_frontend(hass: HomeAssistant, coordinator) -> None:
    """Expose and register the Herald frontend card for Lovelace/editor use."""
    if hass.data[DOMAIN].get(DATA_FRONTEND_REGISTERED):
        return

    from .frontend_registry import HeraldFrontendRegistration

    registration = HeraldFrontendRegistration(
        hass,
        dashboard_factory=coordinator.build_dashboard_config,
        sidebar_visible_getter=coordinator.controls.dashboard_sidebar_enabled,
    )
    await registration.async_register()
    hass.data[DOMAIN][DATA_FRONTEND_REGISTRATION] = registration
    hass.data[DOMAIN][DATA_FRONTEND_REGISTERED] = True
