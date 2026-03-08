"""Context building for Herald requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant

from .const import CONF_HOME_MODE_ENTITY
from .controls import HeraldControlManager
from .models import HeraldConfig
from .presence import PresenceResolver, canonical_room_name, coerce_room
from .request import HeraldRequest


@dataclass(slots=True)
class ResolvedUserProfile:
    """Resolved user preferences from Home Assistant helper entities."""

    person_entity_id: str
    slug: str
    name: str
    language: str = "ru"
    character: str | None = None
    silent: bool = False
    home: bool = False
    current_room: str | None = None
    room_source: str | None = None
    source_entity_id: str | None = None


@dataclass(slots=True)
class RuntimeContext:
    """Resolved runtime context used by the Herald pipeline."""

    people_home: list[str] = field(default_factory=list)
    device_trackers_home: list[str] = field(default_factory=list)
    occupied_rooms: list[str] = field(default_factory=list)
    primary_room: str | None = None
    quiet_hours: bool = False
    home_mode: str = "home"
    activity: str = "idle"
    room_sensors: dict[str, str] = field(default_factory=dict)
    users: list[ResolvedUserProfile] = field(default_factory=list)

    def room_for_user(self, identifier: str | None) -> str | None:
        """Return a resolved room for one user identifier when available."""
        if not identifier:
            return None
        normalized = identifier.split(".", maxsplit=1)[1] if "." in identifier else identifier
        for item in self.users:
            if identifier in {item.person_entity_id, item.slug} or normalized == item.slug:
                return item.current_room
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for traces and diagnostics."""
        return {
            "people_home": list(self.people_home),
            "device_trackers_home": list(self.device_trackers_home),
            "occupied_rooms": list(self.occupied_rooms),
            "primary_room": self.primary_room,
            "quiet_hours": self.quiet_hours,
            "home_mode": self.home_mode,
            "activity": self.activity,
            "room_sensors": dict(self.room_sensors),
            "user_rooms": {
                item.slug: item.current_room
                for item in self.users
                if item.current_room is not None
            },
            "users": [
                {
                    "person_entity_id": item.person_entity_id,
                    "slug": item.slug,
                    "name": item.name,
                    "language": item.language,
                    "character": item.character,
                    "silent": item.silent,
                    "home": item.home,
                    "current_room": item.current_room,
                    "room_source": item.room_source,
                    "source_entity_id": item.source_entity_id,
                }
                for item in self.users
            ],
        }


