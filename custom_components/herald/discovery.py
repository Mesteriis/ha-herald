"""Runtime channel discovery helpers for Herald."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from homeassistant.core import HomeAssistant

LEGACY_MOBILE_SERVICES: dict[str, str] = {
    "mobile_iphone_aleksander": "notify.mobile_app_iphone_aleksander",
    "mobile_iphone_vi": "notify.mobile_app_iphone_vi",
    "mobile_ipad": "notify.mobile_app_ipad",
    "mobile_macbook": "notify.mobile_app_macbook",
    "mobile_aleksandrs_macbook_pro": "notify.mobile_app_aleksandrs_macbook_pro",
}

VOICE_ROOM_TARGETS: dict[str, str] = {
    "living_room": "media_player.yandex_station_x11jdn200bwyse",
    "bedroom": "media_player.yandex_station_lp000000000000472311000094e3cf79",
    "bathroom": "media_player.yandex_station_lp0000000000006590730000ef14cd97",
    "kitchen": "media_player.yandex_station_lb00000000000003070000004facb013",
}
ROOM_ALIASES: dict[str, str] = {
    "gostinaia": "living_room",
    "living_room": "living_room",
    "living room": "living_room",
    "гостиная": "living_room",
    "spalnia": "bedroom",
    "bedroom": "bedroom",
    "спальня": "bedroom",
    "kukhnia": "kitchen",
    "kitchen": "kitchen",
    "кухня": "kitchen",
    "vannaia": "bathroom",
    "bathroom": "bathroom",
    "ванная": "bathroom",
    "kabinet": "office",
    "office": "office",
    "кабинет": "office",
}
TV_HINTS: tuple[str, ...] = ("tv", "appletv", "apple tv", "chromecast", "google tv", "shield", "fire tv")
HOMEPOD_HINTS: tuple[str, ...] = ("homepod",)


def discover_runtime_channels(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    """Discover useful channels from the live Home Assistant runtime."""
    channels: dict[str, dict[str, Any]] = {}
    services = hass.services.async_services()
    _, voice_channel_payload = _discover_room_audio_targets(hass)

    if voice_channel_payload is not None:
        channels["voice_auto"] = voice_channel_payload

    for service_name in sorted(services.get("notify", {})):
        if not service_name.startswith("mobile_app_"):
            continue
        channel_name = service_name.removeprefix("mobile_app_")
        channels[f"mobile_{channel_name}"] = {
            "type": "mobile_app",
            "service": f"notify.{service_name}",
            "min_level": "info",
        }

    for channel_name, service_name in LEGACY_MOBILE_SERVICES.items():
        channels.setdefault(
            channel_name,
            {
                "type": "mobile_app",
                "service": service_name,
                "min_level": "info",
            },
        )

    if telegram_channel := _discover_telegram_channel(hass, services):
        channels["telegram_default"] = telegram_channel

    channels.update(_discover_tv_channels(hass))

    return channels


def _discover_room_audio_targets(
    hass: HomeAssistant,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any] | None]:
    """Discover room-level audio targets and build the conceptual voice_auto channel."""
    media_player_rooms = _load_media_player_rooms(
        Path(hass.config.path(".storage/core.entity_registry")),
        Path(hass.config.path(".storage/core.device_registry")),
    )
    tts_entity_id = _discover_tts_entity(hass)
    room_targets: dict[str, list[dict[str, Any]]] = {}

    for room_name, entity_id in VOICE_ROOM_TARGETS.items():
        if hass.states.get(entity_id) is None:
            continue
        room_targets.setdefault(room_name, []).append(
            {
                "kind": "alisa",
                "entity_id": entity_id,
                "service": "tts.yandex_station_say",
                "priority": 1,
            }
        )

    for entity_id, state in _iter_domain_states(hass, "media_player"):
        room_name = media_player_rooms.get(entity_id) or _infer_room_from_state(entity_id, state)
        if room_name is None:
            continue
        if _looks_like_homepod(entity_id, state) and tts_entity_id is not None:
            room_targets.setdefault(room_name, []).append(
                {
                    "kind": "homepod",
                    "entity_id": entity_id,
                    "service": "tts.speak",
                    "engine_entity_id": tts_entity_id,
                    "active_only": False,
                    "priority": 2,
                }
            )
            continue
        if _looks_like_tv(entity_id, state) and tts_entity_id is not None:
            room_targets.setdefault(room_name, []).append(
                {
                    "kind": "tv",
                    "entity_id": entity_id,
                    "service": "tts.speak",
                    "engine_entity_id": tts_entity_id,
                    "active_only": True,
                    "announce": True,
                    "priority": 3,
                }
            )

    sorted_targets = {
        room_name: sorted(
            targets,
            key=lambda item: (
                int(item.get("priority", 99)),
                str(item.get("entity_id", "")),
            ),
        )
        for room_name, targets in room_targets.items()
        if targets
    }
    if not sorted_targets:
        return {}, None

    fallback_target = next(
        (
            target["entity_id"]
            for _, targets in sorted(sorted_targets.items())
            for target in targets
        ),
        None,
    )
    if fallback_target is None:
        return {}, None

    yandex_available = any(
        target.get("kind") == "alisa"
        for targets in sorted_targets.values()
        for target in targets
    )
    voice_group = "group.voice_notification_targets" if hass.states.get("group.voice_notification_targets") else None
    channel_service = "tts.yandex_station_say" if (voice_group or yandex_available) else "tts.speak"
    channel_entity_id = voice_group or fallback_target
    voice_payload = {
        "type": "tts",
        "service": channel_service,
        "entity_id": channel_entity_id,
        "min_level": "info",
        "data": {
            "room_targets": {
                room_name: targets[0]["entity_id"]
                for room_name, targets in sorted_targets.items()
            },
            "audio_targets": sorted_targets,
        },
    }
    if tts_entity_id is not None:
        voice_payload["data"]["engine_entity_id"] = tts_entity_id
    return sorted_targets, voice_payload


def _discover_telegram_channel(
    hass: HomeAssistant,
    services: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Discover the current Telegram delivery settings from existing HA config."""
    if "send_message" not in services.get("telegram_bot", {}):
        return None

    secrets = _load_yaml_file(Path(hass.config.path("secrets.yaml")))
    config_entry_id = _as_text(secrets.get("telegram_bot_entry_id"))
    chat_id = _coerce_intlike(secrets.get("telegram_history_chat_id"))
    thread_id = _coerce_intlike(secrets.get("telegram_history_iot_thread_id"))

    if not config_entry_id or chat_id is None:
        storage_info = _load_telegram_from_storage(Path(hass.config.path(".storage/core.config_entries")))
        config_entry_id = config_entry_id or storage_info.get("config_entry_id")
        chat_id = chat_id if chat_id is not None else storage_info.get("chat_id")

    if not config_entry_id or chat_id is None:
        return None

    channel: dict[str, Any] = {
        "type": "telegram",
        "service": "telegram_bot.send_message",
        "chat_id": chat_id,
        "min_level": "info",
        "data": {
            "config_entry_id": config_entry_id,
        },
    }
    if thread_id is not None:
        channel["thread_id"] = thread_id
    return channel


