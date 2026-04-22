"""Tests for Herald AI helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from custom_components.herald.ai import HeraldAIClient
from custom_components.herald.characters import CharacterManager
from custom_components.herald.models import HeraldConfig, NotificationContext


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


class _FakeControls:
    def is_ai_enabled(self, level: str | None = None) -> bool:
        return False


class _EnabledControls:
    def is_ai_enabled(self, level: str | None = None) -> bool:
        return True


@pytest.mark.asyncio
async def test_ai_summary_uses_static_fallback_when_disabled(tmp_path: Path) -> None:
    config = HeraldConfig.from_raw({"ollama": {"enabled": False}})
    hass = _FakeHass(tmp_path)
    client = HeraldAIClient(hass, AsyncMock(), config, CharacterManager(hass), _FakeControls())
    notifications = [
        NotificationContext(
            flow="device_alerts",
            title="Door",
            message="Front door opened",
            level="warning",
            source="automation.door",
            timestamp="2026-03-08T11:00:00+00:00",
            event="door_opened",
        ),
        NotificationContext(
            flow="device_alerts",
            title="Washer",
            message="Washer finished",
            level="info",
            source="automation.washer",
            timestamp="2026-03-08T11:01:00+00:00",
            event="washer_finished",
        ),
    ]

    summary = await client.async_summarize_notifications(
        notifications,
        language="ru",
        character="hestia",
        render_context={"event": "summary"},
    )

    assert "событий" in summary["message"].lower()
    assert summary["title"]


@pytest.mark.asyncio
async def test_ai_rewrite_false_skips_translation_and_rewrite(tmp_path: Path) -> None:
    config = HeraldConfig.from_raw({"ollama": {"enabled": True}})
    hass = _FakeHass(tmp_path)
    client = HeraldAIClient(hass, AsyncMock(), config, CharacterManager(hass), _EnabledControls())
    client._async_generate_json = AsyncMock(return_value={"title": "Translated", "message": "Translated"})  # type: ignore[attr-defined]

    payload = await client.async_rewrite_payload(
        title="Herald",
        message="Maintenance mode enabled",
        level="info",
        language="en",
        character="hestia",
        rewrite=False,
        render_context={"event": "herald_runtime"},
    )

    assert payload == {"title": "Herald", "message": "Maintenance mode enabled"}
    client._async_generate_json.assert_not_awaited()  # type: ignore[attr-defined]
