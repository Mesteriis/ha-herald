"""Registry identity, renames, and unavailable Herald control entities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.herald.const import DOMAIN
from custom_components.herald.control_entities import resolve_control_entities
from custom_components.herald.controls import HeraldControlSpec

ENTRY_ID = "synthetic_herald_entry"


def spec(key="channel_enabled:phone", platform="switch", object_id="herald_channel_phone_enabled"):
    return HeraldControlSpec(key=key, platform=platform, object_id=object_id, name="Control", group="channel", default=False)


def entry(control, entity_id=None, *, config_entry_id=ENTRY_ID, platform=DOMAIN, unique_id=None, disabled_by=None):
    return SimpleNamespace(
        entity_id=entity_id or control.entity_id,
        domain=control.platform,
        platform=platform,
        unique_id=unique_id or f"{ENTRY_ID}_{control.object_id}",
        config_entry_id=config_entry_id,
        disabled_by=disabled_by,
    )


class Registry:
    """Only the real HA registry's two read APIs used by the helper."""

    def __init__(self, entries=()):
        self.entities = {item.entity_id: item for item in entries}

    def async_get_entity_id(self, domain, platform, unique_id):
        return next((item.entity_id for item in self.entities.values()
                     if (item.domain, item.platform, item.unique_id) == (domain, platform, unique_id)), None)

    def async_get(self, entity_id):
        return self.entities.get(entity_id)


def environment(controls, entries=(), states=None):
    state_reader = Mock(side_effect=lambda entity_id: (states or {}).get(entity_id))
    hass = SimpleNamespace(data={"entity_registry": Registry(entries)}, states=SimpleNamespace(get=state_reader))
    manager = SimpleNamespace(build_specs=lambda: controls)
    return hass, manager


@pytest.mark.parametrize("control", [
    spec(),
    spec("channel_min_level:phone", "select", "herald_channel_phone_min_level"),
    spec("flow_cooldown:system_events", "number", "herald_flow_system_events_cooldown"),
    spec("mute_all", "switch", "herald_mute_all"),
])
def test_renamed_controls_resolve_actual_registry_ids(control):
    registered = entry(control, f"{control.platform}.renamed_by_user")
    hass, controls = environment([control], [registered])
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {control.key: registered.entity_id}
    hass.states.get.assert_not_called()


@pytest.mark.parametrize("state", [None, "unavailable", "unknown", "on"])
@pytest.mark.parametrize("disabled_by", [None, "user"])
def test_unavailable_or_disabled_registry_entity_keeps_its_identity(state, disabled_by):
    control = spec()
    registered = entry(control, "switch.actual_control", disabled_by=disabled_by)
    hass, controls = environment([control], [registered], {registered.entity_id: state})
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {control.key: registered.entity_id}
    hass.states.get.assert_not_called()


def test_unregistered_state_cannot_impersonate_default_control():
    control = spec()
    hass, controls = environment([control], states={control.entity_id: "on"})
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {}
    hass.states.get.assert_not_called()


def test_default_entity_id_collision_with_another_integration_is_not_adopted():
    control = spec()
    foreign = entry(control, platform="template", config_entry_id="different_entry")
    hass, controls = environment([control], [foreign], {control.entity_id: "on"})
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {}


def test_renamed_herald_entity_wins_over_foreign_state_at_default_id():
    control = spec()
    actual = entry(control, "switch.user_chosen_name")
    foreign = entry(control, platform="mqtt", config_entry_id="different_entry")
    hass, controls = environment([control], [foreign, actual], {control.entity_id: "on", actual.entity_id: "unavailable"})
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {control.key: actual.entity_id}


@pytest.mark.parametrize("config_entry_id", [None, "different_herald_entry"])
def test_unique_id_match_without_config_entry_ownership_is_rejected(config_entry_id):
    control = spec()
    hass, controls = environment([control], [entry(control, config_entry_id=config_entry_id)])
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {}


def test_deleted_control_is_not_resurrected_from_remaining_state():
    control = spec()
    registered = entry(control, "switch.old_name")
    hass, controls = environment([control], [registered], {registered.entity_id: "on"})
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {control.key: registered.entity_id}
    del hass.data["entity_registry"].entities[registered.entity_id]
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {}


def test_rename_is_observed_on_next_lookup_without_cached_default():
    control = spec()
    registered = entry(control)
    hass, controls = environment([control], [registered])
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {control.key: control.entity_id}
    registry = hass.data["entity_registry"]
    del registry.entities[registered.entity_id]
    registered.entity_id = "switch.new_name"
    registry.entities[registered.entity_id] = registered
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {control.key: "switch.new_name"}


def test_missing_registry_is_not_created_and_no_state_fallback_is_used(monkeypatch):
    control = spec()
    hass = SimpleNamespace(data={}, states=SimpleNamespace(get=Mock(return_value="on")))
    controls = SimpleNamespace(build_specs=Mock(return_value=[control]))
    get_registry = Mock(side_effect=AssertionError("must not create registry"))
    monkeypatch.setattr(er, "async_get", get_registry)
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {}
    assert hass.data == {}
    get_registry.assert_not_called()
    controls.build_specs.assert_not_called()
    hass.states.get.assert_not_called()


def test_buttons_are_not_exposed_as_configuration_controls():
    switch = spec()
    button = spec("test_channel:phone", "button", "herald_test_channel_phone")
    hass, controls = environment([switch, button], [entry(switch), entry(button)])
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {switch.key: switch.entity_id}


def test_constructed_but_unloaded_registry_has_no_resolvable_entities():
    registry = SimpleNamespace(async_get_entity_id=Mock(side_effect=AssertionError("registry is not loaded")))
    hass = SimpleNamespace(data={"entity_registry": registry})
    controls = SimpleNamespace(build_specs=Mock(return_value=[spec()]))
    assert resolve_control_entities(hass, ENTRY_ID, controls) == {}
    registry.async_get_entity_id.assert_not_called()
    controls.build_specs.assert_not_called()
