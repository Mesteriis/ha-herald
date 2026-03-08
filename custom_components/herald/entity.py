"""Shared entity helpers for Herald."""

from __future__ import annotations

try:
    from homeassistant.helpers.device_registry import DeviceEntryType
except Exception:  # pragma: no cover - lightweight test stubs may not expose device_registry
    DeviceEntryType = None

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME


class HeraldCoordinatorEntity(CoordinatorEntity):
    """Base Herald entity bound to the coordinator."""

    _attr_has_entity_name = True

    @property
    def device_info(self):  # type: ignore[override]
        """Return shared device info for Herald entities."""
        return {
            "identifiers": {(DOMAIN, "notification_center")},
            "name": NAME,
            "manufacturer": "Aleksandr Meshchryakov",
            "model": "Herald Notification Center",
            "entry_type": DeviceEntryType.SERVICE if DeviceEntryType is not None else "service",
        }
