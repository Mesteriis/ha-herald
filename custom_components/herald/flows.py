"""Flow helpers for the Herald integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from .const import CONF_CONDITIONS, CONF_HOME_MODE_ENTITY, CONF_SEVERITY, SEVERITY_RANK
from .models import FlowConfig, NotificationContext


def severity_rank(level: str) -> int:
    """Return the comparable rank for a severity label."""
    return SEVERITY_RANK.get(level, SEVERITY_RANK["info"])


def severity_allowed(level: str, minimum: str) -> bool:
    """Check that the provided level satisfies the configured minimum."""
    return severity_rank(level) >= severity_rank(minimum)


async def async_flow_matches(
    hass: HomeAssistant,
    flow: FlowConfig,
    context: NotificationContext,
    *,
    home_mode_entity: str | None = None,
) -> bool:
    """Evaluate flow conditions against the current Home Assistant state."""
    conditions = dict(flow.conditions)
    if not conditions:
        return True

    now_local = datetime.now().time()

    presence_value = conditions.get("presence")
    if presence_value == "nobody_home":
        nobody_entity = conditions.get("nobody_home_entity", "binary_sensor.nobody_home")
        if hass.states.get(nobody_entity) is None or hass.states.get(nobody_entity).state != "on":
            return False
    if presence_value == "someone_home":
        nobody_entity = conditions.get("nobody_home_entity", "binary_sensor.nobody_home")
        if hass.states.get(nobody_entity) is not None and hass.states.get(nobody_entity).state == "on":
            return False

    if time_condition := conditions.get("time"):
        after_value = time_condition.get("after")
        before_value = time_condition.get("before")
        if after_value:
            after_time = datetime.strptime(str(after_value), "%H:%M").time()
            if now_local < after_time:
                return False
        if before_value:
            before_time = datetime.strptime(str(before_value), "%H:%M").time()
            if now_local > before_time:
                return False

    if expected_mode := conditions.get("mode"):
        mode_entity = conditions.get(CONF_HOME_MODE_ENTITY, home_mode_entity or "sensor.home_mode")
        state = hass.states.get(mode_entity)
        if state is None or state.state != expected_mode:
            return False

    if entity_state_conditions := conditions.get("entity_state"):
        if isinstance(entity_state_conditions, dict):
            iterable = [entity_state_conditions]
        else:
            iterable = list(entity_state_conditions)
        for item in iterable:
            entity_id = item.get("entity_id")
            expected = item.get("state")
            if not entity_id or expected is None:
                continue
            state = hass.states.get(entity_id)
            if state is None or state.state != str(expected):
                return False

    if source_allowlist := conditions.get("source_in"):
        if context.source not in source_allowlist:
            return False

    return True


def resolve_requested_flow(flows: dict[str, FlowConfig], requested_flow: str | None, level: str) -> str:
    """Resolve the effective flow name for a notification."""
    if requested_flow and requested_flow in flows:
        return requested_flow
    if requested_flow:
        normalized = requested_flow.strip().lower().replace(" ", "_")
        if normalized in flows:
            return normalized

    if level in {"security", "critical"} and "security_alerts" in flows:
        return "security_alerts"
    if level in {"ai"} and "ai_events" in flows:
        return "ai_events"
    if level in {"warning"} and "device_alerts" in flows:
        return "device_alerts"
    if level in {"system"} and "system_events" in flows:
        return "system_events"
    if "system_events" in flows:
        return "system_events"
    return next(iter(flows), "system_events")


def flow_defaults(flow: FlowConfig) -> dict[str, Any]:
    """Expose useful flow defaults for traces and diagnostics."""
    return {
        CONF_SEVERITY: flow.severity,
        CONF_CONDITIONS: flow.conditions,
        "allow_summary": flow.allow_summary,
        "summary_window_seconds": flow.summary_window_seconds,
    }
