"""Service registration for Herald."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_NOTIFICATION_ID,
    DATA_COORDINATORS,
    DEFAULT_DASHBOARD_PRESET,
    DEFAULT_SNOOZE_MINUTES,
    DOMAIN,
    SERVICE_ACKNOWLEDGE,
    SERVICE_GENERATE_DASHBOARD,
    SERVICE_NOTIFY,
    SERVICE_SET_FLOW_STATE,
    SERVICE_SNOOZE_FLOW,
    SERVICE_TRACE_SNAPSHOT,
    SUPPORTED_DASHBOARD_PRESETS,
)

NOTIFY_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Optional("event"): cv.string,
        vol.Optional("level", default="info"): vol.In(
            ["debug", "info", "notice", "warning", "critical", "security", "ai", "system"]
        ),
        vol.Required("message"): cv.string,
        vol.Optional("ai"): vol.Any(dict, cv.string),
        vol.Optional("context"): vol.Any(dict, cv.string),
        vol.Optional("entities"): vol.Any([cv.string], cv.string),
        vol.Optional("suppress"): vol.All(vol.Coerce(int), vol.Range(min=0, max=24 * 60 * 60)),
        vol.Optional("group"): cv.string,
        vol.Optional("immediately", default=True): cv.boolean,
        vol.Optional("title", default="Herald"): cv.string,
        vol.Optional("flow"): cv.string,
        vol.Optional("source", default="manual"): cv.string,
        vol.Optional("automation_id"): cv.string,
        vol.Optional("device"): cv.string,
        vol.Optional("room"): cv.string,
        vol.Optional("user"): cv.string,
        vol.Optional("users"): vol.Any([cv.string], cv.string),
        vol.Optional("channels"): vol.Any([cv.string], cv.string),
        vol.Optional("personality"): cv.string,
        vol.Optional("metadata"): vol.Any(dict, cv.string),
        vol.Optional("notification_id"): cv.string,
        vol.Optional("include_actions", default=False): cv.boolean,
        vol.Optional("rewrite", default=True): cv.boolean,
        vol.Optional("summarize", default=True): cv.boolean,
        vol.Optional("force", default=False): cv.boolean,
    }
)

DASHBOARD_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Optional("path", default="dashboards/herald_dashboard.yaml"): cv.string,
        vol.Optional("title", default="Herald Control Center"): cv.string,
        vol.Optional("preset", default=DEFAULT_DASHBOARD_PRESET): vol.In(SUPPORTED_DASHBOARD_PRESETS),
    }
)

FLOW_STATE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("flow"): cv.string,
        vol.Required("enabled"): cv.boolean,
    }
)

TRACE_SCHEMA = vol.Schema({vol.Optional("entry_id"): cv.string})

ACKNOWLEDGE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("notification_id"): cv.string,
        vol.Optional("actor"): cv.string,
        vol.Optional("source", default="service"): cv.string,
    }
)

SNOOZE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("flow"): cv.string,
        vol.Optional(CONF_NOTIFICATION_ID): cv.string,
        vol.Optional("minutes", default=DEFAULT_SNOOZE_MINUTES): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=24 * 60)
        ),
        vol.Optional("actor"): cv.string,
        vol.Optional("source", default="service"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register Herald services once."""
    if hass.data.get(DOMAIN, {}).get("services_registered"):
        return

    async def async_handle_notify(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        await coordinator.async_handle_service_notify(call.data)

    async def async_handle_generate_dashboard(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        await coordinator.async_generate_dashboard(
            path=call.data["path"],
            title=call.data["title"],
            preset=call.data["preset"],
        )

    async def async_handle_set_flow_state(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        await coordinator.async_set_flow_state(call.data["flow"], call.data["enabled"])

    async def async_handle_trace_snapshot(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return coordinator.trace_snapshot()

    async def async_handle_acknowledge(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        await coordinator.async_acknowledge(
            call.data["notification_id"],
            actor=call.data.get("actor"),
            source=call.data["source"],
        )

    async def async_handle_snooze_flow(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        await coordinator.async_snooze_flow(
            call.data["flow"],
            minutes=call.data["minutes"],
            actor=call.data.get("actor"),
            source=call.data["source"],
            notification_id=call.data.get(CONF_NOTIFICATION_ID),
        )

    hass.services.async_register(DOMAIN, SERVICE_NOTIFY, async_handle_notify, schema=NOTIFY_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_DASHBOARD,
        async_handle_generate_dashboard,
        schema=DASHBOARD_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_STATE,
        async_handle_set_flow_state,
        schema=FLOW_STATE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TRACE_SNAPSHOT,
        async_handle_trace_snapshot,
        schema=TRACE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACKNOWLEDGE,
        async_handle_acknowledge,
        schema=ACKNOWLEDGE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SNOOZE_FLOW,
        async_handle_snooze_flow,
        schema=SNOOZE_SCHEMA,
    )
    hass.data.setdefault(DOMAIN, {})["services_registered"] = True


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister Herald services if the last entry is removed."""
    coordinators = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})
    if coordinators:
        return
    hass.services.async_remove(DOMAIN, SERVICE_NOTIFY)
    hass.services.async_remove(DOMAIN, SERVICE_GENERATE_DASHBOARD)
    hass.services.async_remove(DOMAIN, SERVICE_SET_FLOW_STATE)
    hass.services.async_remove(DOMAIN, SERVICE_TRACE_SNAPSHOT)
    hass.services.async_remove(DOMAIN, SERVICE_ACKNOWLEDGE)
    hass.services.async_remove(DOMAIN, SERVICE_SNOOZE_FLOW)
    hass.data.setdefault(DOMAIN, {})["services_registered"] = False


def _get_coordinator(hass: HomeAssistant, entry_id: str | None):
    coordinators = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})
    if entry_id:
        return coordinators[entry_id]
    return next(iter(coordinators.values()))
