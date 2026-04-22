"""Tests for Herald runtime context enrichment."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.herald.context_builder import HeraldContextBuilder
from custom_components.herald.models import HeraldConfig
from custom_components.herald.presence import PresenceResolver
from custom_components.herald.request import HeraldRequest


class _FakeStates:
    def __init__(
        self,
        mapping: dict[str, str],
        attributes: dict[str, dict[str, object]] | None = None,
    ) -> None:
        self._mapping = mapping
        self._attributes = attributes or {}

    def get(self, entity_id: str):
        state = self._mapping.get(entity_id)
        if state is None:
            return None
        return SimpleNamespace(
            state=state,
            entity_id=entity_id,
            attributes=dict(self._attributes.get(entity_id, {})),
        )

    def async_all(self, domain: str | None = None):
        entities = []
        for entity_id, state in self._mapping.items():
            if domain is not None and not entity_id.startswith(f"{domain}."):
                continue
            entities.append(
                SimpleNamespace(
                    state=state,
                    entity_id=entity_id,
                    attributes=dict(self._attributes.get(entity_id, {})),
                )
            )
        return entities


class _FakeHass:
    def __init__(
        self,
        mapping: dict[str, str],
        attributes: dict[str, dict[str, object]] | None = None,
    ) -> None:
        self.states = _FakeStates(mapping, attributes)


class _FakeControls:
    def user_language(self, user_slug: str, *, default: str = "ru") -> str:
        return default

    def user_character(self, user_slug: str, *, default: str | None = None) -> str | None:
        return default or "domovoy"

    def user_silent(self, user_slug: str) -> bool:
        return False


@pytest.mark.asyncio
async def test_context_builder_uses_configured_room_entity_for_user_room() -> None:
    hass = _FakeHass(
        {
            "person.aleksandr_meshcheriakov": "home",
            "sensor.alex_room": "Гостиная",
        },
        {
            "person.aleksandr_meshcheriakov": {
                "friendly_name": "Aleksandr Meshcheriakov",
                "source": "device_tracker.iphone_aleksander_2",
                "device_trackers": ["device_tracker.iphone_aleksander_2"],
            },
        },
    )
    config = HeraldConfig.from_raw(
        {
            "users": {
                "aleksandr_meshcheriakov": {
                    "room_entity": "sensor.alex_room",
                }
            }
        }
    )
    presence = PresenceResolver(hass, config)
    presence._room_wait_exhausted = True
    builder = HeraldContextBuilder(hass, config, presence, _FakeControls())

    runtime_context = await builder.async_build(
        HeraldRequest(event="smoke", message="smoke")
    )

    profile = runtime_context.users[0]
    assert profile.current_room == "living_room"
    assert profile.room_source == "config_room_entity:sensor.alex_room"
    assert runtime_context.primary_room == "living_room"


@pytest.mark.asyncio
async def test_context_builder_falls_back_to_single_occupied_room_for_single_home_user() -> None:
    hass = _FakeHass(
        {
            "person.aleksandr_meshcheriakov": "home",
            "binary_sensor.room_gostinaia_occupied": "on",
        },
        {
            "person.aleksandr_meshcheriakov": {
                "friendly_name": "Aleksandr Meshcheriakov",
                "source": "device_tracker.iphone_aleksander_2",
                "device_trackers": ["device_tracker.iphone_aleksander_2"],
            },
        },
    )
    config = HeraldConfig.from_raw(None)
    presence = PresenceResolver(hass, config)
    presence._room_entities_ready_once = True
    builder = HeraldContextBuilder(hass, config, presence, _FakeControls())

    runtime_context = await builder.async_build(
        HeraldRequest(event="smoke", message="smoke")
    )

    profile = runtime_context.users[0]
    assert profile.current_room == "living_room"
    assert profile.room_source == "single_occupied_room"
    assert runtime_context.primary_room == "living_room"
