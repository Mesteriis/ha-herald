"""Tests for live Herald topology rematerialization."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.herald.binary_sensor import async_setup_entry as async_setup_binary_sensor_entry
from custom_components.herald.button import async_setup_entry as async_setup_button_entry
from custom_components.herald.const import DATA_COORDINATORS, DOMAIN
from custom_components.herald.controls import HeraldControlSpec
from custom_components.herald.select import HeraldSelectEntity
from custom_components.herald.switch import async_setup_entry as async_setup_switch_entry


class _FakeCoordinator:
    def __init__(self, controls, presence=None) -> None:
        self.controls = controls
        self.presence = presence or SimpleNamespace(room_sensors=lambda: {})
        self.data = {}


class _FakeControls:
    def __init__(self, specs_by_platform: dict[str, list[HeraldControlSpec]]) -> None:
        self._specs_by_platform = specs_by_platform

    def build_specs_for_platform(self, platform: str) -> list[HeraldControlSpec]:
        return list(self._specs_by_platform.get(platform, []))

    def spec(self, key: str) -> HeraldControlSpec | None:
        for specs in self._specs_by_platform.values():
            for spec in specs:
                if spec.key == key:
                    return spec
        return None

    def value(self, key: str, default=None):
        spec = self.spec(key)
        return spec.default if spec is not None else default


class _FakeEntry:
    def __init__(self, entry_id: str = "entry-1") -> None:
        self.entry_id = entry_id
        self.unloads = []

    def async_on_unload(self, callback) -> None:
        self.unloads.append(callback)


class _FakeHass:
    def __init__(self, coordinator) -> None:
        self.data = {
            DOMAIN: {
                DATA_COORDINATORS: {
                    "entry-1": coordinator,
                }
            }
        }


@pytest.mark.asyncio
async def test_switch_platform_adds_new_entities_on_topology_signal(monkeypatch) -> None:
    callbacks = []
    specs = {
        "switch": [
            HeraldControlSpec(
                key="flow_enabled:system_events",
                platform="switch",
                object_id="herald_flow_system_events_enabled",
                name="Herald Flow System Events Enabled",
                group="flows",
                default=True,
            )
        ]
    }
    controls = _FakeControls(specs)
    coordinator = _FakeCoordinator(controls)
    hass = _FakeHass(coordinator)
    entry = _FakeEntry()
    added = []

    monkeypatch.setattr(
        "custom_components.herald.switch.async_dispatcher_connect",
        lambda hass, signal, callback: callbacks.append(callback) or (lambda: None),
    )

    await async_setup_switch_entry(hass, entry, lambda entities: added.extend(list(entities)))
    assert len(added) == 1

    specs["switch"].append(
        HeraldControlSpec(
            key="channel_enabled:tv_auto",
            platform="switch",
            object_id="herald_channel_tv_auto_enabled",
            name="Herald Channel Tv Auto Enabled",
            group="channels",
            default=True,
        )
    )
    callbacks[0]()

    assert len(added) == 2
    assert added[1].entity_id == "switch.herald_channel_tv_auto_enabled"


@pytest.mark.asyncio
async def test_binary_sensor_platform_adds_new_rooms_on_topology_signal(monkeypatch) -> None:
    callbacks = []
    room_map = {"living_room": "binary_sensor.room_gostinaia_occupied"}
    coordinator = _FakeCoordinator(
        _FakeControls({}),
        presence=SimpleNamespace(room_sensors=lambda: dict(room_map)),
    )
    hass = _FakeHass(coordinator)
    entry = _FakeEntry()
    added = []

    monkeypatch.setattr(
        "custom_components.herald.binary_sensor.async_dispatcher_connect",
        lambda hass, signal, callback: callbacks.append(callback) or (lambda: None),
    )

    await async_setup_binary_sensor_entry(hass, entry, lambda entities: added.extend(list(entities)))
    assert len(added) == 1

    room_map["office"] = "binary_sensor.room_kabinet_occupied"
    callbacks[0]()

    assert len(added) == 2
    assert added[1].entity_id == "binary_sensor.herald_room_office_presence"


@pytest.mark.asyncio
async def test_button_platform_adds_new_entities_on_topology_signal(monkeypatch) -> None:
    callbacks = []
    specs = {
        "button": [
            HeraldControlSpec(
                key="test_level:warning",
                platform="button",
                object_id="herald_test_level_warning",
                name="Herald Test Level Warning",
                group="tests",
                default=0,
            )
        ]
    }
    controls = _FakeControls(specs)
    coordinator = _FakeCoordinator(controls)
    hass = _FakeHass(coordinator)
    entry = _FakeEntry()
    added = []

    monkeypatch.setattr(
        "custom_components.herald.button.async_dispatcher_connect",
        lambda hass, signal, callback: callbacks.append(callback) or (lambda: None),
    )

    await async_setup_button_entry(hass, entry, lambda entities: added.extend(list(entities)))
    assert len(added) == 1

    specs["button"].append(
        HeraldControlSpec(
            key="test_channel:tv_auto",
            platform="button",
            object_id="herald_test_channel_tv_auto",
            name="Herald Test Channel Tv Auto",
            group="tests",
            default=0,
        )
    )
    callbacks[0]()

    assert len(added) == 2
    assert added[1].entity_id == "button.herald_test_channel_tv_auto"


def test_select_entity_uses_live_options_for_new_characters() -> None:
    specs = {
        "select": [
            HeraldControlSpec(
                key="user_character:aleksandr",
                platform="select",
                object_id="herald_user_aleksandr_character",
                name="Herald User Aleksandr Character",
                group="users",
                default="hestia",
                options=("hestia", "domovoy"),
            )
        ]
    }
    controls = _FakeControls(specs)
    coordinator = _FakeCoordinator(controls)
    entity = HeraldSelectEntity(coordinator, _FakeEntry(), specs["select"][0])

    assert entity.options == ["hestia", "domovoy"]

    specs["select"][0] = HeraldControlSpec(
        key="user_character:aleksandr",
        platform="select",
        object_id="herald_user_aleksandr_character",
        name="Herald User Aleksandr Character",
        group="users",
        default="hestia",
        options=("hestia", "domovoy", "nightwatch"),
    )

    assert entity.options == ["hestia", "domovoy", "nightwatch"]
