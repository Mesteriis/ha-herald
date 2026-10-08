"""Regression coverage for configuration, diagnostics and frontend lifecycle."""

from __future__ import annotations

import asyncio
import json
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.herald import _async_update_options, _merge_config, async_setup_entry, async_unload_entry
from custom_components.herald.config_flow import HeraldConfigFlow, HeraldOptionsFlow
from custom_components.herald.const import DATA_COORDINATORS, DATA_FRONTEND_REGISTRATION, DATA_YAML_CONFIG, DOMAIN
from custom_components.herald.diagnostics import async_get_config_entry_diagnostics
from custom_components.herald.frontend_registry import HeraldFrontendRegistration


def test_configuration_layers_preserve_nested_base_and_do_not_alias() -> None:
    base = {"channels": {"voice": {"type": "tts_hume", "data": {"api_key": "synthetic", "voice_name": "name"}}}, "ollama": {"enabled": False}}
    entry = {"ollama": {"host": "http://localhost"}, "router": {"recent_limit": 3}}
    options = {"ollama": {"model": "model"}, "channels": {"voice": {"data": {"voice_name": "new"}, "enabled": False}}}
    result = _merge_config(base, entry, options)
    assert result["ollama"] == {"enabled": False, "host": "http://localhost", "model": "model"}
    assert result["channels"]["voice"]["data"] == {"api_key": "synthetic", "voice_name": "new"}
    result["channels"]["voice"]["data"]["api_key"] = "different"
    assert base["channels"]["voice"]["data"]["api_key"] == "synthetic"


@pytest.mark.asyncio
async def test_setup_merges_options_and_registers_reload_listener(monkeypatch) -> None:
    coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock(), async_shutdown=AsyncMock(), async_apply_option_control_updates=AsyncMock())
    factory = Mock(return_value=coordinator)
    listener = Mock(return_value=Mock())
    entry = SimpleNamespace(entry_id="entry", data={"ollama": {"enabled": False}}, options={"ollama": {"model": "new"}}, add_update_listener=listener, async_on_unload=Mock())
    hass = SimpleNamespace(data={DOMAIN: {DATA_YAML_CONFIG: {"ollama": {"host": "http://local"}}}}, config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock(), async_reload=AsyncMock()))
    coordinator_module = ModuleType("custom_components.herald.coordinator")
    coordinator_module.HeraldCoordinator = factory
    monkeypatch.setitem(sys.modules, "custom_components.herald.coordinator", coordinator_module)
    services = ModuleType("custom_components.herald.services")
    services.async_setup_services = AsyncMock()
    services.async_unload_services = AsyncMock()
    monkeypatch.setitem(sys.modules, "custom_components.herald.services", services)
    monkeypatch.setattr("custom_components.herald._async_register_frontend", AsyncMock())
    assert await async_setup_entry(hass, entry)
    assert factory.call_args.args[2]["ollama"] == {"host": "http://local", "enabled": False, "model": "new"}
    listener.assert_called_once_with(_async_update_options)
    entry.async_on_unload.assert_called_once_with(listener.return_value)
    await listener.call_args.args[0](hass, entry)
    hass.config_entries.async_reload.assert_awaited_once_with("entry")


@pytest.mark.asyncio
async def test_unload_shuts_down_frontend_and_coordinator(monkeypatch) -> None:
    coordinator = SimpleNamespace(async_shutdown=AsyncMock())
    registration = SimpleNamespace(async_shutdown=AsyncMock())
    hass = SimpleNamespace(data={DOMAIN: {DATA_COORDINATORS: {"entry": coordinator}, DATA_FRONTEND_REGISTRATION: registration}}, config_entries=SimpleNamespace(async_unload_platforms=AsyncMock(return_value=True)))
    services = ModuleType("custom_components.herald.services")
    services.async_unload_services = AsyncMock()
    monkeypatch.setitem(sys.modules, "custom_components.herald.services", services)
    assert await async_unload_entry(hass, SimpleNamespace(entry_id="entry"))
    registration.async_shutdown.assert_awaited_once()
    coordinator.async_shutdown.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["25:00", "12:60", "7:30", "-1:00", "23:00:00", "invalid"])
async def test_config_flow_rejects_invalid_quiet_hours(invalid) -> None:
    flow = HeraldConfigFlow()
    result = await flow.async_step_user({"name": "Herald", "host": "http://local", "model": "model", "start": invalid, "end": "08:00"})
    assert result["type"] == "form"
    assert result["errors"] == {"start": "invalid_time"}


@pytest.mark.asyncio
async def test_options_keep_hidden_values_and_validate_quiet_hours() -> None:
    entry = SimpleNamespace(data={"ollama": {"enabled": False}, "channels": {"voice": {"type": "tts_hume", "data": {"api_key": "synthetic"}}}}, options={"router": {"recent_limit": 10}, "channels": {"voice": {"enabled": False}}})
    flow = HeraldOptionsFlow(entry)
    user = {"start": "23:00", "end": "08:00"}
    await flow.async_step_quiet_hours()
    invalid = await flow.async_step_quiet_hours({**user, "end": "24:00"})
    assert invalid["errors"] == {"end": "invalid_time"}
    result = await flow.async_step_quiet_hours(user)
    assert result["data"]["router"]["recent_limit"] == 10
    assert _merge_config(entry.data, result["data"])["channels"]["voice"]["data"] == {"api_key": "synthetic"}
    assert result["data"]["channels"]["voice"]["enabled"] is False


