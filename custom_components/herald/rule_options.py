"""Read-only catalogs for rule targets, shared by the editor and admission checks."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .models import HeraldConfig
from .policy_rules import normalize_user
from .presence import PresenceResolver, canonical_room_name


def rule_options(hass: HomeAssistant, config: HeraldConfig, presence: PresenceResolver) -> dict[str, list[dict[str, str]]]:
    """Describe existing people and known local routing rooms without discovering secrets."""
    users: dict[str, str] = {}
    for key, user in config.users.items():
        if entity_id := normalize_user(key):
            users[entity_id] = user.name
    for state in hass.states.async_all("person"):
        users[normalize_user(state.entity_id)] = str(state.attributes.get("friendly_name") or state.entity_id)
    rooms = set(presence.room_sensors())
    for channel in config.channels.values():
        if channel.room:
            rooms.add(channel.room)
        for field in ("room_targets", "audio_targets", "notify_services"):
            mapping = channel.data.get(field)
            if isinstance(mapping, dict):
                rooms.update(str(name) for name in mapping)
    room_names = {room for name in rooms if name and (room := canonical_room_name(name))}
    # 'auto' and 'all' are legacy routing directives, never concrete room targets.
    room_names -= {"auto", "all"}
    return {
        "user_options": [{"value": value, "label": label} for value, label in sorted(users.items())],
        "room_options": [{"value": room, "label": room.replace("_", " ").title()} for room in sorted(room_names)],
    }
