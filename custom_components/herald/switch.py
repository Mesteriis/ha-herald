"""Switch platform for Herald-owned runtime controls."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DOMAIN, topology_signal
from .controls import HeraldControlSpec
from .entity import HeraldCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Herald switch controls from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    known_entity_ids = {
        spec.entity_id
        for spec in coordinator.controls.build_specs_for_platform("switch")
    }
    async_add_entities(
        HeraldSwitchEntity(coordinator, entry, spec)
        for spec in coordinator.controls.build_specs_for_platform("switch")
    )

    @callback
    def _async_handle_topology_change() -> None:
        new_specs = [
            spec
            for spec in coordinator.controls.build_specs_for_platform("switch")
            if spec.entity_id not in known_entity_ids
        ]
        if not new_specs:
            return
        known_entity_ids.update(spec.entity_id for spec in new_specs)
        async_add_entities(HeraldSwitchEntity(coordinator, entry, spec) for spec in new_specs)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            topology_signal(entry.entry_id),
            _async_handle_topology_change,
        )
    )


class HeraldSwitchEntity(HeraldCoordinatorEntity, SwitchEntity):
    """One Herald-owned runtime switch."""

    _attr_has_entity_name = False

    def __init__(self, coordinator, entry: ConfigEntry, spec: HeraldControlSpec) -> None:
        super().__init__(coordinator)
        self._spec = spec
        self._attr_unique_id = f"{entry.entry_id}_{spec.object_id}"
        self._attr_icon = spec.icon
        self._attr_entity_category = spec.entity_category
        if spec.translation_key:
            self._attr_translation_key = spec.translation_key
            self._attr_translation_placeholders = dict(spec.translation_placeholders)
        else:
            self._attr_name = spec.name
        self.entity_id = spec.entity_id

    @property
    def is_on(self) -> bool:
        """Return the current switch state."""
        return bool(self.coordinator.controls.value(self._spec.key, self._spec.default))

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the control."""
        await self.coordinator.async_set_control_value(self._spec.key, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the control."""
        await self.coordinator.async_set_control_value(self._spec.key, False)
