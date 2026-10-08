"""Effective configuration parity, sparse edits and durable revision regression tests."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.herald import _merge_config
from custom_components.herald.config_flow import HeraldOptionsFlow
from custom_components.herald.const import DATA_COORDINATORS, DOMAIN
from custom_components.herald.controls import HeraldControlManager
from custom_components.herald.effective_config import (
    OPTIONS_CONTROL_UPDATES,
    async_options_config,
    edited_options,
    options_field_bindings,
    options_form_values,
)
from custom_components.herald.models import HeraldConfig, RuntimeState


def make_controls(*, yaml=None, data=None, options=None, state=None):
    layers = {"yaml": yaml or {}, "entry": data or {}, "options": options or {}}
    config = HeraldConfig.from_raw(_merge_config(*layers.values()))
    state = state or RuntimeState(current_day="2026-09-30")
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: None, async_all=lambda domain: []))
    presence = SimpleNamespace(room_sensors=lambda: {})
    characters = SimpleNamespace(list_character_keys=lambda: ["hestia"], get=lambda name: SimpleNamespace(key="hestia"))
    controls = HeraldControlManager(hass, config, presence, characters, lambda: state, config_layers_getter=lambda: layers)
    return controls, config, state, layers


def channel_config():
    return {"channels": {"phone": {"type": "mobile_app", "service": "notify.mobile_app_synthetic", "enabled": True, "min_level": "info"}}, "router": {"recent_limit": 7}, "ollama": {"enabled": False}}


def form_defaults(result):
    return {
        marker.schema: marker.description["suggested_value"]
        if marker.description and "suggested_value" in marker.description
        else marker.default()
        for marker in result["data_schema"].schema
    }


async def options_flow(monkeypatch, controls, config, entry):
    hass = SimpleNamespace(data={DOMAIN: {DATA_COORDINATORS: {entry.entry_id: SimpleNamespace(config=config, controls=controls)}}})
    monkeypatch.setattr("custom_components.herald.config_flow.async_discover_runtime_channels", AsyncMock(return_value={}))
    flow = HeraldOptionsFlow(entry)
    flow.hass = hass
    return flow


def test_migrate_restored_controls_without_resetting_preferences_or_enabling_ai() -> None:
    state = RuntimeState(current_day="2026-09-30", control_values={"channel_min_level:phone": "warning", "ai_enabled": True})
    controls, config, state, _ = make_controls(data=channel_config(), state=state)
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "warning"
    assert config.ollama["enabled"] is False
    settings = controls.effective_settings()
    assert settings["channel_min_level:phone"] == {"value": "warning", "source": "restored", "inherited": "info", "inherited_source": "entry"}
    assert settings["ai_enabled"]["source"] == "restored"


def test_inherited_provenance_is_not_taken_from_mutated_runtime_config() -> None:
    controls, config, _, layers = make_controls(yaml=channel_config(), data={"channels": {"phone": {"min_level": "notice"}}}, options={"channels": {"phone": {"min_level": "security"}}})
    controls.ensure_defaults()
    assert controls.value("channel_min_level:phone") == "security"
    controls.set_value("channel_min_level:phone", "warning")
    assert config.channels["phone"].min_level == "warning"
    setting = controls.effective_settings()["channel_min_level:phone"]
    assert setting == {"value": "warning", "source": "runtime", "inherited": "security", "inherited_source": "options"}
    layers["options"]["channels"]["phone"]["min_level"] = "debug"
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "warning"
    assert controls.effective_settings()["channel_min_level:phone"]["inherited"] == "debug"


def test_new_inherited_values_follow_config_until_explicitly_changed() -> None:
    controls, config, state, layers = make_controls(yaml=channel_config())
    controls.ensure_defaults()
    assert state.control_metadata["channel_min_level:phone"]["source"] == "yaml"
    layers["yaml"]["channels"]["phone"]["min_level"] = "critical"
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "critical"
    controls.set_value("channel_min_level:phone", "notice")
    layers["yaml"]["channels"]["phone"]["min_level"] = "debug"
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "notice"


def test_options_revision_is_consumed_once_and_later_control_edit_survives_restart() -> None:
    controls, config, state, layers = make_controls(data=channel_config())
    controls.ensure_defaults()
    options = {"channels": {"phone": {"min_level": "security"}}, OPTIONS_CONTROL_UPDATES: {"channel_min_level:phone": {"revision": "revision-1", "value": "security"}}}
    layers["options"] = options
    assert controls.apply_option_updates(options) is True
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "security"
    controls.set_value("channel_min_level:phone", "warning")
    assert controls.apply_option_updates(options) is False
    restored = RuntimeState.from_dict(state.to_dict())
    next_controls, next_config, _, _ = make_controls(data=channel_config(), options=options, state=restored)
    assert next_controls.apply_option_updates(options) is False
    next_controls.ensure_defaults()
    assert next_config.channels["phone"].min_level == "warning"
    assert next_controls.effective_settings()["channel_min_level:phone"]["source"] == "runtime"


def test_option_domain_matches_ha_controls_for_all_levels_and_full_duration() -> None:
    controls, config, _, _ = make_controls(data=channel_config())
    controls.ensure_defaults()
    controls.set_value("channel_min_level:phone", "security")
    controls.set_value("maintenance_min_level", "notice")
    controls.set_value("flow_cooldown:system_events", 7200)
    controls.set_value("flow_dedup_window:system_events", 86400)
    assert config.channels["phone"].min_level == "security"
    assert config.router["maintenance_min_level"] == "notice"
    assert config.flows["system_events"].cooldown_seconds == 7200
    assert config.flows["system_events"].dedup_window_seconds == 86400


@pytest.mark.asyncio
async def test_options_show_runtime_and_save_only_edited_fields(monkeypatch) -> None:
    controls, config, _, _ = make_controls(data=channel_config())
    controls.ensure_defaults()
    controls.set_value("channel_min_level:phone", "warning")
    entry = SimpleNamespace(entry_id="test", data=channel_config(), options={"router": {"recent_limit": 11}})
    flow = await options_flow(monkeypatch, controls, config, entry)
    form = await flow.async_step_channel_select({"channel": "phone"})
    submitted = form_defaults(form)
    assert submitted["min_level"] == "warning"
    # Another HA control edit occurs after the form was opened.
    controls.set_value("channel_min_level:phone", "critical")
    result = await flow.async_step_channel(submitted)
    assert result["data"] == {"router": {"recent_limit": 11}}
    assert controls.value("channel_min_level:phone") == "critical"
    await flow.async_step_init()
    submitted = form_defaults(await flow.async_step_ai())
    submitted["model"] = "changed-model"
    result = await flow.async_step_ai(submitted)
    assert result["data"] == {"router": {"recent_limit": 11}, "ollama": {"model": "changed-model"}}


@pytest.mark.asyncio
async def test_edited_option_wins_only_its_control_and_survives_invalid_form_retry(monkeypatch) -> None:
    controls, config, state, layers = make_controls(data=channel_config())
    controls.ensure_defaults()
    controls.set_value("channel_min_level:phone", "warning")
    entry = SimpleNamespace(entry_id="test", data=channel_config(), options={})
    flow = await options_flow(monkeypatch, controls, config, entry)
    submitted = form_defaults(await flow.async_step_channel_select({"channel": "phone"}))
    submitted["min_level"] = "invalid"
    assert (await flow.async_step_channel(submitted))["errors"] == {"min_level": "invalid_value"}
    controls.set_value("flow_cooldown:system_events", 1234)
    submitted["min_level"] = "notice"
    result = await flow.async_step_channel(submitted)
    updates = result["data"][OPTIONS_CONTROL_UPDATES]
    assert set(updates) == {"channel_min_level:phone"}
    layers["options"] = result["data"]
    assert controls.apply_option_updates(result["data"])
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "notice"
    assert config.flows["system_events"].cooldown_seconds == 1234
    assert state.control_metadata["channel_min_level:phone"]["source"] == "options"


def test_sparse_patch_keeps_latest_unexposed_and_other_flow_changes() -> None:
    config = HeraldConfig.from_raw(channel_config()).to_dict()
    displayed = options_form_values(config)
    submitted = {**displayed, "model": "new"}
    latest = {"channels": {"phone": {"data": {"api_key": "synthetic"}}}, "router": {"trace_limit": 91}, "quiet_hours": {"start": "22:00"}}
    result = edited_options(latest, displayed, submitted, options_field_bindings(config))
    assert result["quiet_hours"] == {"start": "22:00"}
    assert result["channels"] == latest["channels"]
    assert result["router"] == latest["router"]
    assert result["ollama"] == {"model": "new"}
    assert OPTIONS_CONTROL_UPDATES not in result


def test_discovered_channel_edits_do_not_copy_provider_definitions() -> None:
    config = HeraldConfig.from_raw(channel_config()).to_dict()
    displayed = options_form_values(config)
    result = edited_options({}, displayed, {**displayed, "channel_enabled__phone": False}, options_field_bindings(config))
    assert result["channels"] == {"phone": {"enabled": False}}
    assert result[OPTIONS_CONTROL_UPDATES]["channel_enabled:phone"]["value"] is False


def test_dormant_controls_keep_values_and_consumed_revisions() -> None:
    state = RuntimeState(current_day="2026-09-30", control_values={"channel_enabled:temporarily_absent": False}, control_metadata={"channel_enabled:temporarily_absent": {"source": "runtime", "option_revision": "old"}})
    controls, _, state, _ = make_controls(data=channel_config(), state=state)
    controls.ensure_defaults()
    assert state.control_values["channel_enabled:temporarily_absent"] is False
    assert state.control_metadata["channel_enabled:temporarily_absent"]["option_revision"] == "old"


@pytest.mark.asyncio
async def test_offline_options_use_restored_store_and_pending_edits_without_writing(monkeypatch) -> None:
    stored = {"control_values": {"channel_min_level:phone": "warning"}, "control_metadata": {"channel_min_level:phone": {"source": "runtime", "option_revision": "old"}}}
    store = SimpleNamespace(async_load=AsyncMock(return_value=deepcopy(stored)), async_save=AsyncMock())
    monkeypatch.setattr("custom_components.herald.effective_config.Store", lambda *args: store)
    entry = SimpleNamespace(entry_id="test", data=channel_config(), options={OPTIONS_CONTROL_UPDATES: {"channel_min_level:phone": {"revision": "new", "value": "notice"}}})
    result = await async_options_config(SimpleNamespace(data={}), entry)
    assert result["channels"]["phone"]["min_level"] == "notice"
    store.async_save.assert_not_called()
    assert stored["control_values"]["channel_min_level:phone"] == "warning"


def test_deleted_inherited_option_does_not_reappear_from_an_initial_snapshot() -> None:
    controls, config, _, layers = make_controls(data=channel_config(), options={"channels": {"phone": {"min_level": "security"}}})
    controls.ensure_defaults()
    assert config.channels["phone"].min_level == "security"
    layers["options"] = {}
    layers["entry"]["channels"]["phone"].pop("min_level")
    controls.ensure_defaults()
    setting = controls.effective_settings()["channel_min_level:phone"]
    assert setting["value"] == "info"
    assert setting["inherited"] == "info"
    assert setting["source"] == "default"


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["yaml", "entry", "options", "default"])
async def test_offline_options_follow_inherited_changes_without_replaying_seeded_values(monkeypatch, source) -> None:
    stored = {"control_values": {"channel_min_level:phone": "info"}, "control_metadata": {"channel_min_level:phone": {"source": source}}}
    monkeypatch.setattr("custom_components.herald.effective_config.Store", lambda *args: SimpleNamespace(async_load=AsyncMock(return_value=stored)))
    data = channel_config()
    data["channels"]["phone"]["min_level"] = "warning"
    entry = SimpleNamespace(entry_id="test", data=data, options={})
    result = await async_options_config(SimpleNamespace(data={}), entry)
    assert result["channels"]["phone"]["min_level"] == "warning"


@pytest.mark.asyncio
async def test_offline_options_do_not_resurrect_dormant_definitions(monkeypatch) -> None:
    stored = {"control_values": {"flow_enabled:retired_plugin": False, "channel_min_level:retired_phone": "warning"}}
    monkeypatch.setattr("custom_components.herald.effective_config.Store", lambda *args: SimpleNamespace(async_load=AsyncMock(return_value=stored)))
    entry = SimpleNamespace(entry_id="test", data=channel_config(), options={})
    result = await async_options_config(SimpleNamespace(data={}), entry)
    assert "retired_plugin" not in result["flows"]
    assert "retired_phone" not in result["channels"]
    assert options_form_values(result)
