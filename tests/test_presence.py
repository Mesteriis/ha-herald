"""Tests for Herald presence resolution."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.herald.controls import HeraldControlManager, room_presence_control_key
from custom_components.herald.models import HeraldConfig, NotificationContext
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


@pytest.mark.asyncio
async def test_presence_falls_back_to_home_when_home_mode_not_ready() -> None:
    hass = _FakeHass(
        {
            "person.aleksandr_meshcheriakov": "home",
            "binary_sensor.room_gostinaia_occupied": "on",
        }
    )
    resolver = PresenceResolver(hass, HeraldConfig())
    resolver._room_entities_ready_once = True

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
    resolver._room_wait_exhausted = True

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
    )
    controls = HeraldControlManager(hass, HeraldConfig(), resolver, _FakeCharacters(), lambda: state)
    resolver.attach_controls(controls)
    controls.ensure_defaults()
    controls.set_value(room_presence_control_key("living_room"), True)
    resolver._room_wait_exhausted = True

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
