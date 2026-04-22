"""Notification registry scanning and policy override helpers for Herald."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

import yaml

from .controls import CHANNEL_FAMILY_TYPES
from .models import ChannelConfig

POLICY_MODE_INHERIT = "inherit"
POLICY_MODE_DISABLED = "disabled"
POLICY_MODE_TEXT_ONLY = "text_only"
POLICY_MODE_VOICE_ONLY = "voice_only"
POLICY_MODE_PUSH_ONLY = "push_only"
POLICY_MODE_CUSTOM = "custom"

POLICY_MODE_OPTIONS: tuple[str, ...] = (
    POLICY_MODE_INHERIT,
    POLICY_MODE_DISABLED,
    POLICY_MODE_TEXT_ONLY,
    POLICY_MODE_VOICE_ONLY,
    POLICY_MODE_PUSH_ONLY,
    POLICY_MODE_CUSTOM,
)

_CODE_RE = r"[a-z0-9_]+"
_IGNORED_CODES: set[str] = {
    "",
    "none",
    "null",
    "unknown",
    "unavailable",
    "idle",
    "on",
    "off",
    "info",
    "warning",
    "critical",
    "security",
    "system",
    "ai",
    "high",
    "medium",
    "low",
    "moderate",
    "healthy",
    "current",
    "available",
    "disabled",
    "enabled",
    "ok",
    "safe",
    "normal",
    "good",
    "fair",
    "calm",
    "quiet",
}

_NOTIFICATION_KEY_EXACT: dict[str, str] = {
    "washer_started_expensive_tariff": "Стиралка запущена на дорогом тарифе",
    "washer_finished": "Стирка завершена",
    "wifi_guest_detected": "Обнаружен гостевой Wi-Fi",
    "adult_content_enabled": "Режим 18+ включен",
    "adult_content_disabled": "Режим 18+ выключен",
    "morning_briefing": "Утренний брифинг",
    "evening_briefing": "Вечерний брифинг",
    "daily_report": "Ежедневный отчет",
    "weekly_report": "Недельный отчет",
    "geomagnetic_storm": "Геомагнитная буря",
    "critical_co2": "Критический CO2",
    "ollama_unavailable": "Ollama недоступен",
    "power_overload": "Перегрузка мощности",
    "grid_quality_problem": "Проблема качества сети",
    "grid_quality_recovered": "Качество сети восстановлено",
    "jump_expensive": "Скачок нагрузки на дорогом тарифе",
    "punta_started": "Начался пиковый тариф",
    "valle_started": "Начался ночной тариф",
    "report_ready": "Отчет готов",
    "report_skipped": "Отчет пропущен",
    "timer_status": "Статус таймера",
    "timer_finished": "Таймер завершен",
    "timer_cancelled": "Таймер отменен",
}

_NOTIFICATION_KEY_WORDS: dict[str, str] = {
    "ai": "ИИ",
    "co2": "CO2",
    "pm10": "PM10",
    "pm25": "PM2.5",
    "ev": "EV",
    "tts": "TTS",
    "wifi": "Wi-Fi",
    "herald": "Herald",
    "washer": "стиралка",
    "guest": "гость",
    "guests": "гости",
    "adult": "18+",
    "content": "контент",
    "mode": "режим",
    "started": "запущено",
    "finished": "завершено",
    "enabled": "включено",
    "disabled": "отключено",
    "detected": "обнаружено",
    "recommendation": "рекомендация",
    "critical": "критический",
    "warning": "предупреждение",
    "alert": "сигнал",
    "reminder": "напоминание",
    "report": "отчет",
    "power": "мощность",
    "overload": "перегрузка",
    "grid": "сеть",
    "quality": "качество",
    "problem": "проблема",
    "recovered": "восстановлено",
    "expensive": "дорогой",
    "tariff": "тариф",
    "morning": "утренний",
    "evening": "вечерний",
    "timer": "таймер",
    "status": "статус",
    "cancelled": "отменено",
    "beach": "пляж",
    "walk": "прогулка",
    "window": "окна",
    "unavailable": "недоступно",
    "security": "безопасность",
    "camera": "камеры",
    "suspicious": "подозрительно",
    "silence": "тишина",
    "anomaly": "аномалия",
    "manual": "ручной",
    "lights": "свет",
    "home": "дом",
    "selected": "выбрано",
}


@dataclass(slots=True)
class NotificationPolicyOverride:
    """User-managed policy override for one concrete notification key."""

    enabled: bool = True
    delivery_mode: str = POLICY_MODE_INHERIT
    channels: list[str] = field(default_factory=list)
    level_override: str | None = None
    cooldown_override: int | None = None
    notes: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "NotificationPolicyOverride":
        payload = dict(raw or {})
        mode = str(payload.get("delivery_mode", POLICY_MODE_INHERIT)).strip().lower()
        if mode not in POLICY_MODE_OPTIONS:
            mode = POLICY_MODE_INHERIT
        return cls(
            enabled=bool(payload.get("enabled", True)),
            delivery_mode=mode,
            channels=_normalize_channels(payload.get("channels")),
            level_override=_normalize_text(payload.get("level_override")),
            cooldown_override=_normalize_int(payload.get("cooldown_override")),
            notes=_normalize_text(payload.get("notes")),
            updated_at=_normalize_text(payload.get("updated_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "delivery_mode": self.delivery_mode,
            "channels": list(self.channels),
            "level_override": self.level_override,
            "cooldown_override": self.cooldown_override,
            "notes": self.notes,
            "updated_at": self.updated_at,
        }


@dataclass(slots=True)
class NotificationPolicyManager:
    """Discover concrete notification keys and merge effective policy."""

    root: Path

    def scan(self, *, channels: dict[str, ChannelConfig], hass) -> dict[str, dict[str, Any]]:
        """Scan the config tree and return a derived notification registry."""
        registry: dict[str, dict[str, Any]] = {}
        for route in self._discover_delivery_routes():
            selected_entity = str(route.get("selected_entity") or "").strip()
            if not selected_entity:
                continue
            router_meta = self._discover_router_meta(selected_entity)
            event_codes = list(router_meta.get("event_codes") or [])
            if not event_codes:
                current_state = _state_value(hass, selected_entity)
                if current_state and current_state not in _IGNORED_CODES:
                    event_codes = [current_state]
            if not event_codes:
                continue

            family = str(router_meta.get("family") or route.get("family") or "").strip()
            attention_entity = str(router_meta.get("attention_entity") or "").strip() or None
            helper_code_entity = str(router_meta.get("helper_code_entity") or "").strip() or None
            helper_timestamp_entity = (
                str(router_meta.get("helper_timestamp_entity") or "").strip() or None
            )
            source_files = sorted(
                {
                    str(route.get("delivery_file") or ""),
                    str(router_meta.get("router_file") or ""),
                    *[
                        str(path)
                        for path in list(router_meta.get("source_files") or [])
                        if str(path).strip()
                    ],
                }
                - {""}
            )
            channel_candidates = list(route.get("default_channels") or [])
            active_state = _state_value(hass, selected_entity)
            selected_state_ru = _state_attr(hass, selected_entity, "state_ru")
            selected_title_ru = _state_attr(hass, selected_entity, "title_ru")
            family_last_event_code = _state_value(hass, helper_code_entity)
            family_last_event_code = (
                family_last_event_code
                if family_last_event_code and family_last_event_code not in _IGNORED_CODES
                else None
            )
            family_last_event_at = (
                _normalize_state_timestamp(_state_value(hass, helper_timestamp_entity))
                if family_last_event_code
                else None
            )

            for code in event_codes:
                title = _humanize_notification_key(code)
                registry[code] = {
                    "notification_key": code,
                    "family": family or _family_from_entity(selected_entity),
                    "title": title,
                    "selected_entity": selected_entity,
                    "attention_entity": attention_entity,
                    "helper_code_entity": helper_code_entity,
                    "helper_timestamp_entity": helper_timestamp_entity,
                    "delivery_automation_id": route.get("delivery_automation_id"),
                    "delivery_file": route.get("delivery_file"),
                    "router_file": router_meta.get("router_file"),
                    "source_files": source_files,
                    "default_channels": list(channel_candidates),
                    "default_level": None,
                    "default_flow": None,
                    "active": active_state == code,
                    "active_attention": bool(_state_on(hass, attention_entity)) if attention_entity else False,
                    "selected_state": active_state if active_state and active_state not in _IGNORED_CODES else None,
                    "selected_state_ru": selected_state_ru,
                    "selected_title_ru": selected_title_ru,
                    "family_last_event_code": family_last_event_code,
                    "family_last_event_at": family_last_event_at,
                    "last_seen_at": family_last_event_at if family_last_event_code == code else None,
                    "source_count": len(source_files),
                }

        return dict(sorted(registry.items(), key=lambda item: (str(item[1].get("family") or ""), item[0])))

    def effective_registry(
        self,
        *,
        registry: dict[str, dict[str, Any]],
        overrides: dict[str, dict[str, Any]],
        channels: dict[str, ChannelConfig],
    ) -> list[dict[str, Any]]:
        """Merge derived registry entries with user policy overrides."""
        channel_names = sorted(channels)
        items: list[dict[str, Any]] = []
        for notification_key, entry in sorted(
            registry.items(),
            key=lambda item: (str(item[1].get("family") or ""), item[0]),
        ):
            override = NotificationPolicyOverride.from_dict(overrides.get(notification_key))
            effective_channels = self.resolve_channels(
                mode=override.delivery_mode,
                requested_channels=override.channels,
                available_channels=channels,
                inherited_channels=list(entry.get("default_channels") or []),
            )
            items.append(
                {
                    **dict(entry),
                    "policy": override.to_dict(),
                    "effective": {
                        "enabled": override.enabled and override.delivery_mode != POLICY_MODE_DISABLED,
                        "delivery_mode": override.delivery_mode,
                        "channels": effective_channels,
                        "level_override": override.level_override,
                        "cooldown_override": override.cooldown_override,
                        "notes": override.notes,
                    },
                    "available_channels": channel_names,
                }
            )
        return items

    def effective_policy(
        self,
        *,
        notification_key: str,
        overrides: dict[str, dict[str, Any]],
        channels: dict[str, ChannelConfig],
        inherited_channels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return the effective policy for one notification key."""
        override = NotificationPolicyOverride.from_dict(overrides.get(notification_key))
        resolved_channels = self.resolve_channels(
            mode=override.delivery_mode,
            requested_channels=override.channels,
            available_channels=channels,
            inherited_channels=list(inherited_channels or []),
        )
        return {
            "notification_key": notification_key,
            "enabled": override.enabled and override.delivery_mode != POLICY_MODE_DISABLED,
            "delivery_mode": override.delivery_mode,
            "channels": resolved_channels,
            "level_override": override.level_override,
            "cooldown_override": override.cooldown_override,
            "notes": override.notes,
            "updated_at": override.updated_at,
        }

    def resolve_channels(
        self,
        *,
        mode: str,
        requested_channels: list[str],
        available_channels: dict[str, ChannelConfig],
        inherited_channels: list[str],
    ) -> list[str]:
        """Resolve effective channels from one delivery mode."""
        normalized_mode = str(mode or POLICY_MODE_INHERIT).strip().lower()
        if normalized_mode not in POLICY_MODE_OPTIONS:
            normalized_mode = POLICY_MODE_INHERIT
        if normalized_mode == POLICY_MODE_INHERIT:
            return list(inherited_channels)
        if normalized_mode == POLICY_MODE_DISABLED:
            return []
        if normalized_mode == POLICY_MODE_CUSTOM:
            return [
                name
                for name in requested_channels
                if name in available_channels
            ]
        if normalized_mode == POLICY_MODE_VOICE_ONLY:
            return _channels_for_types(
                available_channels,
                CHANNEL_FAMILY_TYPES["voice"] | CHANNEL_FAMILY_TYPES["tv"],
            )
        if normalized_mode == POLICY_MODE_PUSH_ONLY:
            return _channels_for_types(
                available_channels,
                CHANNEL_FAMILY_TYPES["push"],
            )
        if normalized_mode == POLICY_MODE_TEXT_ONLY:
            return [
                name
                for name, channel in sorted(available_channels.items())
                if channel.channel_type not in (CHANNEL_FAMILY_TYPES["voice"] | CHANNEL_FAMILY_TYPES["tv"])
            ]
        return list(inherited_channels)

    def _discover_delivery_routes(self) -> list[dict[str, Any]]:
        automations_dir = self.root / "automations"
        routes: list[dict[str, Any]] = []
        for path in sorted(automations_dir.glob("*.yaml")):
            raw = _safe_read_text(path)
            if "service: herald.notify" not in raw:
                continue
            if "selected_alert" not in raw and "selected_alert_notify" not in raw and "selected event" not in raw.lower():
                if "selected_state" not in raw and "vybrann" not in raw and "sistema_vybrannyi_alert" not in raw:
                    continue
            selected_entity = _first_match(
                raw,
                r"selected_state:\s*[\"']\{\{\s*states\('([^']+)'\)\s*\}\}[\"']",
            )
            if not selected_entity:
                selected_entity = _first_match(raw, r"state_attr\('([^']+)',\s*'flow'\)")
            if not selected_entity:
                continue
            route = {
                "family": _family_from_entity(selected_entity),
                "selected_entity": selected_entity,
                "delivery_file": str(path.relative_to(self.root)),
                "delivery_automation_id": _first_match(raw, r'^\s*-\s+id:\s*"([^"]+)"', flags=re.M),
                "default_channels": _extract_channel_names(raw),
            }
            routes.append(route)
        return routes

    def _discover_router_meta(self, selected_entity: str) -> dict[str, Any]:
        templates_dir = self.root / "templates"
        object_id = selected_entity.split(".", maxsplit=1)[-1]
        candidates: list[Path] = []
        for path in sorted(templates_dir.glob("*.yaml")):
            raw = _safe_read_text(path)
            if f"unique_id: {object_id}" in raw or selected_entity in raw:
                candidates.append(path)
        if not candidates:
            return {
                "family": _family_from_entity(selected_entity),
                "event_codes": [],
                "router_file": None,
                "attention_entity": None,
                "helper_code_entity": None,
                "helper_timestamp_entity": None,
                "source_files": [],
            }

        for path in candidates:
            raw = _safe_read_text(path)
            docs = _safe_load_yaml(path)
            selected_item = None
            attention_unique_id = None
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                for item in list(doc.get("sensor", []) or []):
                    if str(item.get("unique_id") or "").strip() == object_id:
                        selected_item = item
                for item in list(doc.get("binary_sensor", []) or []):
                    unique_id = str(item.get("unique_id") or "").strip()
                    if unique_id.endswith("attention_required") and selected_entity in raw:
                        attention_unique_id = unique_id
                    if object_id.replace("_selected", "_attention_required") == unique_id:
                        attention_unique_id = unique_id
            if selected_item is None:
                continue
            family = _family_from_entity(selected_entity)
            return {
                "family": family,
                "event_codes": self._extract_event_codes(selected_entity, selected_item),
                "router_file": str(path.relative_to(self.root)),
                "attention_entity": f"binary_sensor.{attention_unique_id}" if attention_unique_id else None,
                "helper_code_entity": _first_match(raw, r"(input_text\.[a-z0-9_]+_last_event_code)"),
                "helper_timestamp_entity": _first_match(
                    raw,
                    r"(input_datetime\.[a-z0-9_]+_(?:last_event_at|last_selected_event_at))",
                ),
                "source_files": self._discover_source_files(raw),
            }
        return {
            "family": _family_from_entity(selected_entity),
            "event_codes": [],
            "router_file": None,
            "attention_entity": None,
            "helper_code_entity": None,
            "helper_timestamp_entity": None,
            "source_files": [],
        }

    def _extract_event_codes(
        self,
        selected_entity: str,
        sensor_item: dict[str, Any],
    ) -> list[str]:
        object_id = selected_entity.split(".", maxsplit=1)[-1]
        sources = [
            sensor_item.get("state"),
            sensor_item.get("icon"),
            *list((sensor_item.get("attributes") or {}).values()),
        ]
        codes: set[str] = set()
        for source in sources:
            if not isinstance(source, str):
                continue
            if "states(" in source:
                codes.update(
                    re.findall(
                        rf"states\('{re.escape(selected_entity)}'\)\s*==\s*'({_CODE_RE})'",
                        source,
                    )
                )
                for block in re.findall(
                    rf"states\('{re.escape(selected_entity)}'\)\s+in\s+\[([^\]]+)\]",
                    source,
                ):
                    codes.update(re.findall(rf"'({_CODE_RE})'", block))
            if "this.state" in source:
                codes.update(re.findall(rf"this\.state\s*==\s*'({_CODE_RE})'", source))
                for block in re.findall(r"this\.state\s+in\s+\[([^\]]+)\]", source):
                    codes.update(re.findall(rf"'({_CODE_RE})'", block))
            if "icons =" in source or "labels =" in source:
                codes.update(re.findall(rf"'({_CODE_RE})'\s*:", source))
            if source is sensor_item.get("state"):
                codes.update(
                    re.findall(
                        rf"%\}}\s*({_CODE_RE})\s*(?:\n|$)",
                        source,
                        flags=re.M,
                    )
                )
            if object_id in source:
                codes.update(re.findall(rf"'({_CODE_RE})'", source))
        filtered = [
            code
            for code in codes
            if code not in _IGNORED_CODES
        ]
        return sorted(set(filtered))

    def _discover_source_files(self, router_raw: str) -> list[str]:
        source_entities = re.findall(r"automation\.([a-z0-9_]+)", router_raw)
        if not source_entities:
            return []
        matched: list[str] = []
        automations_dir = self.root / "automations"
        for path in sorted(automations_dir.glob("*.yaml")):
            raw = _safe_read_text(path)
            if any(f'id: "{entity}"' in raw or f"id: '{entity}'" in raw for entity in source_entities):
                matched.append(str(path.relative_to(self.root)))
        return matched