@pytest.mark.asyncio
async def test_diagnostics_redact_credentials_and_omit_private_runtime() -> None:
    secret = "SYNTHETIC_SECRET_NEVER_EXPORT"
    private = "SYNTHETIC_PRIVATE_MESSAGE_OR_PERSON"
    config = {"channels": {"voice": {"data": {"api_key": secret, "Authorization": secret, "API-KEY": secret, "nested": [{"password": secret}]}}}}
    entry = SimpleNamespace(entry_id="entry", data=config, options={"token": secret})
    coordinator = SimpleNamespace(config=SimpleNamespace(to_dict=lambda: config), data={"last_notification": private, "notifications_today": 5, "presence": private}, trace_snapshot=lambda: {"traces": [{"text": private, "api_key": secret}], "last_route_preview": private, "analytics": {"deliveries_today": 2, "channel_delivery_counts": {private: 3}}})
    hass = SimpleNamespace(data={DOMAIN: {DATA_COORDINATORS: {"entry": coordinator}}})
    result = await async_get_config_entry_diagnostics(hass, entry)
    encoded = json.dumps(result)
    assert secret not in encoded
    assert private not in encoded
    assert result["runtime"] == {"traces_count": 1, "analytics": {"deliveries_today": 2}}
    assert result["snapshot"] == {"notifications_today": 5}


@pytest.mark.asyncio
async def test_frontend_yaml_mode_does_not_retry_or_remove_existing_dashboard(monkeypatch) -> None:
    dashboard = object()
    hass = SimpleNamespace(data={"lovelace": {"mode": "yaml", "dashboards": {"herald-center": dashboard}}})
    registration = HeraldFrontendRegistration(hass, dashboard_factory=lambda: {})
    schedule = Mock()
    monkeypatch.setattr(registration, "_async_schedule_retry", schedule)
    monkeypatch.setattr(registration, "_prefer_yaml_dashboard", lambda: True)
    await registration._async_register_lovelace_artifacts()
    schedule.assert_not_called()
    assert hass.data["lovelace"]["dashboards"]["herald-center"] is dashboard


@pytest.mark.asyncio
async def test_frontend_shutdown_cancels_retry_and_stale_callback_cannot_restart(monkeypatch) -> None:
    cancel = Mock()
    callbacks = []
    def schedule(hass, delay, callback):
        callbacks.append(callback)
        return cancel
    monkeypatch.setattr("custom_components.herald.frontend_registry.async_call_later", schedule)
    registration = HeraldFrontendRegistration(SimpleNamespace(data={}))
    await registration._async_register_lovelace_artifacts()
    assert len(callbacks) == 1
    await registration.async_shutdown()
    cancel.assert_called_once()
    await callbacks[0](None)
    assert len(callbacks) == 1


@pytest.mark.asyncio
async def test_yaml_import_rejects_invalid_quiet_hours() -> None:
    flow = HeraldConfigFlow()
    result = await flow.async_step_import({"quiet_hours": {"start": "invalid"}})
    assert result == {"type": "abort", "reason": "invalid_quiet_hours"}


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [RuntimeError("setup failed"), asyncio.CancelledError()])
async def test_failed_or_cancelled_setup_shuts_down_created_resources(monkeypatch, error) -> None:
    coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock(), async_shutdown=AsyncMock(), async_apply_option_control_updates=AsyncMock())
    registration = SimpleNamespace(async_shutdown=AsyncMock())
    module = ModuleType("custom_components.herald.coordinator")
    module.HeraldCoordinator = Mock(return_value=coordinator)
    monkeypatch.setitem(sys.modules, "custom_components.herald.coordinator", module)
    services = ModuleType("custom_components.herald.services")
    services.async_setup_services = AsyncMock()
    services.async_unload_services = AsyncMock()
    monkeypatch.setitem(sys.modules, "custom_components.herald.services", services)
    entry = SimpleNamespace(entry_id="entry", data={}, options={})
    hass = SimpleNamespace(data={DOMAIN: {DATA_FRONTEND_REGISTRATION: registration}}, config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock(side_effect=error)))
    monkeypatch.setattr("custom_components.herald._async_register_frontend", AsyncMock())
    with pytest.raises(type(error)):
        await async_setup_entry(hass, entry)
    assert hass.data[DOMAIN][DATA_COORDINATORS] == {}
    assert DATA_FRONTEND_REGISTRATION not in hass.data[DOMAIN]
    registration.async_shutdown.assert_awaited_once()
    coordinator.async_shutdown.assert_awaited_once()
    services.async_unload_services.assert_awaited_once_with(hass)


@pytest.mark.asyncio
async def test_failed_unload_stops_frontend_but_retains_coordinator_for_retry(monkeypatch) -> None:
    coordinator = SimpleNamespace(async_shutdown=AsyncMock(side_effect=RuntimeError("failed to save state")))
    registration = SimpleNamespace(async_shutdown=AsyncMock())
    services = ModuleType("custom_components.herald.services")
    services.async_unload_services = AsyncMock()
    monkeypatch.setitem(sys.modules, "custom_components.herald.services", services)
    hass = SimpleNamespace(data={DOMAIN: {DATA_COORDINATORS: {"entry": coordinator}, DATA_FRONTEND_REGISTRATION: registration}}, config_entries=SimpleNamespace(async_unload_platforms=AsyncMock(return_value=True)))
    with pytest.raises(RuntimeError, match="failed to save"):
        await async_unload_entry(hass, SimpleNamespace(entry_id="entry"))
    assert hass.data[DOMAIN][DATA_COORDINATORS]["entry"] is coordinator
    registration.async_shutdown.assert_awaited_once()
    services.async_unload_services.assert_not_awaited()
