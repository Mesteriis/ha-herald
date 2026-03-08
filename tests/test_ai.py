"""Tests for Herald AI helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from custom_components.herald.ai import HeraldAIClient
from custom_components.herald.models import HeraldConfig, NotificationContext


@pytest.mark.asyncio
async def test_ai_summary_uses_static_fallback_when_disabled() -> None:
    config = HeraldConfig.from_raw({"ollama": {"enabled": False}})
    client = HeraldAIClient(AsyncMock(), config)
    notifications = [
        NotificationContext(
            flow="device_alerts",
            title="Door",
            message="Front door opened",
            level="warning",
            source="automation.door",
            timestamp="2026-03-08T11:00:00+00:00",
        ),
        NotificationContext(
            flow="device_alerts",
            title="Washer",
            message="Washer finished",
            level="info",
            source="automation.washer",
            timestamp="2026-03-08T11:01:00+00:00",
        ),
    ]

    summary = await client.async_summarize_notifications(notifications, language="ru", personality="HESTIA")

    assert "событий" in summary["message"].lower()
    assert summary["title"]
