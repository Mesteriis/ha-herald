"""Tests for Herald routing helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock

from custom_components.herald.models import HeraldConfig, NotificationContext, PresenceSnapshot
from custom_components.herald.router import HeraldRouter


class _FakeStates:
    def get(self, entity_id: str):
        return None


class _FakeServices:
    def __init__(self) -> None:
        self.async_call = AsyncMock()


class _FakeHass:
    def __init__(self) -> None:
        self.states = _FakeStates()
        self.services = _FakeServices()


class _FakePresence:
    def __init__(self, snapshot: PresenceSnapshot) -> None:
        self._snapshot = snapshot

    async def async_resolve(self, context: NotificationContext) -> PresenceSnapshot:
        return self._snapshot

    def away_channels(self) -> list[str]:
        return []


def test_quiet_hours_override_allows_tts_channel() -> None:
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "bedroom_tts": {
                    "type": "tts",
                    "entity_id": "media_player.bedroom",
                    "quiet_hours_policy": "allow",
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["bedroom_tts"],
                }
            },
        }
    )
    snapshot = PresenceSnapshot(quiet_hours=True, people_home=["person.alex"], primary_room="bedroom")
    router = HeraldRouter(_FakeHass(), config, AsyncMock(), _FakePresence(snapshot))
    context = NotificationContext(
        flow="system_events",
        title="System",
        message="Night summary",
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
    )

    channel_names = router._resolve_channel_names(context, config.flows["system_events"], snapshot)

    assert channel_names == ["bedroom_tts"]


def test_mobile_actions_contain_notification_feedback_tokens() -> None:
    config = HeraldConfig.from_raw(None)
    router = HeraldRouter(
        _FakeHass(),
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot()),
    )
    context = NotificationContext(
        flow="security_alerts",
        title="Door",
        message="Front door opened",
        level="warning",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        notification_id="notif_123",
        include_actions=True,
    )

    actions = router._build_mobile_actions(context, "en")

    assert actions[0]["title"] == "Acknowledge"
    assert actions[0]["action"].endswith("notif_123")
    assert "notif_123" in actions[1]["action"]
