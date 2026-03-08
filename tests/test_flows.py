"""Tests for Herald flow helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from custom_components.herald.flows import async_flow_matches, resolve_requested_flow, severity_allowed
from custom_components.herald.models import FlowConfig, NotificationContext


class _FakeStates:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def get(self, entity_id: str):
        state = self._mapping.get(entity_id)
        if state is None:
            return None
        return SimpleNamespace(state=state)


class _FakeHass:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.states = _FakeStates(mapping)


@pytest.mark.asyncio
async def test_flow_conditions_match_presence_and_mode() -> None:
    flow = FlowConfig(
        name="energy_events",
        conditions={
            "presence": "nobody_home",
            "mode": "away",
            "entity_state": [{"entity_id": "binary_sensor.washer_running", "state": "off"}],
        },
    )
    context = NotificationContext(
        flow="energy_events",
        title="Energy",
        message="Washer finished",
        level="warning",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
    )
    hass = _FakeHass(
        {
            "binary_sensor.nobody_home": "on",
            "sensor.home_mode": "away",
            "binary_sensor.washer_running": "off",
        }
    )

    assert await async_flow_matches(hass, flow, context, home_mode_entity="sensor.home_mode") is True


@pytest.mark.asyncio
async def test_flow_conditions_fail_when_mode_is_wrong() -> None:
    flow = FlowConfig(name="system_events", conditions={"mode": "night"})
    context = NotificationContext(
        flow="system_events",
        title="System",
        message="Update finished",
        level="system",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
    )
    hass = _FakeHass({"sensor.home_mode": "home"})

    assert await async_flow_matches(hass, flow, context, home_mode_entity="sensor.home_mode") is False


def test_severity_resolution_and_fallback() -> None:
    flows = {
        "security_alerts": FlowConfig(name="security_alerts"),
        "ai_events": FlowConfig(name="ai_events"),
        "system_events": FlowConfig(name="system_events"),
    }

    assert severity_allowed("critical", "warning") is True
    assert resolve_requested_flow(flows, None, "security") == "security_alerts"
    assert resolve_requested_flow(flows, None, "ai") == "ai_events"
    assert resolve_requested_flow(flows, None, "system") == "system_events"
