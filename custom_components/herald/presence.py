"""Presence and quiet-hours helpers for Herald."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AWAY_CHANNELS,
    CONF_FAMILY_GROUP,
    CONF_HOME_MODE_ENTITY,
    CONF_NOBODY_HOME_ENTITY,
    CONF_ROOM_SENSORS,
    DEFAULT_ROOM_SENSORS,
)
from .controls import room_presence_entity_id
from .discovery import _infer_room_from_state, _iter_domain_states, _load_media_player_rooms, _looks_like_tv
from .models import HeraldConfig, NotificationContext, PresenceSnapshot
from .request import HeraldRequest

if TYPE_CHECKING:
    from .controls import HeraldControlManager

ROOM_ALIASES: dict[str, str] = {
    "gostinaia": "living_room",
    "гостиная": "living_room",
    "livingroom": "living_room",
    "spalnia": "bedroom",
    "спальня": "bedroom",
    "kukhnia": "kitchen",
    "кухня": "kitchen",
    "vannaia": "bathroom",
    "ванная": "bathroom",
    "kabinet": "office",
    "кабинет": "office",
    "туалет": "tualet",
}
INACTIVE_TV_STATES: set[str] = {"off", "idle", "standby", "unavailable", "unknown"}
_MEDIA_PLAYER_ROOM_REFRESH_SECONDS = 60


class PresenceResolver:
    """Resolve household presence, room routing, and quiet-hours state."""

    def __init__(self, hass: HomeAssistant, config: HeraldConfig) -> None:
        self._hass = hass
        self._config = config
        self._controls: HeraldControlManager | None = None
        self._media_player_rooms: dict[str, str] = {}
        self._media_player_rooms_refresh_at = 0.0
        self._media_player_rooms_lock = asyncio.Lock()

    def attach_controls(self, controls: HeraldControlManager) -> None:
        """Attach Herald-owned runtime controls for fallback room state."""
        self._controls = controls

    def snapshot(self) -> PresenceSnapshot:
        """Read current HA presence for configuration inspection without discovery or I/O."""
        return self._resolve_presence(explicit_room=None)

    async def async_resolve(self, context: NotificationContext) -> PresenceSnapshot:
        """Return the presence snapshot for the current notification context."""
        await self._async_refresh_media_player_rooms()
        return self._resolve_presence(explicit_room=coerce_room(context.room))

    async def async_resolve_from_request(self, request: HeraldRequest) -> PresenceSnapshot:
        """Return the presence snapshot for a thin Herald request."""
        explicit_room = _coerce_room(
            (request.context or {}).get("room") if request.context else None
        ) or coerce_room(
            (request.context or {}).get("room_hint") if request.context else None
        ) or coerce_room(
            (request.context or {}).get("room_name") if request.context else None
        ) or coerce_room(request.legacy_room)
        await self._async_refresh_media_player_rooms()
        return self._resolve_presence(explicit_room=explicit_room)

    def away_channels(self) -> list[str]:
        """Return configured away-only channels."""
        return list(self._config.presence.get(CONF_AWAY_CHANNELS, []))

    def room_sensors(self) -> dict[str, str]:
        """Return known room presence entities with Herald switch fallbacks."""
        configured = {
            **dict(DEFAULT_ROOM_SENSORS),
            **dict(self._config.presence.get(CONF_ROOM_SENSORS, {})),
        }
        configured = {
            canonical_room_name(room_name): entity_id
            for room_name, entity_id in configured.items()
        }
        configured_by_entity = {
            entity_id: room_name
            for room_name, entity_id in configured.items()
        }
        discovered: dict[str, str] = {}

        def _priority(entity_id: str) -> int:
            if entity_id.endswith("_presence"):
                return 2
            if entity_id.endswith("_occupied"):
                return 1
            return 0

        for state in self._hass.states.async_all("binary_sensor"):
            entity_id = state.entity_id
            if not entity_id.startswith("binary_sensor.room_"):
                continue
            slug = entity_id.removeprefix("binary_sensor.room_")
            if slug.endswith("_presence"):
                room_name = slug.removesuffix("_presence")
            elif slug.endswith("_occupied"):
                room_name = slug.removesuffix("_occupied")
            else:
                continue
            canonical_room = configured_by_entity.get(entity_id) or canonical_room_name(room_name)
            if canonical_room in configured:
                continue
            current_entity = discovered.get(canonical_room)
            if current_entity is None or _priority(entity_id) > _priority(current_entity):
                discovered[canonical_room] = entity_id

        combined = {**configured, **discovered}
        for room_name in set(configured) | set(discovered):
            fallback_entity = room_presence_entity_id(room_name)
            current_state = self._hass.states.get(combined.get(room_name, ""))
            if current_state is not None and current_state.state not in {"unknown", "unavailable"}:
                continue
            combined[room_name] = fallback_entity
        return combined

    def in_quiet_hours(self) -> bool:
        """Public quiet-hours evaluation for routing and context."""
        return self._in_quiet_hours()

    def _resolve_presence(self, *, explicit_room: str | None) -> PresenceSnapshot:
        presence_cfg = self._config.presence
        family_group = str(presence_cfg.get(CONF_FAMILY_GROUP, "group.family"))
        nobody_entity = str(presence_cfg.get(CONF_NOBODY_HOME_ENTITY, "binary_sensor.nobody_home"))
        home_mode_entity = str(presence_cfg.get(CONF_HOME_MODE_ENTITY, "sensor.home_mode"))

        people_home: list[str] = []
        group_state = self._hass.states.get(family_group)
        if group_state and (members := group_state.attributes.get("entity_id")):
            person_states = [self._hass.states.get(entity_id) for entity_id in members]
            for entity_id, state in zip(members, person_states, strict=False):
                if state is not None and state.state == "home":
                    people_home.append(entity_id)
        else:
            person_states = list(self._hass.states.async_all("person"))
            for state in person_states:
                if state.state == "home":
                    people_home.append(state.entity_id)

        nobody_state = self._hass.states.get(nobody_entity)
        if nobody_state is not None and nobody_state.state in {"on", "off"}:
            nobody_home = nobody_state.state == "on"
        else:
            nobody_home = not people_home

        home_mode_state = self._hass.states.get(home_mode_entity)
        if home_mode_state is not None and home_mode_state.state not in {"unknown", "unavailable"}:
            home_mode = home_mode_state.state
        elif nobody_home:
            home_mode = "away"
        else:
            home_mode = "home"

        room_sensors = self.room_sensors()
        occupied_rooms = [
            room_name
            for room_name, entity_id in room_sensors.items()
            if self._room_entity_is_on(room_name, entity_id)
        ]
        if not presence_cfg.get("occupied_room_routing", False):
            for room_name in self._active_tv_rooms():
                if room_name not in occupied_rooms:
                    occupied_rooms.append(room_name)
        primary_room = explicit_room or (occupied_rooms[0] if occupied_rooms else None)

        return PresenceSnapshot(
            people_home=people_home,
            nobody_home=nobody_home,
            absence_confirmed=bool(
                nobody_state is not None and nobody_state.state == "on"
                and person_states
                and all(state is not None and state.state not in {"home", "unknown", "unavailable"} for state in person_states)
            ),
            home_mode=home_mode,
            occupied_rooms=occupied_rooms,
            primary_room=primary_room,
            quiet_hours=self._in_quiet_hours(),
        )

    def _room_entity_is_on(self, room_name: str, entity_id: str) -> bool:
        """Return True when a real or Herald-owned room presence entity is active."""
        state = self._hass.states.get(entity_id)
        if state is not None and state.state == "on":
            return True
        if entity_id.startswith("binary_sensor.room_"):
            return False
        return bool(self._controls and self._controls.room_presence(room_name))

    async def _async_refresh_media_player_rooms(self) -> None:
        """Load storage mappings off the event loop and cache them briefly."""
        config = getattr(self._hass, "config", None)
        if config is None or not hasattr(config, "path"):
            return
        async with self._media_player_rooms_lock:
            if asyncio.get_running_loop().time() < self._media_player_rooms_refresh_at:
                return
            self._media_player_rooms = await self._hass.async_add_executor_job(
                _load_media_player_rooms,
                Path(config.path(".storage/core.entity_registry")),
                Path(config.path(".storage/core.device_registry")),
            )
            self._media_player_rooms_refresh_at = (
                asyncio.get_running_loop().time() + _MEDIA_PLAYER_ROOM_REFRESH_SECONDS
            )

    def _active_tv_rooms(self) -> list[str]:
        """Return active TV rooms using the cached registry mapping."""
        active_rooms: list[str] = []
        for entity_id, state in _iter_domain_states(self._hass, "media_player"):
            if not _looks_like_tv(entity_id, state):
                continue
            room_name = self._media_player_rooms.get(entity_id) or _infer_room_from_state(entity_id, state)
            if room_name is None:
                continue
            state_value = str(getattr(state, "state", "")).strip().lower()
            if state_value in INACTIVE_TV_STATES:
                continue
            if room_name not in active_rooms:
                active_rooms.append(room_name)
        return active_rooms

    def _in_quiet_hours(self) -> bool:
        """Evaluate the configured quiet-hours interval."""
        start_text = self._config.quiet_hours.start
        end_text = self._config.quiet_hours.end
        start = datetime.strptime(start_text, "%H:%M").time()
        end = datetime.strptime(end_text, "%H:%M").time()
        now_local = dt_util.now().time()
        if start <= end:
            return start <= now_local <= end
        return now_local >= start or now_local <= end

def coerce_room(value: Any) -> str | None:
    if value is None:
        return None
    return canonical_room_name(str(value))


def canonical_room_name(value: str) -> str | None:
    text = value.strip().lower().replace(" ", "_")
    if not text:
        return None
    return ROOM_ALIASES.get(text, text)


def _coerce_room(value: Any) -> str | None:
    return coerce_room(value)


def _canonical_room_name(value: str) -> str | None:
    return canonical_room_name(value)
