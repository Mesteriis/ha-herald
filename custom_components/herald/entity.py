"""Shared entity helpers for Herald."""

from __future__ import annotations

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
            "manufacturer": "OpenAI / Codex",
            "model": "Herald Notification Center",
            "entry_type": "service",
        }
