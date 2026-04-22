"""Select platform for Herald-owned runtime controls."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
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
    """Set up Herald select controls from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    known_entity_ids = {
        spec.entity_id
        for spec in coordinator.controls.build_specs_for_platform("select")
    }
    async_add_entities(
        HeraldSelectEntity(coordinator, entry, spec)
        for spec in coordinator.controls.build_specs_for_platform("select")
    )

    @callback
    def _async_handle_topology_change() -> None:
        new_specs = [
            spec
            for spec in coordinator.controls.build_specs_for_platform("select")
            if spec.entity_id not in known_entity_ids
        ]
        if not new_specs:
            return
        known_entity_ids.update(spec.entity_id for spec in new_specs)
        async_add_entities(HeraldSelectEntity(coordinator, entry, spec) for spec in new_specs)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            topology_signal(entry.entry_id),
            _async_handle_topology_change,
        )
    )


class HeraldSelectEntity(HeraldCoordinatorEntity, SelectEntity):
    """One Herald-owned runtime select."""

    _attr_has_entity_name = False

    def __init__(self, coordinator, entry: ConfigEntry, spec: HeraldControlSpec) -> None:
        super().__init__(coordinator)
        self._spec = spec
        self._attr_unique_id = f"{entry.entry_id}_{spec.object_id}"
        self._attr_icon = spec.icon
        self._attr_entity_category = spec.entity_category
        self._attr_options = list(spec.options)
        if spec.translation_key:
            self._attr_translation_key = spec.translation_key
            self._attr_translation_placeholders = dict(spec.translation_placeholders)
        else:
            self._attr_name = spec.name
        self.entity_id = spec.entity_id

    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        return str(self.coordinator.controls.value(self._spec.key, self._spec.default))

    @property
    def options(self) -> list[str]:
        """Return live options so new characters appear without a reload."""
        spec = self.coordinator.controls.spec(self._spec.key)
        if spec is None:
            return list(self._spec.options)
        return list(spec.options)

    async def async_select_option(self, option: str) -> None:
        """Select a new runtime option."""
        await self.coordinator.async_set_control_value(self._spec.key, option)

    @callback
    def _handle_coordinator_update(self) -> None:
        spec = self.coordinator.controls.spec(self._spec.key)
        if spec is not None:
            self._attr_options = list(spec.options)
        super()._handle_coordinator_update()
