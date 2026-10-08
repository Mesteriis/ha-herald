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


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["Russian", "English", "Spanish", "French"])
async def test_domovoy_templates_render_all_delivery_modes(tmp_path: Path, language: str) -> None:
    manager = CharacterManager(_FakeHass(tmp_path))
    await manager.async_initialize()
    context = {
        "title": "Window alert",
        "event": "window_open",
        "message": "The living room window has been open for 15 minutes; outside it is 8 degrees.",
        "level": "warning",
        "language": language,
        "room": "office",
        "notifications": [{"message": "Fixture wash finished", "level": "info"}],
    }

    system = manager.render_prompt("domovoy", "system.jinja", context)
    assert system is not None
    assert "fairy-tale household spirit" in system
    assert f"spoken {language}" in system
    assert "Delivery room: office" in system
    assert "never infer an event location" in system
    for template_name in ("notification.jinja", "critical.jinja"):
        rendered = manager.render_prompt("domovoy", template_name, context)
        assert rendered is not None
        assert context["message"] in rendered
        assert "window_open" in rendered
    summary = manager.render_prompt("domovoy", "short.jinja", context)
    assert summary is not None
    assert "Fixture wash finished" in summary


@pytest.mark.asyncio
async def test_default_scaffold_keeps_existing_domovoy_customizations(tmp_path: Path) -> None:
    root = tmp_path / "herald"
    profile = root / "domovoy"
    profile.mkdir(parents=True)
    custom_prompt = "Custom household voice: {{ message }}"
    (profile / "notification.jinja").write_text(custom_prompt, encoding="utf-8")
    manager = CharacterManager(_FakeHass(tmp_path))

    await manager.async_initialize()
    await manager.async_initialize()

    assert (profile / "notification.jinja").read_text(encoding="utf-8") == custom_prompt
    assert manager.render_prompt("domovoy", "notification.jinja", {"message": "Fixture"}) == "Custom household voice: Fixture"
    assert (profile / "critical.jinja").exists()
