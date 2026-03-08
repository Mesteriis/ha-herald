"""Tests for Herald sensor entity setup and migrations."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.herald.sensor import _async_migrate_analytics_sensor_entity_ids


class _FakeRegistry:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = dict(mapping)
        self.updated: list[tuple[str, str]] = []

    def async_get_entity_id(self, domain: str, platform: str, unique_id: str) -> str | None:
        assert domain == "herald"
        assert platform == "sensor"
        return self.mapping.get(unique_id)

    def async_update_entity(self, entity_id: str, *, new_entity_id: str) -> None:
        self.updated.append((entity_id, new_entity_id))


@pytest.mark.asyncio
async def test_migrate_analytics_sensor_entity_ids(monkeypatch) -> None:
    entry = SimpleNamespace(entry_id="entry123")
    registry = _FakeRegistry(
        {
            "entry123_deliveries_today": "sensor.herald_notification_center",
            "entry123_dropped_today": "sensor.herald_notification_center_2",
            "entry123_errors_today": "sensor.herald_notification_center_3",
            "entry123_ai_requests_today": "sensor.herald_notification_center_4",
        }
    )

    monkeypatch.setattr(
        "custom_components.herald.sensor.er.async_get",
        lambda hass: registry,
    )

    await _async_migrate_analytics_sensor_entity_ids(object(), entry)

    assert registry.updated == [
        (
            "sensor.herald_notification_center",
            "sensor.herald_notification_center_deliveries_today",
        ),
        (
            "sensor.herald_notification_center_2",
            "sensor.herald_notification_center_dropped_today",
        ),
        (
            "sensor.herald_notification_center_3",
            "sensor.herald_notification_center_errors_today",
        ),
        (
            "sensor.herald_notification_center_4",
            "sensor.herald_notification_center_ai_requests_today",
        ),
    ]
