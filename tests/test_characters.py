"""Tests for Herald AI character scaffolding."""

from __future__ import annotations

from pathlib import Path

import pytest

from custom_components.herald.characters import CharacterManager


class _FakeStates:
    def get(self, entity_id: str):
        return None


class _FakeConfig:
    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, value: str) -> str:
        return str(self._root / value)


class _FakeHass:
    def __init__(self, root: Path) -> None:
        self.states = _FakeStates()
        self.config = _FakeConfig(root)

    async def async_add_executor_job(self, func, *args):
        return func(*args)


@pytest.mark.asyncio
async def test_character_manager_bootstraps_default_characters(tmp_path: Path) -> None:
    manager = CharacterManager(_FakeHass(tmp_path))

    await manager.async_initialize()

    assert "hestia" in manager.characters
    prompt = manager.render_prompt(
        "hestia",
        "notification.jinja",
        {
            "message": "Door opened",
            "event": "door_opened",
            "level": "warning",
            "person": "person.alex",
            "room": "living_room",
            "entities": ["binary_sensor.front_door"],
            "context": {"source": "automation"},
            "time": "2026-03-08T12:00:00+00:00",
            "language": "English",
        },
    )

    assert prompt is not None
    assert "door_opened" in prompt