def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from disk."""
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _load_telegram_from_storage(path: Path) -> dict[str, Any]:
    """Read the active telegram_bot entry from HA storage."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

    entries = payload.get("data", {}).get("entries", [])
    for entry in entries:
        if entry.get("domain") != "telegram_bot":
            continue
        subentries = entry.get("subentries", [])
        chat_id = None
        for subentry in subentries:
            if subentry.get("subentry_type") != "allowed_chat_ids":
                continue
            chat_id = _coerce_intlike(subentry.get("data", {}).get("chat_id"))
            if chat_id is not None:
                break
        return {
            "config_entry_id": _as_text(entry.get("entry_id")),
            "chat_id": chat_id,
        }
    return {}


def _discover_tv_channels(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    """Discover TV-capable media players and build TV delivery channels."""
    tts_entity_id = _discover_tts_entity(hass)
    if tts_entity_id is None:
        return {}

    media_player_rooms = _load_media_player_rooms(
        Path(hass.config.path(".storage/core.entity_registry")),
        Path(hass.config.path(".storage/core.device_registry")),
    )
    room_targets: dict[str, str] = {}
    fallback_target: str | None = None

    for entity_id, state in _iter_domain_states(hass, "media_player"):
        if not _looks_like_tv(entity_id, state):
            continue
        fallback_target = fallback_target or entity_id
        room_name = media_player_rooms.get(entity_id) or _infer_room_from_state(entity_id, state)
        if room_name and room_name not in room_targets:
            room_targets[room_name] = entity_id

    if fallback_target is None:
        return {}

    channels: dict[str, dict[str, Any]] = {
        "tv_auto": {
            "type": "tv",
            "service": "tts.speak",
            "entity_id": fallback_target,
            "min_level": "warning",
            "data": {
                "engine_entity_id": tts_entity_id,
                "active_only": True,
                "turn_on": False,
                "announce": True,
                "room_targets": room_targets,
            },
        }
    }
    for room_name, entity_id in sorted(room_targets.items()):
        channels[f"tv_{room_name}"] = {
            "type": "tv",
            "service": "tts.speak",
            "entity_id": entity_id,
            "room": room_name,
            "min_level": "warning",
            "data": {
                "engine_entity_id": tts_entity_id,
                "active_only": True,
                "turn_on": False,
                "announce": True,
            },
        }
    return channels


def _discover_tts_entity(hass: HomeAssistant) -> str | None:
    """Return the first usable local TTS entity."""
    preferred = "tts.google_translate_en_com"
    available = [entity_id for entity_id, _ in _iter_domain_states(hass, "tts")]
    if preferred in available:
        return preferred
    return available[0] if available else None


def _iter_domain_states(hass: HomeAssistant, domain: str) -> list[tuple[str, Any]]:
    """Iterate over states for one domain for both real HA and lightweight tests."""
    if hasattr(hass.states, "async_all"):
        return [
            (state.entity_id, state)
            for state in hass.states.async_all(domain)  # type: ignore[call-arg]
        ]
    entities = getattr(hass.states, "_entities", {})
    return [
        (entity_id, state)
        for entity_id, state in entities.items()
        if entity_id.startswith(f"{domain}.")
    ]


def _looks_like_tv(entity_id: str, state: Any) -> bool:
    text = " ".join(
        (
            entity_id,
            str(getattr(state, "attributes", {}).get("friendly_name", "")),
        )
    ).lower()
    return any(hint in text for hint in TV_HINTS)


def _looks_like_homepod(entity_id: str, state: Any) -> bool:
    """Return True when a media_player looks like a HomePod target."""
    text = " ".join(
        (
            entity_id,
            str(getattr(state, "attributes", {}).get("friendly_name", "")),
            str(getattr(state, "attributes", {}).get("model", "")),
        )
    ).lower()
    return any(hint in text for hint in HOMEPOD_HINTS)


def _infer_room_from_state(entity_id: str, state: Any) -> str | None:
    text = " ".join(
        (
            entity_id,
            str(getattr(state, "attributes", {}).get("friendly_name", "")),
        )
    ).lower()
    for alias, normalized in ROOM_ALIASES.items():
        if alias in text:
            return normalized
    return None


def _load_media_player_rooms(entity_registry_path: Path, device_registry_path: Path) -> dict[str, str]:
    """Map media_player entity ids to normalized room names via HA storage registries."""
    entity_payload = _load_json_file(entity_registry_path)
    device_payload = _load_json_file(device_registry_path)
    if not entity_payload or not device_payload:
        return {}

    devices = device_payload.get("data", {}).get("devices", [])
    device_to_area = {
        str(item.get("id")): _normalize_room_name(item.get("area_id"))
        for item in devices
        if item.get("id")
    }
    rooms: dict[str, str] = {}
    for item in entity_payload.get("data", {}).get("entities", []):
        entity_id = _as_text(item.get("entity_id"))
        if entity_id is None or not entity_id.startswith("media_player."):
            continue
        area_id = _normalize_room_name(item.get("area_id"))
        if area_id is None and item.get("device_id"):
            area_id = device_to_area.get(str(item["device_id"]))
        if area_id is not None:
            rooms[entity_id] = area_id
    return rooms


def _normalize_room_name(value: Any) -> str | None:
    text = _as_text(value)
    if text is None:
        return None
    return ROOM_ALIASES.get(text.lower(), text.lower())


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _coerce_intlike(value: Any) -> int | None:
    """Convert a string/int value to int when possible."""
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _as_text(value: Any) -> str | None:
    """Return a stripped string or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
