"""Tests for Herald AI helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from custom_components.herald.ai import HeraldAIClient
from custom_components.herald.characters import CharacterManager
from custom_components.herald.const import VERSION
from custom_components.herald.models import HeraldConfig, NotificationContext


class _Response:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def raise_for_status(self):
        return None

    async def json(self):
        return self.payload


class _Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response(self.payload)


@pytest.mark.asyncio
async def test_openai_compatible_request_and_response(tmp_path: Path) -> None:
    session = _Session({"choices": [{"message": {"content": '{"title":"Ready","message":"Done"}'}}]})
    config = HeraldConfig.from_raw({"ollama": {"provider": "openai", "host": "https://ai.example.invalid", "model": "synthetic-model", "api_key": "synthetic-secret"}})
    client = HeraldAIClient(_FakeHass(tmp_path), session, config, CharacterManager(_FakeHass(tmp_path)), _EnabledControls())
    result = await client._async_generate_json("synthetic prompt")
    assert result == ({"title": "Ready", "message": "Done"}, None)
    url, request = session.calls[0]
    assert url == "https://ai.example.invalid/v1/chat/completions"
    assert request["json"] == {"model": "synthetic-model", "stream": False, "messages": [{"role": "user", "content": "synthetic prompt"}]}
    assert request["headers"] == {"Authorization": "Bearer synthetic-secret", "User-Agent": f"Herald/{VERSION}"}


@pytest.mark.asyncio
@pytest.mark.parametrize("settings,reason", [
    ({"provider": "openai", "host": "https://ai.example.invalid", "api_key": ""}, "ai_missing_api_key"),
    ({"provider": "openai", "host": "http://ai.example.invalid", "api_key": "synthetic-secret"}, "ai_invalid_configuration"),
    ({"provider": "unsupported", "host": "https://ai.example.invalid", "api_key": "synthetic-secret"}, "ai_invalid_configuration"),
])
async def test_invalid_provider_configuration_never_sends_prompt(tmp_path: Path, settings, reason) -> None:
    session = _Session({})
    hass = _FakeHass(tmp_path)
    client = HeraldAIClient(hass, session, HeraldConfig.from_raw({"ollama": settings}), CharacterManager(hass), _EnabledControls())
    assert await client._async_generate_json("synthetic prompt") == (None, reason)
    assert session.calls == []


@pytest.mark.asyncio
async def test_openai_invalid_answer_falls_back_without_logging_content(tmp_path: Path, caplog) -> None:
    session = _Session({"choices": [{"message": {"content": "private non-json text"}}]})
    hass = _FakeHass(tmp_path)
    client = HeraldAIClient(hass, session, HeraldConfig.from_raw({"ollama": {"provider": "openai", "host": "https://ai.example.invalid", "api_key": "synthetic-secret"}}), CharacterManager(hass), _EnabledControls())
    assert await client._async_generate_json("private prompt") == (None, "ai_invalid_json")
    assert "private non-json text" not in caplog.text
    assert "synthetic-secret" not in caplog.text


@pytest.mark.asyncio
async def test_legacy_ollama_request_is_unchanged(tmp_path: Path) -> None:
    session = _Session({"response": '{"title":"Legacy","message":"Works"}'})
    hass = _FakeHass(tmp_path)
    client = HeraldAIClient(hass, session, HeraldConfig.from_raw({"ollama": {"host": "http://ollama.local:11434", "model": "llama3"}}), CharacterManager(hass), _EnabledControls())
    assert await client._async_generate_json("synthetic prompt") == ({"title": "Legacy", "message": "Works"}, None)
    url, request = session.calls[0]
    assert url == "http://ollama.local:11434/api/generate"
    assert request["json"]["format"] == "json"
    assert request["json"]["prompt"] == "synthetic prompt"
    assert request["headers"] is None


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

    assert payload["title"] == "Herald"
    assert payload["message"] == "Maintenance mode enabled"
    assert payload["_herald_ai_status"] == "passthrough"
    assert payload["_herald_ai_reason"] == "rewrite_disabled"
    client._async_generate_json.assert_not_awaited()  # type: ignore[attr-defined]
