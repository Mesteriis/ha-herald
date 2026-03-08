"""Sensor platform for Herald."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DATA_COORDINATORS, DOMAIN
from .entity import HeraldCoordinatorEntity


def _empty_extra(data: dict[str, Any]) -> dict[str, Any]:
    """Return an empty attribute mapping for sensors without extras."""
    return {}


@dataclass(kw_only=True)
class HeraldSensorDescription(SensorEntityDescription):
    """Describes a Herald sensor."""

    value_fn: Callable[[dict[str, Any]], StateType]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] = _empty_extra


SENSORS: tuple[HeraldSensorDescription, ...] = (
    HeraldSensorDescription(
        key="status",
        icon="mdi:shield-home-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("status", "ready"),
        extra_fn=lambda data: {
            "quiet_hours": data.get("quiet_hours", False),
            "home_mode": data.get("home_mode", "unknown"),
            "people_home": data.get("people_home", []),
            "maintenance_mode": data.get("maintenance_mode", False),
            "mute_all": data.get("mute_all", False),
            "maintenance_min_level": data.get("maintenance_min_level", "critical"),
            "characters": data.get("characters", []),
            "plugins": data.get("plugins", {}),
            "control_entities": data.get("control_entities", {}),
            "helper_bootstrap": data.get("helper_bootstrap", {}),
            "control_values": data.get("control_values", {}),
            "room_presence_sensors": data.get("room_presence_sensors", {}),
            "flow_states": data.get("flow_states", {}),
            "snoozed_flows": data.get("snoozed_flows", {}),
            "flow_policies": data.get("flow_policies", {}),
            "channel_policies": data.get("channel_policies", {}),
            "dashboard_feed": data.get("dashboard_feed", []),
            "queued_notifications": data.get("queued_notifications", []),
            "analytics": data.get("analytics", {}),
            "pipeline_trace": data.get("pipeline_trace", []),
        },
    ),
    HeraldSensorDescription(
        key="notifications_today",
        icon="mdi:counter",
        value_fn=lambda data: data.get("notifications_today", 0),
        extra_fn=lambda data: {
            "recent_notifications": data.get("recent_notifications", []),
            "dashboard_feed": data.get("dashboard_feed", []),
            "flow_states": data.get("flow_states", {}),
            "analytics": data.get("analytics", {}),
            "pipeline_trace": data.get("pipeline_trace", []),
        },
    ),
    HeraldSensorDescription(
        key="deliveries_today",
        icon="mdi:send-check-outline",
        value_fn=lambda data: data.get("deliveries_today", 0),
        extra_fn=lambda data: data.get("analytics", {}),
    ),
    HeraldSensorDescription(
        key="dropped_today",
        icon="mdi:bell-remove-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("dropped_today", 0),
        extra_fn=lambda data: data.get("analytics", {}),
    ),
    HeraldSensorDescription(
        key="errors_today",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("errors_today", 0),
        extra_fn=lambda data: data.get("analytics", {}),
    ),
    HeraldSensorDescription(
        key="ai_requests_today",
        icon="mdi:brain",
        value_fn=lambda data: data.get("ai_requests_today", 0),
        extra_fn=lambda data: data.get("analytics", {}),
    ),
    HeraldSensorDescription(
        key="last_notification",
        icon="mdi:bell-ring-outline",
        value_fn=lambda data: data.get("last_notification", {}).get("title", "idle"),
        extra_fn=lambda data: data.get("last_notification", {}),
    ),
    HeraldSensorDescription(
        key="queue_size",
        icon="mdi:playlist-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("queue_size", 0),
        extra_fn=lambda data: {
            "quiet_hours": data.get("quiet_hours", False),
            "home_mode": data.get("home_mode", "unknown"),
            "people_home": data.get("people_home", []),
            "maintenance_mode": data.get("maintenance_mode", False),
            "mute_all": data.get("mute_all", False),
            "characters": data.get("characters", []),
            "plugins": data.get("plugins", {}),
            "control_entities": data.get("control_entities", {}),
            "helper_bootstrap": data.get("helper_bootstrap", {}),
            "control_values": data.get("control_values", {}),
            "room_presence_sensors": data.get("room_presence_sensors", {}),
            "flow_states": data.get("flow_states", {}),
            "snoozed_flows": data.get("snoozed_flows", {}),
            "flow_policies": data.get("flow_policies", {}),
            "channel_policies": data.get("channel_policies", {}),
            "dashboard_feed": data.get("dashboard_feed", []),
            "queued_notifications": data.get("queued_notifications", []),
            "analytics": data.get("analytics", {}),
            "pipeline_trace": data.get("pipeline_trace", []),
            "acknowledged_count": data.get("acknowledged_count", 0),
        },
    ),
)

_ANALYTICS_SENSOR_ENTITY_IDS: dict[str, str] = {
    "deliveries_today": "sensor.herald_notification_center_deliveries_today",
    "dropped_today": "sensor.herald_notification_center_dropped_today",
    "errors_today": "sensor.herald_notification_center_errors_today",
    "ai_requests_today": "sensor.herald_notification_center_ai_requests_today",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Herald sensors from a config entry."""
    await _async_migrate_analytics_sensor_entity_ids(hass, entry)
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(
        HeraldSensor(coordinator, entry, description)
        for description in SENSORS
    )


async def _async_migrate_analytics_sensor_entity_ids(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Rename early analytics sensor ids that were created without translation names."""
    registry = er.async_get(hass)
    for key, expected_entity_id in _ANALYTICS_SENSOR_ENTITY_IDS.items():
        unique_id = f"{entry.entry_id}_{key}"
        current_entity_id = registry.async_get_entity_id(DOMAIN, "sensor", unique_id)
        if not current_entity_id or current_entity_id == expected_entity_id:
            continue
        try:
            registry.async_update_entity(
                current_entity_id,
                new_entity_id=expected_entity_id,
            )
        except ValueError:
            # If the target id already exists, prefer the current registry state over guessing.
            continue


class HeraldSensor(HeraldCoordinatorEntity, SensorEntity):
    """Represent a Herald sensor entity."""

    entity_description: HeraldSensorDescription

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        description: HeraldSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key

    @property
    def native_value(self) -> StateType:
        """Return the current sensor value."""
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes for the sensor."""
        return self.entity_description.extra_fn(self.coordinator.data or {})
