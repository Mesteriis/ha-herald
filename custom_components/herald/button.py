"""Button platform for Herald-owned runtime test actions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up Herald button controls from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    known_entity_ids = {
        spec.entity_id
        for spec in coordinator.controls.build_specs_for_platform("button")
    }
    async_add_entities(
        HeraldButtonEntity(coordinator, entry, spec)
        for spec in coordinator.controls.build_specs_for_platform("button")
    )

    @callback
    def _async_handle_topology_change() -> None:
        new_specs = [
            spec
            for spec in coordinator.controls.build_specs_for_platform("button")
            if spec.entity_id not in known_entity_ids
        ]
        if not new_specs:
            return
        known_entity_ids.update(spec.entity_id for spec in new_specs)
        async_add_entities(HeraldButtonEntity(coordinator, entry, spec) for spec in new_specs)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            topology_signal(entry.entry_id),
            _async_handle_topology_change,
        )
    )


class HeraldButtonEntity(HeraldCoordinatorEntity, ButtonEntity):
    """One Herald-owned runtime button."""

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

    async def async_press(self) -> None:
        """Execute the bound Herald test action."""
        await self.coordinator.async_press_control_button(self._spec.key)
