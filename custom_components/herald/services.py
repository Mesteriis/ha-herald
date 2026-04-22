"""Service registration for Herald."""

from __future__ import annotations

import inspect
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

try:
    from homeassistant.core import ServiceCall, SupportsResponse
except ImportError:  # pragma: no cover - compatibility fallback for test/runtime drift
    ServiceCall = Any  # type: ignore[assignment]
    SupportsResponse = None  # type: ignore[assignment]

ServiceResponse = dict[str, Any]

from .const import (
    CONF_NOTIFICATION_ID,
    DATA_COORDINATORS,
    DEFAULT_DASHBOARD_PRESET,
    DEFAULT_SNOOZE_MINUTES,
    DOMAIN,
    SERVICE_ACKNOWLEDGE,
    SERVICE_GENERATE_DASHBOARD,
    SERVICE_GET_NOTIFICATION_POLICY,
    SERVICE_GET_NOTIFICATION_REGISTRY,
    SERVICE_NOTIFY,
    SERVICE_REFRESH_NOTIFICATION_REGISTRY,
    SERVICE_ROUTE_PREVIEW,
    SERVICE_RESET_NOTIFICATION_POLICY,
    SERVICE_SET_NOTIFICATION_POLICY,
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
        vol.Optional("tts_options"): vol.Any(dict, cv.string),
        vol.Optional("mobile_options"): vol.Any(dict, cv.string),
        vol.Optional("mobile_zone"): cv.string,
        vol.Optional("send_voice"): cv.boolean,
        vol.Optional("send_text"): cv.boolean,
        vol.Optional("send_mobile"): cv.boolean,
        vol.Optional("send_telegram"): cv.boolean,
        vol.Optional("target_group"): cv.string,
        vol.Optional("target"): vol.Any(dict, cv.string),
        vol.Optional("timestamp_policy"): cv.string,
        vol.Optional("already_humanized"): cv.boolean,
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
        vol.Optional("rewrite", default=False): cv.boolean,
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
ROUTE_PREVIEW_SCHEMA = NOTIFY_SCHEMA.extend({})

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

REFRESH_NOTIFICATION_REGISTRY_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Optional("force", default=True): cv.boolean,
    }
)

GET_NOTIFICATION_REGISTRY_SCHEMA = vol.Schema({vol.Optional("entry_id"): cv.string})

GET_NOTIFICATION_POLICY_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("notification_key"): cv.string,
    }
)

SET_NOTIFICATION_POLICY_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("notification_key"): cv.string,
        vol.Optional("enabled"): cv.boolean,
        vol.Optional("delivery_mode"): vol.In(
            ["inherit", "disabled", "text_only", "voice_only", "push_only", "custom"]
        ),
        vol.Optional("channels"): vol.Any([cv.string], cv.string),
        vol.Optional("level_override"): cv.string,
        vol.Optional("cooldown_override"): vol.Any(vol.Coerce(int), None, ""),
        vol.Optional("notes"): cv.string,
    }
)

