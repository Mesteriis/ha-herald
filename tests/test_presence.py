"""Tests for Herald presence resolution."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.herald.controls import HeraldControlManager, room_presence_control_key
from custom_components.herald.models import HeraldConfig, NotificationContext
from custom_components.herald.policy_rules import apply_rule
from custom_components.herald.presence import PresenceResolver
from custom_components.herald.request import HeraldRequest


class _FakeStates:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def get(self, entity_id: str):
        state = self._mapping.get(entity_id)
        if state is None:
            return None
        return SimpleNamespace(state=state, entity_id=entity_id, attributes={})

    def async_all(self, domain: str | None = None):
        entities = []
        for entity_id, state in self._mapping.items():
            if domain is not None and not entity_id.startswith(f"{domain}."):
                continue
            entities.append(SimpleNamespace(state=state, entity_id=entity_id, attributes={}))
        return entities


class _FakeHass:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.states = _FakeStates(mapping)


class _FakeCharacters:
    def list_character_keys(self) -> list[str]:
        return ["hestia", "domovoy"]

    def get(self, key: str | None):
        return SimpleNamespace(key="hestia")


@pytest.mark.parametrize("sensor_state", [None, "unknown", "unavailable", "on", "off"])
@pytest.mark.parametrize("person_state", ["home", "not_home"])
@pytest.mark.asyncio
async def test_nobody_home_requires_ready_sensor_or_falls_back_to_people(sensor_state, person_state) -> None:
    mapping = {"person.alice": person_state}
    if sensor_state is not None:
        mapping["binary_sensor.nobody_home"] = sensor_state
    resolver = PresenceResolver(_FakeHass(mapping), HeraldConfig())
    snapshot = await resolver.async_resolve_from_request(HeraldRequest(event="test", message="Test"))

    expected_nobody = sensor_state == "on" if sensor_state in {"on", "off"} else person_state != "home"
    assert snapshot.people_home == (["person.alice"] if person_state == "home" else [])
    assert snapshot.nobody_home is expected_nobody
    assert snapshot.absence_confirmed is (sensor_state == "on" and person_state != "home")
    assert snapshot.home_mode == ("away" if expected_nobody else "home")
    context = NotificationContext(
        flow="system_events", title="Test", message="Test", level="info", source="test",
        timestamp="2026-09-30T12:00:00+00:00", force=True,
    )
    assert apply_rule(context, {"presence": "someone_home"}, snapshot) == (
        "policy_someone_home" if expected_nobody else None
    )
    assert apply_rule(context, {"presence": "nobody_home"}, snapshot) == (
        None if expected_nobody else "policy_nobody_home"
    )


def test_occupied_room_routing_does_not_count_active_tv_as_person_present() -> None:
    config = HeraldConfig.from_raw({"presence": {"occupied_room_routing": True}})
    resolver = PresenceResolver(_FakeHass({"person.alice": "home"}), config)
    resolver._active_tv_rooms = lambda: ["living_room"]
    assert resolver.snapshot().occupied_rooms == []


def test_unknown_person_does_not_confirm_empty_home() -> None:
    resolver = PresenceResolver(
        _FakeHass({"person.alice": "unknown", "binary_sensor.nobody_home": "on"}),
        HeraldConfig(),
    )
    assert resolver.snapshot().nobody_home is True
    assert resolver.snapshot().absence_confirmed is False


@pytest.mark.asyncio
async def test_presence_falls_back_to_home_when_home_mode_not_ready() -> None:
    hass = _FakeHass(
        {
            "person.aleksandr_meshcheriakov": "home",
            "binary_sensor.room_gostinaia_occupied": "on",
        }
    )
    resolver = PresenceResolver(hass, HeraldConfig())

    snapshot = await resolver.async_resolve(
        NotificationContext(
            flow="system_events",
            event="smoke",
            title="smoke",
            message="smoke",
            level="info",
            source="test",
            timestamp="2026-03-08T00:00:00+00:00",
        )
    )

    assert snapshot.home_mode == "home"
    assert "living_room" in snapshot.occupied_rooms


@pytest.mark.asyncio
async def test_presence_uses_room_hint_from_request_context() -> None:
    hass = _FakeHass(
        {
            "person.aleksandr_meshcheriakov": "home",
        }
    )
    resolver = PresenceResolver(hass, HeraldConfig())

    snapshot = await resolver.async_resolve_from_request(
        HeraldRequest(
            event="smoke",
            message="smoke",
            context={"room_hint": "living_room"},
        )
    )

    assert snapshot.primary_room == "living_room"
    assert snapshot.home_mode == "home"


def test_room_sensors_canonicalize_discovered_room_aliases() -> None:
    hass = _FakeHass(
        {
            "binary_sensor.room_gostinaia_occupied": "on",
            "binary_sensor.room_spalnia_occupied": "on",
            "binary_sensor.room_kukhnia_occupied": "off",
            "binary_sensor.room_vannaia_occupied": "on",
            "binary_sensor.room_kabinet_occupied": "on",
        }
    )
    resolver = PresenceResolver(hass, HeraldConfig())

    room_sensors = resolver.room_sensors()

    assert room_sensors["living_room"] == "binary_sensor.room_gostinaia_occupied"
    assert room_sensors["bedroom"] == "binary_sensor.room_spalnia_occupied"
    assert room_sensors["kitchen"] == "binary_sensor.room_kukhnia_occupied"
    assert room_sensors["bathroom"] == "binary_sensor.room_vannaia_occupied"
    assert room_sensors["office"] == "binary_sensor.room_kabinet_occupied"
    assert "gostinaia" not in room_sensors
    assert "spalnia" not in room_sensors
    assert "kukhnia" not in room_sensors
    assert "vannaia" not in room_sensors
    assert "kabinet" not in room_sensors


@pytest.mark.asyncio
async def test_presence_uses_herald_room_switch_fallback_when_binary_sensor_missing() -> None:
    hass = _FakeHass({"person.aleksandr_meshcheriakov": "home"})
    resolver = PresenceResolver(hass, HeraldConfig())
    state = SimpleNamespace(
        current_day="2026-03-08",
        notifications_today=0,
        queue_size=0,
        last_notification={},
        recent_notifications=[],
        flow_overrides={},
        snoozed_flows={},
        acknowledged_notifications={},
        dedup_cache={},
        last_flow_delivery={},
        traces=[],
        control_values={},
        control_metadata={},
    )
    controls = HeraldControlManager(hass, HeraldConfig(), resolver, _FakeCharacters(), lambda: state)
    resolver.attach_controls(controls)
    controls.ensure_defaults()
    controls.set_value(room_presence_control_key("living_room"), True)

    snapshot = await resolver.async_resolve(
        NotificationContext(
            flow="system_events",
            event="smoke",
            title="smoke",
            message="smoke",
            level="info",
            source="test",
            timestamp="2026-03-08T00:00:00+00:00",
        )
    )

    assert "living_room" in snapshot.occupied_rooms


@pytest.mark.asyncio
async def test_tv_registry_mapping_loads_in_executor_and_is_cached(monkeypatch, tmp_path) -> None:
    import asyncio
    import threading

    from custom_components.herald import presence as presence_module

    hass = _FakeHass({"media_player.screen_tv": "playing"})
    hass.config = SimpleNamespace(path=lambda name: str(tmp_path / name))
    loop_thread = threading.get_ident()
    loads: list[tuple[object, object]] = []
    room = "kitchen"

    def load_rooms(entity_path, device_path):
        assert threading.get_ident() != loop_thread
        loads.append((entity_path, device_path))
        return {"media_player.screen_tv": room}

    async def executor_job(func, *args):
        return await asyncio.to_thread(func, *args)

    hass.async_add_executor_job = executor_job
    monkeypatch.setattr(presence_module, "_load_media_player_rooms", load_rooms)
    resolver = PresenceResolver(hass, HeraldConfig())
    request = HeraldRequest(event="smoke", message="smoke")

    first, second = await asyncio.gather(
        resolver.async_resolve_from_request(request),
        resolver.async_resolve_from_request(request),
    )

    assert first.occupied_rooms == ["kitchen"]
    assert second.occupied_rooms == ["kitchen"]
    assert len(loads) == 1
    assert loads[0] == (
        tmp_path / ".storage/core.entity_registry",
        tmp_path / ".storage/core.device_registry",
    )

    room = "office"
    resolver._media_player_rooms_refresh_at = 0
    refreshed = await resolver.async_resolve_from_request(request)
    assert refreshed.occupied_rooms == ["office"]
    assert len(loads) == 2

    # Device activity is never cached with the registry metadata.
    hass.states._mapping["media_player.screen_tv"] = "off"
    inactive = await resolver.async_resolve_from_request(request)
    assert inactive.occupied_rooms == []
    assert len(loads) == 2


@pytest.mark.parametrize("local_hour, expected", [(22, True), (23, True), (1, True), (8, True), (12, False), (21, False)])
def test_quiet_hours_use_home_assistant_local_time(monkeypatch, local_hour, expected) -> None:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from custom_components.herald import presence as presence_module

    local_now = datetime(2026, 9, 30, local_hour, tzinfo=ZoneInfo("Europe/Madrid"))
    monkeypatch.setattr(presence_module.dt_util, "now", lambda: local_now)
    config = HeraldConfig()
    config.quiet_hours.start = "22:00"
    config.quiet_hours.end = "08:00"

    assert PresenceResolver(_FakeHass({}), config).in_quiet_hours() is expected


@pytest.mark.parametrize("initial_state", [None, "unknown", "unavailable"])
@pytest.mark.parametrize("entrypoint", ["context", "request"])
@pytest.mark.asyncio
async def test_unready_room_sensor_never_delays_resolution_and_is_picked_up_later(monkeypatch, initial_state, entrypoint) -> None:
    from unittest.mock import AsyncMock

    from custom_components.herald import presence as presence_module
    from custom_components.herald.const import CONF_ROOM_SENSORS

    sensor = "binary_sensor.room_selected_presence"
    hass = _FakeHass({} if initial_state is None else {sensor: initial_state})
    config = HeraldConfig()
    config.presence[CONF_ROOM_SENSORS] = {"living_room": sensor}
    resolver = PresenceResolver(hass, config)
    sleep = AsyncMock(side_effect=AssertionError("Presence resolution must not wait for room sensors"))
    monkeypatch.setattr(presence_module.asyncio, "sleep", sleep)

    async def resolve():
        if entrypoint == "request":
            return await resolver.async_resolve_from_request(HeraldRequest(event="alarm", message="Alarm", level="critical"))
        return await resolver.async_resolve(NotificationContext(
            flow="system_events", event="alarm", title="Alarm", message="Alarm",
            level="critical", source="test", timestamp="2026-09-30T12:00:00+00:00",
        ))

    initial = await resolve()
    assert initial.occupied_rooms == []
    assert initial.primary_room is None
    hass.states._mapping[sensor] = "on"
    ready = await resolve()
    assert ready.occupied_rooms == ["living_room"]
    assert ready.primary_room == "living_room"
    sleep.assert_not_awaited()
