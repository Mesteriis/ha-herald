"""Binary sensor platform for Herald room presence diagnostics."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DATA_COORDINATORS, DOMAIN, topology_signal
from .controls import room_presence_entity_id, room_presence_sensor_entity_id
from .entity import HeraldCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Herald room presence binary sensors."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    known_rooms = set(coordinator.presence.room_sensors())
    async_add_entities(
        HeraldRoomPresenceBinarySensor(coordinator, entry, room_name)
        for room_name in sorted(known_rooms)
    )

    @callback
    def _async_handle_topology_change() -> None:
        new_rooms = [
            room_name
            for room_name in sorted(coordinator.presence.room_sensors())
            if room_name not in known_rooms
        ]
        if not new_rooms:
            return
        known_rooms.update(new_rooms)
        async_add_entities(
            HeraldRoomPresenceBinarySensor(coordinator, entry, room_name)
            for room_name in new_rooms
        )

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            topology_signal(entry.entry_id),
            _async_handle_topology_change,
        )
    )


class HeraldRoomPresenceBinarySensor(HeraldCoordinatorEntity, BinarySensorEntity):
    """Resolved room presence sensor backed by real room entities and Herald fallback."""

    _attr_has_entity_name = False

    def __init__(self, coordinator, entry: ConfigEntry, room_name: str) -> None:
        super().__init__(coordinator)
        self._room_name = room_name
        self._attr_unique_id = f"{entry.entry_id}_room_presence_{room_name}"
        self._attr_icon = "mdi:motion-sensor"
        self._attr_translation_key = "room_presence_sensor"
        self._attr_translation_placeholders = {
            "room_name": room_name.replace("_", " ").title(),
        }
        self.entity_id = room_presence_sensor_entity_id(room_name)

    async def async_added_to_hass(self) -> None:
        """Track upstream room sources so the binary sensor follows live state."""
        await super().async_added_to_hass()
        tracked = {room_presence_entity_id(self._room_name)}
        source_entity = self.coordinator.presence.room_sensors().get(self._room_name)
        if source_entity:
            tracked.add(source_entity)
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                list(tracked),
                self._async_handle_source_change,
            )
        )

    @property
    def is_on(self) -> bool:
        """Return the resolved room presence state."""
        source_entity = self.coordinator.presence.room_sensors().get(self._room_name)
        if source_entity:
            source_state = self.hass.states.get(source_entity)
            if source_state is not None and source_state.state == "on":
                return True
            if source_entity.startswith("binary_sensor.room_"):
                return False
        return self.coordinator.controls.room_presence(self._room_name)

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | None]:
        """Expose which source currently drives the resolved room state."""
        source_entity = self.coordinator.presence.room_sensors().get(self._room_name)
        return {
            "room": self._room_name,
            "source_entity_id": source_entity,
            "fallback_switch": room_presence_entity_id(self._room_name),
            "resolved_from": (
                "real_room_sensor"
                if source_entity and source_entity.startswith("binary_sensor.room_")
                else "herald_fallback_switch"
            ),
        }

    @callback
    def _async_handle_source_change(self, event: Event) -> None:
        """Refresh when an upstream room entity changes."""
        self.async_write_ha_state()
