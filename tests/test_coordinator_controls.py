"""Tests for Herald coordinator control-plane helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.herald.coordinator import HeraldCoordinator
from custom_components.herald.models import HeraldConfig, NotificationContext


def test_mute_all_drops_non_critical_notifications() -> None:
    fake = SimpleNamespace(
        controls=SimpleNamespace(is_mute_all_enabled=lambda: True),
    )

    assert HeraldCoordinator._drop_for_mute_all(
        fake,
        NotificationContext(
            flow="system_events",
            title="Muted",
            message="Skip warning",
            level="warning",
            source="automation.test",
            timestamp="2026-03-08T11:00:00+00:00",
        ),
    ) is True
    assert HeraldCoordinator._drop_for_mute_all(
        fake,
        NotificationContext(
            flow="system_events",
            title="Critical",
            message="Allow critical",
            level="critical",
            source="automation.test",
            timestamp="2026-03-08T11:00:00+00:00",
        ),
    ) is False


def test_maintenance_mode_prefers_herald_owned_switch() -> None:
    fake = SimpleNamespace(
        controls=SimpleNamespace(maintenance_mode_enabled=lambda: True),
        _external_maintenance_mode_active=lambda: False,
    )

    assert HeraldCoordinator._maintenance_mode_active(fake) is True


@pytest.mark.asyncio
async def test_sync_external_maintenance_entity_calls_helper_service() -> None:
    services = SimpleNamespace(async_call=AsyncMock())
    fake = SimpleNamespace(
        config=HeraldConfig.from_raw(
            {
                "router": {
                    "maintenance_mode_entity": "input_boolean.maintenance_mode",
                }
            }
        ),
        hass=SimpleNamespace(services=services),
    )

    await HeraldCoordinator._async_sync_external_maintenance_entity(fake, True)

    services.async_call.assert_awaited_once_with(
        "input_boolean",
        "turn_on",
        {"entity_id": "input_boolean.maintenance_mode"},
        blocking=True,
    )


@pytest.mark.asyncio
async def test_self_action_announcement_requires_someone_home() -> None:
    fake = SimpleNamespace(
        _someone_home_for_self_action=lambda: False,
        _voice_announcement_channels=lambda: ["voice_auto"],
        async_handle_service_notify=AsyncMock(),
    )

    await HeraldCoordinator._async_announce_self_action(
        fake,
        message="Herald runtime action",
        level="info",
    )

    fake.async_handle_service_notify.assert_not_awaited()


@pytest.mark.asyncio
async def test_self_action_announcement_uses_voice_channels_only() -> None:
    fake = SimpleNamespace(
        _someone_home_for_self_action=lambda: True,
        _voice_announcement_channels=lambda: ["voice_auto", "tv_auto"],
        async_handle_service_notify=AsyncMock(),
    )

    await HeraldCoordinator._async_announce_self_action(
        fake,
        message="Herald runtime action",
        level="info",
        metadata={"herald_runtime_key": "mute_all"},
    )

    fake.async_handle_service_notify.assert_awaited_once()
    payload = fake.async_handle_service_notify.await_args.args[0]
    assert payload["channels"] == ["voice_auto", "tv_auto"]
    assert payload["metadata"]["bypass_channel_policy"] is True