def _safe_load_yaml(path: Path) -> list[dict[str, Any]]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _first_match(text: str, pattern: str, *, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    if match is None:
        return None
    return str(match.group(1)).strip() or None


def _extract_channel_names(text: str) -> list[str]:
    matches: list[str] = []
    for block in re.findall(r"selected_channels:.*", text):
        matches.extend(re.findall(rf"'({_CODE_RE})'", block))
    for block in re.findall(r"channels\s*[:=]\s*\[([^\]]+)\]", text):
        matches.extend(re.findall(rf"'({_CODE_RE})'", block))
    if not matches:
        for block in re.findall(r"channels:\s*\n((?:\s+-\s+[a-z0-9_]+\n)+)", text):
            matches.extend(re.findall(r"-\s+([a-z0-9_]+)", block))
    return sorted(set(matches))


def _state_value(hass, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    return str(state.state).strip()


def _state_on(hass, entity_id: str | None) -> bool:
    if not entity_id:
        return False
    state = hass.states.get(entity_id)
    return state is not None and state.state == "on"


def _state_attr(hass, entity_id: str | None, attribute: str) -> str | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None:
        return None
    value = state.attributes.get(attribute)
    if value in (None, "", "none", "None", "unknown", "unavailable"):
        return None
    return str(value).strip() or None


def _normalize_state_timestamp(raw: str | None) -> str | None:
    if raw in (None, "", "none", "None", "unknown", "unavailable"):
        return None
    return str(raw).strip() or None


def _family_from_entity(entity_id: str) -> str:
    object_id = entity_id.split(".", maxsplit=1)[-1]
    for suffix in (
        "_alert_selected",
        "_selected",
        "_attention_required",
        "_recommendation_selected",
    ):
        if object_id.endswith(suffix):
            return object_id[: -len(suffix)]
    return object_id


def _humanize_notification_key(key: str) -> str:
    normalized = str(key).strip().lower()
    if not normalized:
        return ""
    if normalized in _NOTIFICATION_KEY_EXACT:
        return _NOTIFICATION_KEY_EXACT[normalized]
    human = " ".join(
        _NOTIFICATION_KEY_WORDS.get(part, part)
        for part in normalized.split("_")
        if part
    ).strip()
    if not human:
        return normalized
    return human[0].upper() + human[1:]


def _channels_for_types(
    channels: dict[str, ChannelConfig],
    allowed_types: set[str],
) -> list[str]:
    return [
        name
        for name, channel in sorted(channels.items())
        if channel.channel_type in allowed_types
    ]


def _normalize_channels(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [part.strip() for part in raw.split(",")]
        return [part for part in parts if part]
    if isinstance(raw, list):
        return [
            str(item).strip()
            for item in raw
            if str(item).strip()
        ]
    return []


def _normalize_text(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _normalize_int(raw: Any) -> int | None:
    if raw in (None, "", "none", "null"):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None
