"""Character template filesystem rendering stays outside the HA event loop."""

from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.herald.ai import HeraldAIClient
from custom_components.herald.characters import CharacterManager
from custom_components.herald.models import HeraldConfig, NotificationContext


@pytest.mark.asyncio
@pytest.mark.parametrize("summary", [False, True])
async def test_ai_renders_file_templates_in_executor(tmp_path, monkeypatch, summary) -> None:
    main_thread = threading.get_ident()
    hass = SimpleNamespace(async_add_executor_job=asyncio.to_thread)
    manager = CharacterManager(hass, root=tmp_path / "characters")
    await manager.async_initialize()
    original = manager.render_prompt
    rendered = []

    def checked_render(*args):
        assert threading.get_ident() != main_thread
        result = original(*args)
        rendered.append((args[1], result))
        return result

    monkeypatch.setattr(manager, "render_prompt", checked_render)
    client = HeraldAIClient(
        hass,
        AsyncMock(),
        HeraldConfig.from_raw({"ollama": {"enabled": True}}),
        manager,
        SimpleNamespace(is_ai_enabled=lambda level=None: True),
    )
    client._async_generate_json = AsyncMock(return_value=({"title": "Fixture", "message": "Fixture result"}, None))
    if summary:
        result = await client.async_summarize_notifications(
            [NotificationContext(flow="device_alerts", title="Test", message="Test", level="info", source="test", timestamp="test")],
            language="en", character="hestia", render_context={},
        )
    else:
        result = await client.async_rewrite_payload(
            title="Test", message="Test", level="info", language="en", character="hestia", rewrite=True, render_context={},
        )
    assert len(rendered) == 2
    assert all(text for _, text in rendered)
    assert result["_herald_ai_prompt_source"] == "character_template"
    client._async_generate_json.assert_awaited_once()
