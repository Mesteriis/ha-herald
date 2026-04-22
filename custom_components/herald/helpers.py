"""Helper bootstrap for Herald control entities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

DEFAULT_LANGUAGE_OPTIONS = ["ru", "en", "es", "fr"]
INPUT_BOOLEAN_STORAGE_VERSION = 1
INPUT_SELECT_STORAGE_VERSION = 1
INPUT_SELECT_STORAGE_MINOR_VERSION = 2


@dataclass(slots=True)
class HeraldHelperBootstrap:
    """Summary of helper definitions ensured on disk."""

    input_booleans: list[str]
    input_selects: list[str]
    rooms: list[str]
    users: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_booleans": list(self.input_booleans),
            "input_selects": list(self.input_selects),
            "rooms": list(self.rooms),
            "users": list(self.users),
        }


class HeraldHelperManager:
    """Bootstrap Herald control helpers into Home Assistant storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._storage_root = Path(hass.config.path(".storage"))

    async def async_ensure_helpers(
        self,
        *,
        room_names: list[str],
        user_slugs: list[str],
        character_options: list[str],
    ) -> HeraldHelperBootstrap:
        """Ensure Herald helpers exist in storage for next HA load cycle."""
        return await self._hass.async_add_executor_job(
            self._ensure_helpers,
            sorted(set(room_names)),
            sorted(set(user_slugs)),
            sorted(set(character_options)) or ["hestia", "domovoy"],
        )

    def room_presence_entity(self, room_name: str) -> str:
        """Return the fallback helper entity id for a room presence sensor."""
        return f"input_boolean.herald_room_{room_name}_presence"

    def _ensure_helpers(
        self,
        room_names: list[str],
        user_slugs: list[str],
        character_options: list[str],
    ) -> HeraldHelperBootstrap:
        self._storage_root.mkdir(parents=True, exist_ok=True)
        booleans = self._load_items(self._storage_root / "input_boolean")
        selects = self._load_items(self._storage_root / "input_select")

        ensured_booleans = [
            self._upsert_boolean(booleans, "herald_channel_voice", "Herald Channel Voice", True),
            self._upsert_boolean(booleans, "herald_channel_push", "Herald Channel Push", True),
            self._upsert_boolean(booleans, "herald_channel_tv", "Herald Channel TV", True),
            self._upsert_boolean(booleans, "herald_ai_enabled", "Herald AI Enabled", True),
            self._upsert_boolean(booleans, "herald_level_info", "Herald Level Info", True),
            self._upsert_boolean(booleans, "herald_level_warning", "Herald Level Warning", True),
            self._upsert_boolean(booleans, "herald_level_critical", "Herald Level Critical", True),
            self._upsert_boolean(booleans, "herald_ai_info", "Herald AI Info", False),
            self._upsert_boolean(booleans, "herald_ai_warning", "Herald AI Warning", True),
            self._upsert_boolean(booleans, "herald_ai_critical", "Herald AI Critical", True),
        ]

        for room_name in room_names:
            ensured_booleans.append(
                self._upsert_boolean(
                    booleans,
                    f"herald_room_{room_name}_presence",
                    f"Herald Room {room_name.replace('_', ' ').title()} Presence",
                    False,
                )
            )

        ensured_selects: list[str] = []
        for user_slug in user_slugs:
            ensured_selects.append(
                self._upsert_select(
                    selects,
                    f"herald_user_{user_slug}_language",
                    f"Herald User {user_slug.replace('_', ' ').title()} Language",
                    DEFAULT_LANGUAGE_OPTIONS,
                    "ru",
                )
            )
            ensured_selects.append(
                self._upsert_select(
                    selects,
                    f"herald_user_{user_slug}_character",
                    f"Herald User {user_slug.replace('_', ' ').title()} Character",
                    character_options,
                    character_options[0],
                )
            )
            ensured_booleans.append(
                self._upsert_boolean(
                    booleans,
                    f"herald_user_{user_slug}_silent",
                    f"Herald User {user_slug.replace('_', ' ').title()} Silent",
                    False,
                )
            )

        self._write_items(
            self._storage_root / "input_boolean",
            key="input_boolean",
            version=INPUT_BOOLEAN_STORAGE_VERSION,
            items=booleans,
        )
        self._write_items(
            self._storage_root / "input_select",
            key="input_select",
            version=INPUT_SELECT_STORAGE_VERSION,
            minor_version=INPUT_SELECT_STORAGE_MINOR_VERSION,
            items=selects,
        )
        return HeraldHelperBootstrap(
            input_booleans=sorted(set(ensured_booleans)),
            input_selects=sorted(set(ensured_selects)),
            rooms=room_names,
            users=user_slugs,
        )

    def _upsert_boolean(
        self,
        items: list[dict[str, Any]],
        helper_id: str,
        name: str,
        initial: bool,
    ) -> str:
        existing = _find_item(items, helper_id)
        if existing is None:
            items.append({"id": helper_id, "name": name, "initial": initial})
        else:
            existing.setdefault("name", name)
            existing.setdefault("initial", initial)
        return f"input_boolean.{helper_id}"

    def _upsert_select(
        self,
        items: list[dict[str, Any]],
        helper_id: str,
        name: str,
        options: list[str],
        initial: str,
    ) -> str:
        existing = _find_item(items, helper_id)
        payload = {
            "id": helper_id,
            "name": name,
            "options": list(options),
            "initial": initial,
        }
        if existing is None:
            items.append(payload)
        else:
            existing.setdefault("name", name)
            existing["options"] = list(options)
            existing.setdefault("initial", initial)
        return f"input_select.{helper_id}"

    def _load_items(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return list(raw.get("data", {}).get("items", []))

    def _write_items(
        self,
        path: Path,
        *,
        key: str,
        version: int,
        items: list[dict[str, Any]],
        minor_version: int | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "version": version,
            "key": key,
            "data": {"items": sorted(items, key=lambda item: str(item.get("id", "")))},
        }
        if minor_version is not None:
            payload["minor_version"] = minor_version
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_item(items: list[dict[str, Any]], helper_id: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("id") == helper_id:
            return item
    return None
