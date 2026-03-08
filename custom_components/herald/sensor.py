"""Sensor platform for Herald."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DATA_COORDINATORS, DOMAIN
from .entity import HeraldCoordinatorEntity


@dataclass(kw_only=True)
class HeraldSensorDescription(SensorEntityDescription):
    """Describes a Herald sensor."""

    value_fn: Callable[[dict[str, Any]], StateType]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}


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
            "flow_states": data.get("flow_states", {}),
            "snoozed_flows": data.get("snoozed_flows", {}),
        },
    ),
    HeraldSensorDescription(
        key="notifications_today",
        icon="mdi:counter",
        value_fn=lambda data: data.get("notifications_today", 0),
        extra_fn=lambda data: {
            "recent_notifications": data.get("recent_notifications", []),
            "flow_states": data.get("flow_states", {}),
        },
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
            "flow_states": data.get("flow_states", {}),
            "snoozed_flows": data.get("snoozed_flows", {}),
            "acknowledged_count": data.get("acknowledged_count", 0),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Herald sensors from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(
        HeraldSensor(coordinator, entry, description)
        for description in SENSORS
    )


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
