"""Presence and quiet-hours helpers for Herald."""

from __future__ import annotations

from datetime import datetime

from homeassistant.core import HomeAssistant

from .const import (
    CONF_AWAY_CHANNELS,
    CONF_FAMILY_GROUP,
    CONF_HOME_MODE_ENTITY,
    CONF_NOBODY_HOME_ENTITY,
    CONF_ROOM_SENSORS,
)
from .models import HeraldConfig, NotificationContext, PresenceSnapshot


class PresenceResolver:
    """Resolve household presence, room routing, and quiet-hours state."""

    def __init__(self, hass: HomeAssistant, config: HeraldConfig) -> None:
        self._hass = hass
        self._config = config

    async def async_resolve(self, context: NotificationContext) -> PresenceSnapshot:
        """Return the presence snapshot for the current notification."""
        presence_cfg = self._config.presence
        family_group = str(presence_cfg.get(CONF_FAMILY_GROUP, "group.family"))
        nobody_entity = str(
            presence_cfg.get(CONF_NOBODY_HOME_ENTITY, "binary_sensor.nobody_home")
        )
        home_mode_entity = str(presence_cfg.get(CONF_HOME_MODE_ENTITY, "sensor.home_mode"))

        group_state = self._hass.states.get(family_group)
        people_home: list[str] = []
        if group_state and (members := group_state.attributes.get("entity_id")):
            for entity_id in members:
                state = self._hass.states.get(entity_id)
                if state is not None and state.state == "home":
                    people_home.append(entity_id)
        else:
            for state in self._hass.states.async_all("person"):
                if state.state == "home":
                    people_home.append(state.entity_id)

        nobody_home = False
        nobody_state = self._hass.states.get(nobody_entity)
        if nobody_state is not None:
            nobody_home = nobody_state.state == "on"
        elif people_home:
            nobody_home = False
        else:
            nobody_home = True

        home_mode_state = self._hass.states.get(home_mode_entity)
        home_mode = home_mode_state.state if home_mode_state is not None else "home"

        room_sensors = dict(presence_cfg.get(CONF_ROOM_SENSORS, {}))
        occupied_rooms = [
            room_name
            for room_name, entity_id in room_sensors.items()
            if (state := self._hass.states.get(entity_id)) is not None and state.state == "on"
        ]
        explicit_room = context.room.lower().replace(" ", "_") if context.room else None
        primary_room = explicit_room or (occupied_rooms[0] if occupied_rooms else None)

        return PresenceSnapshot(
            people_home=people_home,
            nobody_home=nobody_home,
            home_mode=home_mode,
            occupied_rooms=occupied_rooms,
            primary_room=primary_room,
            quiet_hours=self._in_quiet_hours(),
        )

    def away_channels(self) -> list[str]:
        """Return configured away-only channels."""
        return list(self._config.presence.get(CONF_AWAY_CHANNELS, []))

    def _in_quiet_hours(self) -> bool:
        """Evaluate the configured quiet-hours interval."""
        start_text = self._config.quiet_hours.start
        end_text = self._config.quiet_hours.end
        start = datetime.strptime(start_text, "%H:%M").time()
        end = datetime.strptime(end_text, "%H:%M").time()
        now_local = datetime.now().time()
        if start <= end:
            return start <= now_local <= end
        return now_local >= start or now_local <= end
