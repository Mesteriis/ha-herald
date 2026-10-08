"""Options sections preserve effective defaults and isolate each submitted edit."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from test_effective_config import channel_config, form_defaults, make_controls

from custom_components.herald import config_flow
from custom_components.herald.const import DATA_COORDINATORS, DOMAIN
from custom_components.herald.effective_config import OPTIONS_CONTROL_UPDATES


@pytest.fixture
def options(monkeypatch):
    controls, config, state, layers = make_controls(data=channel_config())
    controls.ensure_defaults()
    entry = SimpleNamespace(entry_id="test", data=channel_config(), options={"router": {"recent_limit": 11}})
    flow = config_flow.HeraldOptionsFlow(entry)
    flow.hass = SimpleNamespace(data={DOMAIN: {DATA_COORDINATORS: {entry.entry_id: SimpleNamespace(config=config, controls=controls)}}})
    discovery = AsyncMock(return_value={})
    monkeypatch.setattr(config_flow, "async_discover_runtime_channels", discovery)
    return SimpleNamespace(flow=flow, entry=entry, config=config, controls=controls, state=state, layers=layers, discovery=discovery)


async def open_section(options, section):
    if section == "channel":
        return await options.flow.async_step_channel_select({"channel": "phone"})
    if section == "flow":
        return await options.flow.async_step_flow_select({"flow": "system_events"})
    return await getattr(options.flow, f"async_step_{section}")()


@pytest.mark.asyncio
async def test_menu_does_not_load_settings_discover_or_write(options, monkeypatch):
    config_reader = AsyncMock(side_effect=AssertionError("Menu must not load settings"))
    monkeypatch.setattr(config_flow, "async_options_config", config_reader)
    before = deepcopy(options.entry.options)
    result = await options.flow.async_step_init()
    assert result["type"] == "menu"
    assert result["step_id"] == "init"
    assert set(result["menu_options"]) == {"quiet_hours", "ai", "maintenance", "channel_select", "flow_select"}
    config_reader.assert_not_awaited()
    options.discovery.assert_not_awaited()
    assert options.entry.options == before


@pytest.mark.asyncio
@pytest.mark.parametrize(("section", "fields"), [
    ("quiet_hours", {"start", "end"}),
    ("ai", {"provider", "host", "model", "api_key"}),
    ("maintenance", {"maintenance_mode_entity"}),
    ("channel", {"enabled", "min_level"}),
    ("flow", {"summary_personality", "cooldown_seconds", "dedup_window_seconds"}),
])
async def test_section_has_only_its_fields_and_opening_is_read_only(options, section, fields):
    before_options = deepcopy(options.entry.options)
    before_state = options.state.to_dict()
    form = await open_section(options, section)
    assert form["type"] == "form"
    assert form["step_id"] == section
    assert set(form_defaults(form)) == fields
    assert options.entry.options == before_options
    assert options.state.to_dict() == before_state
    if section != "channel":
        options.discovery.assert_not_awaited()


@pytest.mark.asyncio
async def test_ai_password_is_never_prefilled_and_blank_preserves_existing_key(options):
    options.config.ollama.update({"provider": "openai", "host": "https://ai.sh-inc.ru", "api_key": "synthetic-secret"})
    options.entry.options = {"ollama": {"api_key": "synthetic-secret"}}
    form = await options.flow.async_step_ai()
    values = form_defaults(form)
    assert values["api_key"] == ""
    assert "synthetic-secret" not in str(form)
    result = await options.flow.async_step_ai(values)
    assert result["data"]["ollama"]["api_key"] == "synthetic-secret"
    assert result["data"]["ollama"].get("enabled") is None


@pytest.mark.asyncio
async def test_ai_provider_edit_requires_https_and_keeps_other_options(options):
    values = form_defaults(await options.flow.async_step_ai())
    values.update(provider="openai", host="http://ai.sh-inc.ru", model="synthetic-model", api_key="synthetic-secret")
    rejected = await options.flow.async_step_ai(values)
    assert rejected["errors"] == {"host": "invalid_host"}
    assert "synthetic-secret" not in str(rejected)
    assert options.entry.options == {"router": {"recent_limit": 11}}
    values["host"] = "https://ai.sh-inc.ru"
    result = await options.flow.async_step_ai(values)
    assert result["data"] == {"router": {"recent_limit": 11}, "ollama": {
        "provider": "openai", "host": "https://ai.sh-inc.ru", "model": "synthetic-model", "api_key": "synthetic-secret",
    }}


@pytest.mark.asyncio
@pytest.mark.parametrize(("kind", "name"), [("channel", "phone"), ("flow", "system_events")])
async def test_picker_rejects_unknown_and_forged_selections_without_writing(options, kind, name):
    step = getattr(options.flow, f"async_step_{kind}_select")
    form = await step()
    assert form["type"] == "form"
    assert {marker.schema for marker in form["data_schema"].schema} == {kind}
    before = deepcopy(options.entry.options)
    for submitted in ({kind: "missing"}, {kind: name, "enabled": False}, {kind: []}):
        result = await step(submitted)
        assert result["type"] == "form"
        assert result["errors"] == {"base": "invalid_selection"}
        assert options.entry.options == before


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["channel", "flow"])
async def test_empty_catalog_and_unselected_editor_abort_without_writing(options, kind):
    before = deepcopy(options.entry.options)
    result = await getattr(options.flow, f"async_step_{kind}")()
    assert result == {"type": "abort", "reason": f"{kind}_unavailable"}
    getattr(options.config, f"{kind}s").clear()
    result = await getattr(options.flow, f"async_step_{kind}_select")()
    assert result == {"type": "abort", "reason": f"no_{kind}s"}
    assert options.entry.options == before


@pytest.mark.asyncio
@pytest.mark.parametrize(("kind", "name"), [("channel", "phone"), ("flow", "system_events")])
async def test_target_removed_after_opening_cannot_be_resurrected_by_submit(options, kind, name):
    submitted = form_defaults(await open_section(options, kind))
    getattr(options.config, f"{kind}s").pop(name)
    before = deepcopy(options.entry.options)
    result = await getattr(options.flow, f"async_step_{kind}")(submitted)
    assert result == {"type": "abort", "reason": f"{kind}_unavailable"}
    assert options.entry.options == before


@pytest.mark.asyncio
@pytest.mark.parametrize(("section", "extra"), [
    ("quiet_hours", {"model": "forged"}),
    ("ai", {"enabled": True}),
    ("maintenance", {"start": "00:00"}),
    ("channel", {"channel_enabled__other": False}),
    ("flow", {"channel_min_level__phone": "debug"}),
])
async def test_cross_section_input_is_rejected_without_write(options, section, extra):
    submitted = {**form_defaults(await open_section(options, section)), **extra}
    before = deepcopy(options.entry.options)
    result = await getattr(options.flow, f"async_step_{section}")(submitted)
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_value"}
    assert options.entry.options == before


@pytest.mark.asyncio
async def test_defaults_are_captured_on_section_entry_and_refreshed_on_reentry(options):
    await options.flow.async_step_init()
    options.controls.set_value("channel_min_level:phone", "warning")
    first = await open_section(options, "channel")
    assert form_defaults(first)["min_level"] == "warning"
    await options.flow.async_step_init()
    options.controls.set_value("channel_min_level:phone", "security")
    second = await open_section(options, "channel")
    assert form_defaults(second)["min_level"] == "security"
    assert (await options.flow.async_step_channel(form_defaults(second)))["data"] == options.entry.options


@pytest.mark.asyncio
async def test_invalid_retry_retains_user_values_and_original_comparison_snapshot(options):
    form = await open_section(options, "channel")
    submitted = {**form_defaults(form), "min_level": "invalid"}
    retry = await options.flow.async_step_channel(submitted)
    assert retry["errors"] == {"min_level": "invalid_value"}
    assert form_defaults(retry) == submitted
    options.controls.set_value("channel_enabled:phone", False)
    options.controls.set_value("channel_min_level:phone", "critical")
    options.entry.options = {"router": {"recent_limit": 29}, "flows": {"system_events": {"enabled": False}}}
    result = await options.flow.async_step_channel({**submitted, "min_level": "notice"})
    assert result["data"]["channels"] == {"phone": {"min_level": "notice"}}
    assert result["data"]["router"] == {"recent_limit": 29}
    assert result["data"]["flows"] == {"system_events": {"enabled": False}}
    assert set(result["data"][OPTIONS_CONTROL_UPDATES]) == {"channel_min_level:phone"}
    options.layers["options"] = result["data"]
    assert options.controls.apply_option_updates(result["data"])
    options.controls.ensure_defaults()
    assert options.controls.value("channel_enabled:phone") is False
    assert options.controls.value("channel_min_level:phone") == "notice"


@pytest.mark.asyncio
async def test_quiet_hours_retry_preserves_input_and_latest_unrelated_options(options):
    await options.flow.async_step_quiet_hours()
    retry = await options.flow.async_step_quiet_hours({"start": "01:30", "end": "24:00"})
    assert retry["errors"] == {"end": "invalid_time"}
    assert form_defaults(retry) == {"start": "01:30", "end": "24:00"}
    options.entry.options = {"ollama": {"enabled": False, "model": "changed-elsewhere"}}
    result = await options.flow.async_step_quiet_hours({"start": "01:30", "end": "06:45"})
    assert result["data"] == {"ollama": {"enabled": False, "model": "changed-elsewhere"}, "quiet_hours": {"start": "01:30", "end": "06:45"}}


@pytest.mark.asyncio
async def test_maintenance_helper_edit_preserves_existing_legacy_threshold(options):
    options.entry.options = {"router": {"recent_limit": 11, "maintenance_min_level": "warning"}}
    await options.flow.async_step_maintenance()
    before = deepcopy(options.entry.options)
    result = await options.flow.async_step_maintenance({"maintenance_mode_entity": "input_boolean.synthetic_maintenance"})
    assert result["data"] == {"router": {"recent_limit": 11, "maintenance_min_level": "warning", "maintenance_mode_entity": "input_boolean.synthetic_maintenance"}}
    assert OPTIONS_CONTROL_UPDATES not in result["data"]
    assert options.entry.options == before


def set_optional_value(options, section, value):
    if section == "maintenance":
        options.config.router["maintenance_mode_entity"] = value
    else:
        options.config.flows["system_events"].summary_personality = value


@pytest.mark.asyncio
@pytest.mark.parametrize(("section", "field", "original", "expected"), [
    ("maintenance", "maintenance_mode_entity", "input_boolean.synthetic_maintenance", ""),
    ("flow", "summary_personality", "retired_custom_persona", None),
])
async def test_optional_suggested_value_roundtrips_and_native_omission_clears(options, section, field, original, expected):
    set_optional_value(options, section, original)
    form = await open_section(options, section)
    submitted = form_defaults(form)
    assert submitted[field] == original
    step = getattr(options.flow, f"async_step_{section}")
    assert (await step(submitted))["data"] == options.entry.options
    form = await open_section(options, section)
    submitted = form_defaults(form)
    # HA drops empty optional strings before POST; absence must mean clear.
    submitted.pop(field)
    result = await step(submitted)
    expected_patch = {"router": {"maintenance_mode_entity": expected}} if section == "maintenance" else {"flows": {"system_events": {"summary_personality": expected}}}
    if section == "maintenance":
        expected_patch["router"]["recent_limit"] = 11
    else:
        expected_patch["router"] = {"recent_limit": 11}
    assert result["data"] == expected_patch
    assert OPTIONS_CONTROL_UPDATES not in result["data"]


@pytest.mark.asyncio
@pytest.mark.parametrize(("section", "field", "original"), [
    ("maintenance", "maintenance_mode_entity", "input_boolean.synthetic_maintenance"),
    ("flow", "summary_personality", "retired_custom_persona"),
])
async def test_optional_blank_retry_stays_blank_and_keeps_original_edit_baseline(options, section, field, original):
    set_optional_value(options, section, original)
    submitted = {**form_defaults(await open_section(options, section)), field: "", "forged": True}
    submitted.pop(field)  # The native form omits the user's cleared string.
    step = getattr(options.flow, f"async_step_{section}")
    retry = await step(submitted)
    assert retry["errors"] == {"base": "invalid_value"}
    assert form_defaults(retry)[field] == ""
    # A concurrent change must not replace the user's displayed clear intent.
    set_optional_value(options, section, f"{original}_changed")
    submitted = form_defaults(retry)
    submitted.pop(field)
    result = await step(submitted)
    if section == "maintenance":
        assert result["data"]["router"][field] == ""
    else:
        assert result["data"]["flows"]["system_events"][field] is None


@pytest.mark.asyncio
async def test_flow_clear_personality_and_full_duration_produce_only_selected_patch(options):
    options.config.flows["system_events"].summary_personality = "retired_custom_persona"
    options.controls.set_value("flow_dedup_window:system_events", 120)
    form = await open_section(options, "flow")
    submitted = form_defaults(form)
    assert submitted["summary_personality"] == "retired_custom_persona"
    # A missing persona definition cannot force an unrelated edit/reset.
    assert (await options.flow.async_step_flow(submitted))["data"] == options.entry.options
    await open_section(options, "flow")
    submitted.update(summary_personality="", cooldown_seconds="86400", dedup_window_seconds="0")
    result = await options.flow.async_step_flow(submitted)
    assert result["data"]["flows"] == {"system_events": {"summary_personality": None, "cooldown_seconds": 86400, "dedup_window_seconds": 0}}
    updates = result["data"][OPTIONS_CONTROL_UPDATES]
    assert set(updates) == {"flow_cooldown:system_events", "flow_dedup_window:system_events"}
    assert updates["flow_cooldown:system_events"]["value"] == 86400
    assert updates["flow_dedup_window:system_events"]["value"] == 0
    options.discovery.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(("field", "value"), [
    ("cooldown_seconds", -1),
    ("cooldown_seconds", 86401),
    ("dedup_window_seconds", "not-a-number"),
    ("summary_personality", "unknown-persona"),
])
async def test_invalid_flow_field_is_retained_without_write(options, field, value):
    submitted = {**form_defaults(await open_section(options, "flow")), field: value}
    before = deepcopy(options.entry.options)
    result = await options.flow.async_step_flow(submitted)
    assert result["type"] == "form"
    assert result["errors"] == {field: "invalid_value"}
    assert form_defaults(result)[field] == value
    assert options.entry.options == before


@pytest.mark.asyncio
async def test_discovered_channel_edit_is_sparse_and_disappearance_aborts(options):
    options.config.channels.clear()
    options.discovery.return_value = {"temporary": {"type": "mobile_app", "service": "notify.mobile_app_temporary"}}
    form = await options.flow.async_step_channel_select({"channel": "temporary"})
    assert form_defaults(form) == {"enabled": True, "min_level": "info"}
    unchanged = await options.flow.async_step_channel(form_defaults(form))
    assert unchanged["data"] == options.entry.options
    form = await options.flow.async_step_channel_select({"channel": "temporary"})
    changed = {**form_defaults(form), "enabled": False}
    result = await options.flow.async_step_channel(changed)
    assert result["data"]["channels"] == {"temporary": {"enabled": False}}
    assert set(result["data"][OPTIONS_CONTROL_UPDATES]) == {"channel_enabled:temporary"}
    options.discovery.return_value = {}
    assert await options.flow.async_step_channel(changed) == {"type": "abort", "reason": "channel_unavailable"}


@pytest.mark.asyncio
async def test_selecting_another_channel_does_not_reuse_previous_baseline(options):
    options.discovery.return_value = {"second": {"type": "mobile_app", "enabled": False, "min_level": "security"}}
    await options.flow.async_step_channel_select({"channel": "phone"})
    second = await options.flow.async_step_channel_select({"channel": "second"})
    assert form_defaults(second) == {"enabled": False, "min_level": "security"}
    result = await options.flow.async_step_channel({"enabled": True, "min_level": "security"})
    assert result["data"]["channels"] == {"second": {"enabled": True}}
    assert set(result["data"][OPTIONS_CONTROL_UPDATES]) == {"channel_enabled:second"}