class HeraldContextBuilder:
    """Resolve user, room, and activity context from Home Assistant state."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: HeraldConfig,
        presence: PresenceResolver,
        controls: HeraldControlManager,
    ) -> None:
        self._hass = hass
        self._config = config
        self._presence = presence
        self._controls = controls

    async def async_build(self, request: HeraldRequest) -> RuntimeContext:
        """Resolve runtime context for one Herald request."""
        presence = await self._presence.async_resolve_from_request(request)
        room_sensors = self._presence.room_sensors()
        users = self._resolve_user_profiles(presence, room_sensors=room_sensors)
        device_trackers_home = self._resolve_device_trackers_home()
        activity = self._resolve_activity(room=presence.primary_room)
        home_mode = presence.home_mode
        if state := self._hass.states.get(str(self._config.presence.get(CONF_HOME_MODE_ENTITY, ""))):
            home_mode = state.state
        primary_room = presence.primary_room or self._resolve_primary_room_from_users(users)
        return RuntimeContext(
            people_home=list(presence.people_home),
            device_trackers_home=device_trackers_home,
            occupied_rooms=list(presence.occupied_rooms),
            primary_room=primary_room,
            quiet_hours=presence.quiet_hours,
            home_mode=home_mode,
            activity=activity,
            room_sensors=room_sensors,
            users=users,
        )

    def _resolve_user_profiles(
        self,
        presence,
        *,
        room_sensors: dict[str, str],
    ) -> list[ResolvedUserProfile]:
        people: list[ResolvedUserProfile] = []
        occupied_rooms = list(presence.occupied_rooms)
        people_home = list(presence.people_home)
        for state in self._hass.states.async_all("person"):
            slug = state.entity_id.split(".", maxsplit=1)[1]
            user_cfg = self._config.users.get(slug)
            name = str(state.attributes.get("friendly_name") or slug.replace("_", " ").title())
            language = self._controls.user_language(slug, default="ru")
            character = self._controls.user_character(slug, default=None)
            silent = self._controls.user_silent(slug)
            current_room, room_source, source_entity_id = self._resolve_user_room(
                state,
                user_cfg=user_cfg,
                occupied_rooms=occupied_rooms,
                room_sensors=room_sensors,
                people_home=people_home,
                fallback_room=presence.primary_room,
            )
            people.append(
                ResolvedUserProfile(
                    person_entity_id=state.entity_id,
                    slug=slug,
                    name=name,
                    language=language or "ru",
                    character=character,
                    silent=silent,
                    home=state.state == "home",
                    current_room=current_room,
                    room_source=room_source,
                    source_entity_id=source_entity_id,
                )
            )
        return people

    def _resolve_device_trackers_home(self) -> list[str]:
        return [
            state.entity_id
            for state in self._hass.states.async_all("device_tracker")
            if state.state == "home"
        ]

    def _resolve_activity(self, *, room: str | None) -> str:
        room_hint = f"_{room}" if room else ""
        media_states = [
            state
            for state in self._hass.states.async_all("media_player")
            if state.state in {"playing", "buffering", "paused"}
        ]
        if room:
            for state in media_states:
                lowered = state.entity_id.lower()
                if room in lowered or room_hint in lowered:
                    return "media_playing"
        if media_states:
            return "media_playing"
        if self._presence.in_quiet_hours():
            return "sleeping"
        return "idle"

    def _resolve_primary_room_from_users(self, users: list[ResolvedUserProfile]) -> str | None:
        rooms = {item.current_room for item in users if item.home and item.current_room}
        if len(rooms) == 1:
            return next(iter(rooms))
        return None

    def _resolve_user_room(
        self,
        person_state,
        *,
        user_cfg,
        occupied_rooms: list[str],
        room_sensors: dict[str, str],
        people_home: list[str],
        fallback_room: str | None,
    ) -> tuple[str | None, str | None, str | None]:
        known_rooms = set(room_sensors)
        if user_cfg and user_cfg.room_entity:
            room = self._resolve_room_from_entity(user_cfg.room_entity, known_rooms)
            if room:
                return room, f"config_room_entity:{user_cfg.room_entity}", user_cfg.room_entity

        if room := self._resolve_room_from_state(person_state, known_rooms):
            return room, "person_attributes", person_state.entity_id

        tracker_entities = list(person_state.attributes.get("device_trackers") or [])
        source_entity = person_state.attributes.get("source")
        if source_entity:
            tracker_entities.insert(0, source_entity)

        for entity_id in dict.fromkeys(entity_id for entity_id in tracker_entities if entity_id):
            if room := self._resolve_room_from_entity(entity_id, known_rooms):
                return room, f"device_tracker:{entity_id}", entity_id

        if person_state.state == "home" and len(occupied_rooms) == 1:
            return occupied_rooms[0], "single_occupied_room", None

        if (
            person_state.state == "home"
            and fallback_room
            and len(people_home) == 1
        ):
            return fallback_room, "single_home_user_primary_room", None

        return None, None, source_entity if isinstance(source_entity, str) else None

    def _resolve_room_from_entity(
        self,
        entity_id: str,
        known_rooms: set[str],
    ) -> str | None:
        state = self._hass.states.get(entity_id)
        if state is None:
            return self._match_room_from_text(entity_id, known_rooms)
        return self._resolve_room_from_state(state, known_rooms) or self._match_room_from_text(
            f"{entity_id} {state.attributes.get('friendly_name', '')}",
            known_rooms,
        )

    def _resolve_room_from_state(
        self,
        state,
        known_rooms: set[str],
    ) -> str | None:
        for key in ("room", "room_name", "current_room", "area", "area_name"):
            room = self._coerce_known_room(state.attributes.get(key), known_rooms)
            if room:
                return room
        room = self._coerce_known_room(state.state, known_rooms)
        if room:
            return room
        friendly_name = state.attributes.get("friendly_name")
        return self._match_room_from_text(friendly_name, known_rooms)

    def _coerce_known_room(
        self,
        value: Any,
        known_rooms: set[str],
    ) -> str | None:
        room = coerce_room(value)
        if room is None:
            return None
        if not known_rooms or room in known_rooms:
            return room
        return None

    def _match_room_from_text(
        self,
        value: Any,
        known_rooms: set[str],
    ) -> str | None:
        if value is None:
            return None
        lowered = str(value).strip().lower().replace("-", " ")
        if not lowered:
            return None
        candidates: dict[str, set[str]] = {}
        for room_name in known_rooms:
            variants = {
                room_name,
                room_name.replace("_", " "),
                canonical_room_name(room_name) or room_name,
            }
            if room_name == "living_room":
                variants.update({"living room", "gostinaia", "гостиная"})
            if room_name == "bedroom":
                variants.update({"spalnia", "спальня"})
            if room_name == "kitchen":
                variants.update({"kukhnia", "кухня"})
            if room_name == "bathroom":
                variants.update({"vannaia", "ванная"})
            if room_name == "office":
                variants.update({"kabinet", "кабинет"})
            if room_name == "tualet":
                variants.update({"туалет"})
            candidates[room_name] = variants

        for room_name, variants in candidates.items():
            if any(variant in lowered for variant in variants):
                return room_name
        return None
