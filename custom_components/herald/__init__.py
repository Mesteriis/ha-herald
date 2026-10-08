"""Herald notification center integration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

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


def _merge_config(*layers: Mapping[str, Any]) -> dict[str, Any]:
    """Merge nested YAML, entry and options mappings without mutating any layer."""
    merged: dict[str, Any] = {}
    for layer in layers:
        for key, value in layer.items():
            previous = merged.get(key)
            if isinstance(value, Mapping) and isinstance(previous, Mapping):
                merged[key] = _merge_config(previous, value)
            else:
                merged[key] = deepcopy(value)
    return merged


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply edited control values before reload, without replaying older snapshots."""
    coordinator = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {}).get(entry.entry_id)
    if coordinator is not None:
        await coordinator.async_apply_option_control_updates(entry.options)
    await hass.config_entries.async_reload(entry.entry_id)


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
    from .services import async_setup_services, async_unload_services

    hass.data.setdefault(DOMAIN, {})
    coordinators = hass.data[DOMAIN].setdefault(DATA_COORDINATORS, {})
    raw_config = _merge_config(
        hass.data[DOMAIN].get(DATA_YAML_CONFIG, {}), entry.data, entry.options
    )
    setup_complete = False
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
        entry.async_on_unload(entry.add_update_listener(_async_update_options))
        setup_complete = True
        return True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Herald setup failed")
        raise
    finally:
        if not setup_complete:
            cleanup = [async_unload_services(hass)]
            failed_coordinator = coordinators.pop(entry.entry_id, None)
            if failed_coordinator is not None:
                cleanup.append(failed_coordinator.async_shutdown())
            registration = hass.data[DOMAIN].pop(DATA_FRONTEND_REGISTRATION, None)
            if registration is not None:
                cleanup.append(registration.async_shutdown())
            hass.data[DOMAIN].pop(DATA_FRONTEND_REGISTERED, None)
            for result in await asyncio.gather(*cleanup, return_exceptions=True):
                if isinstance(result, BaseException):
                    _LOGGER.error("Herald setup cleanup failed: %s", type(result).__name__)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Herald config entry."""
    from .services import async_unload_services

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    registration = hass.data[DOMAIN].get(DATA_FRONTEND_REGISTRATION)
    try:
        await coordinator.async_shutdown()
    finally:
        if registration is not None:
            await registration.async_shutdown()
    hass.data[DOMAIN][DATA_COORDINATORS].pop(entry.entry_id)
    hass.data[DOMAIN].pop(DATA_FRONTEND_REGISTRATION, None)
    hass.data[DOMAIN].pop(DATA_FRONTEND_REGISTERED, None)
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
    registered = False
    try:
        await registration.async_register()
        registered = True
    finally:
        if not registered:
            await registration.async_shutdown()
    hass.data[DOMAIN][DATA_FRONTEND_REGISTRATION] = registration
    hass.data[DOMAIN][DATA_FRONTEND_REGISTERED] = True
