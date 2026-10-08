"""Resolve existing Herald control entities without creating registry entries."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .controls import HeraldControlManager


def resolve_control_entities(
    hass: HomeAssistant, entry_id: str, controls: HeraldControlManager,
) -> dict[str, str]:
    """Map configurable control keys to their current registered entity IDs.

    HA stores the loaded registry under ``entity_registry``. Read it directly:
    its public ``async_get(hass)`` accessor can create a missing registry. State
    availability and registry disablement do not change an entity's identity;
    callers can display unavailable controls without guessing a replacement.
    """
    registry = getattr(hass, "data", {}).get("entity_registry")
    if registry is None or not hasattr(registry, "entities"):
        return {}

    entities: dict[str, str] = {}
    for spec in controls.build_specs():
        if spec.platform not in {"switch", "select", "number"}:
            continue
        unique_id = f"{entry_id}_{spec.object_id}"
        entity_id = registry.async_get_entity_id(spec.platform, DOMAIN, unique_id)
        if entity_id is None:
            continue
        entry = registry.async_get(entity_id)
        if entry is not None and entry.config_entry_id == entry_id:
            entities[spec.key] = entry.entity_id
    return entities