RESET_NOTIFICATION_POLICY_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("notification_key"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register Herald services once."""
    if hass.data.get(DOMAIN, {}).get("services_registered"):
        return

    def _async_register(
        service: str,
        handler,
        *,
        schema=None,
        supports_response=None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if schema is not None:
            kwargs["schema"] = schema
        if supports_response is not None:
            if "supports_response" in inspect.signature(hass.services.async_register).parameters:
                kwargs["supports_response"] = supports_response
        hass.services.async_register(DOMAIN, service, handler, **kwargs)

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

    async def async_handle_route_preview(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return await coordinator.async_preview_route(call.data)

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

    async def async_handle_refresh_notification_registry(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return await coordinator.async_refresh_notification_registry(force=call.data["force"])

    async def async_handle_get_notification_registry(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return coordinator.notification_registry_snapshot()

    async def async_handle_get_notification_policy(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return coordinator.get_notification_policy(call.data["notification_key"])

    async def async_handle_set_notification_policy(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return await coordinator.async_set_notification_policy(call.data)

    async def async_handle_reset_notification_policy(call: ServiceCall) -> ServiceResponse:
        coordinator = _get_coordinator(hass, call.data.get("entry_id"))
        return await coordinator.async_reset_notification_policy(call.data["notification_key"])

    supports_only = getattr(SupportsResponse, "ONLY", None)
    supports_optional = getattr(SupportsResponse, "OPTIONAL", None)

    _async_register(SERVICE_NOTIFY, async_handle_notify, schema=NOTIFY_SCHEMA)
    _async_register(
        SERVICE_GENERATE_DASHBOARD,
        async_handle_generate_dashboard,
        schema=DASHBOARD_SCHEMA,
    )
    _async_register(
        SERVICE_SET_FLOW_STATE,
        async_handle_set_flow_state,
        schema=FLOW_STATE_SCHEMA,
    )
    _async_register(
        SERVICE_TRACE_SNAPSHOT,
        async_handle_trace_snapshot,
        schema=TRACE_SCHEMA,
        supports_response=supports_only,
    )
    _async_register(
        SERVICE_ROUTE_PREVIEW,
        async_handle_route_preview,
        schema=ROUTE_PREVIEW_SCHEMA,
        supports_response=supports_only,
    )
    _async_register(
        SERVICE_ACKNOWLEDGE,
        async_handle_acknowledge,
        schema=ACKNOWLEDGE_SCHEMA,
    )
    _async_register(
        SERVICE_SNOOZE_FLOW,
        async_handle_snooze_flow,
        schema=SNOOZE_SCHEMA,
    )
    _async_register(
        SERVICE_REFRESH_NOTIFICATION_REGISTRY,
        async_handle_refresh_notification_registry,
        schema=REFRESH_NOTIFICATION_REGISTRY_SCHEMA,
        supports_response=supports_optional,
    )
    _async_register(
        SERVICE_GET_NOTIFICATION_REGISTRY,
        async_handle_get_notification_registry,
        schema=GET_NOTIFICATION_REGISTRY_SCHEMA,
        supports_response=supports_only,
    )
    _async_register(
        SERVICE_GET_NOTIFICATION_POLICY,
        async_handle_get_notification_policy,
        schema=GET_NOTIFICATION_POLICY_SCHEMA,
        supports_response=supports_only,
    )
    _async_register(
        SERVICE_SET_NOTIFICATION_POLICY,
        async_handle_set_notification_policy,
        schema=SET_NOTIFICATION_POLICY_SCHEMA,
        supports_response=supports_optional,
    )
    _async_register(
        SERVICE_RESET_NOTIFICATION_POLICY,
        async_handle_reset_notification_policy,
        schema=RESET_NOTIFICATION_POLICY_SCHEMA,
        supports_response=supports_optional,
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
    hass.services.async_remove(DOMAIN, SERVICE_ROUTE_PREVIEW)
    hass.services.async_remove(DOMAIN, SERVICE_ACKNOWLEDGE)
    hass.services.async_remove(DOMAIN, SERVICE_SNOOZE_FLOW)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_NOTIFICATION_REGISTRY)
    hass.services.async_remove(DOMAIN, SERVICE_GET_NOTIFICATION_REGISTRY)
    hass.services.async_remove(DOMAIN, SERVICE_GET_NOTIFICATION_POLICY)
    hass.services.async_remove(DOMAIN, SERVICE_SET_NOTIFICATION_POLICY)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_NOTIFICATION_POLICY)
    hass.data.setdefault(DOMAIN, {})["services_registered"] = False


def _get_coordinator(hass: HomeAssistant, entry_id: str | None):
    coordinators = hass.data.get(DOMAIN, {}).get(DATA_COORDINATORS, {})
    if entry_id:
        return coordinators[entry_id]
    return next(iter(coordinators.values()))
