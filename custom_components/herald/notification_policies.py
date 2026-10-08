"""Notification registry scanning and policy override helpers for Herald."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .controls import CHANNEL_FAMILY_TYPES
from .models import ChannelConfig
from .policy_rules import normalize_room, normalize_users

PREVIEW_FIELDS = (
    "event", "title", "flow", "level", "channels", "user", "users", "room", "device", "entities", "source",
    "force", "immediately", "summarize", "suppress", "group", "send_voice", "send_text",
    "send_mobile", "send_telegram", "mobile_zone", "target_group", "timestamp_policy",
)


def literal_preview_request(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Keep routing literals only; never execute or retain templates or message text."""
    def literal(value: Any) -> bool:
        if isinstance(value, list):
            return all(literal(item) for item in value)
        return isinstance(value, (str, int, float, bool)) and not any(
            marker in str(value) for marker in ("{{", "{%", "{#")
        )

    values = {key: deepcopy(payload[key]) for key in PREVIEW_FIELDS if key in payload and literal(payload[key])}
    unknown = [key for key in PREVIEW_FIELDS if key in payload and key not in values]
    # These fields can affect routing but require a fully specified route_preview request.
    unknown.extend(key for key in ("context", "target", "mobile_options", "tts_options") if key in payload)
    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and any(key != "notification_key" for key in metadata):
        unknown.append("metadata")
    return values, unknown


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
    users: list[str] | None = None
    target_room: str | None = None
    presence: str = "any"
    quiet_hours: str = "inherit"

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
            users=normalize_users(payload.get("users")),
            target_room=None if payload.get("target_room") is None else normalize_room(payload["target_room"]),
            presence=str(payload.get("presence", "any")),
            quiet_hours=str(payload.get("quiet_hours", "inherit")),
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
            "users": None if self.users is None else list(self.users),
            "target_room": self.target_room,
            "presence": self.presence,
            "quiet_hours": self.quiet_hours,
        }


@dataclass(slots=True)
class NotificationPolicyManager:
    """Discover concrete notification keys and merge effective policy."""

    root: Path
    scan_issues: list[dict[str, str]] = field(default_factory=list, init=False)
    _documents: dict[Path, Any] = field(default_factory=dict, init=False, repr=False)

    def scan(self, *, channels: dict[str, ChannelConfig], states: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Scan in an executor with isolated work data and an HA state snapshot."""
        worker = NotificationPolicyManager(self.root)
        registry = worker._scan(channels=channels, states=states)
        self.scan_issues = worker.scan_issues
        return registry

    def _scan(self, *, channels: dict[str, ChannelConfig], states: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Keep parsed configuration local to one scan, including concurrent calls."""
        self.scan_issues = []
        self._documents = _load_config_documents(self.root, self.scan_issues)
        registry = self._discover_static_calls()
        for route in self._discover_delivery_routes():
            selected_entity = str(route.get("selected_entity") or "").strip()
            if not selected_entity:
                continue
            router_meta = self._discover_router_meta(selected_entity)
            event_codes = list(router_meta.get("event_codes") or [])
            if not event_codes:
                current_state = _state_value(states, selected_entity)
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
            active_state = _state_value(states, selected_entity)
            selected_state_ru = _state_attr(states, selected_entity, "state_ru")
            selected_title_ru = _state_attr(states, selected_entity, "title_ru")
            family_last_event_code = _state_value(states, helper_code_entity)
            family_last_event_code = (
                family_last_event_code
                if family_last_event_code and family_last_event_code not in _IGNORED_CODES
                else None
            )
            family_last_event_at = (
                _normalize_state_timestamp(_state_value(states, helper_timestamp_entity))
                if family_last_event_code
                else None
            )

            for code in event_codes:
                title = _humanize_notification_key(code)
                entry = {
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
                    "active_attention": bool(_state_on(states, attention_entity)) if attention_entity else False,
                    "selected_state": active_state if active_state and active_state not in _IGNORED_CODES else None,
                    "selected_state_ru": selected_state_ru,
                    "selected_title_ru": selected_title_ru,
                    "family_last_event_code": family_last_event_code,
                    "family_last_event_at": family_last_event_at,
                    "last_seen_at": family_last_event_at if family_last_event_code == code else None,
                    "source_count": len(source_files),
                    "discovery": "selected_event",
                }
                _merge_registry_entry(registry, code, entry)

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
                        **override.to_dict(),
                        "enabled": override.enabled and override.delivery_mode != POLICY_MODE_DISABLED,
                        "channels": effective_channels,
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
            **override.to_dict(),
            "notification_key": notification_key,
            "enabled": override.enabled and override.delivery_mode != POLICY_MODE_DISABLED,
            "channels": resolved_channels,
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

    def _discover_static_calls(self) -> dict[str, dict[str, Any]]:
        """Find literal notify calls without evaluating automation templates."""
        registry: dict[str, dict[str, Any]] = {}
        for path, document in self._documents.items():
            relative_path = str(path.relative_to(self.root.resolve()))
            for node in _walk_mappings(document, skip_service_data=True):
                service = node.get("service", node.get("action"))
                if service != "herald.notify":
                    continue
                payload = node.get("data", node.get("data_template", {}))
                if not isinstance(payload, dict):
                    self.scan_issues.append({"file": relative_path, "reason": "dynamic_notify_data"})
                    continue
                metadata = payload.get("metadata") or {}
                if not isinstance(metadata, dict):
                    self.scan_issues.append({"file": relative_path, "reason": "dynamic_notification_metadata"})
                    continue
                key = metadata.get("notification_key")
                key = key or payload.get("event") or payload.get("title") or "Herald"
                if not _is_literal(key):
                    self.scan_issues.append({"file": relative_path, "reason": "dynamic_notification_key"})
                    continue
                key = str(key).strip()
                if not key:
                    continue
                channel_value = payload.get("channels", [])
                literal_channels = isinstance(channel_value, (str, list)) and all(
                    _is_literal(item) for item in (channel_value if isinstance(channel_value, list) else [channel_value])
                )
                defaults_dynamic = not literal_channels or any(
                    field in payload and not _is_literal(payload[field]) for field in ("flow", "level")
                )
                if defaults_dynamic:
                    self.scan_issues.append({"file": relative_path, "reason": "dynamic_route_defaults"})
                preview_request, preview_unknown = literal_preview_request(payload)
                entry = {
                    "preview_request": preview_request,
                    "preview_unknown_fields": preview_unknown,
                    "notification_key": key,
                    "title": _humanize_notification_key(key),
                    "family": str(payload.get("flow") or "general") if _is_literal(payload.get("flow", "general")) else "general",
                    "default_channels": _normalize_channels(channel_value) if literal_channels else [],
                    "default_level": payload.get("level", "info") if _is_literal(payload.get("level", "info")) else None,
                    "default_flow": payload.get("flow") if _is_literal(payload.get("flow", "")) else None,
                    "defaults_dynamic": defaults_dynamic,
                    "active": False,
                    "active_attention": False,
                    "delivery_file": relative_path,
                    "source_files": [relative_path],
                    "source_count": 1,
                    "discovery": "static_service",
                }
                _merge_registry_entry(registry, key, entry)
        return registry

    def _discover_delivery_routes(self) -> list[dict[str, Any]]:
        routes: list[dict[str, Any]] = []
        for path, document in self._documents.items():
            if not any(node.get("service", node.get("action")) == "herald.notify" for node in _walk_mappings(document, skip_service_data=True)):
                continue
            raw = _safe_read_text(path)
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
                "delivery_file": str(path.relative_to(self.root.resolve())),
                "delivery_automation_id": _first_match(raw, r'^\s*-\s+id:\s*"([^"]+)"', flags=re.M),
                "default_channels": _extract_channel_names(raw),
            }
            routes.append(route)
        return routes

    def _discover_router_meta(self, selected_entity: str) -> dict[str, Any]:
        object_id = selected_entity.split(".", maxsplit=1)[-1]
        candidates: list[Path] = []
        for path in self._documents:
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
            docs = _walk_mappings(self._documents[path])
            selected_item = None
            attention_unique_id = None
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                for item in _items_as_mappings(doc.get("sensor")):
                    if str(item.get("unique_id") or "").strip() == object_id:
                        selected_item = item
                for item in _items_as_mappings(doc.get("binary_sensor")):
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
                "router_file": str(path.relative_to(self.root.resolve())),
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
        attributes = sensor_item.get("attributes")
        sources = [
            sensor_item.get("state"),
            sensor_item.get("icon"),
            *(list(attributes.values()) if isinstance(attributes, dict) else []),
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
        for path in self._documents:
            raw = _safe_read_text(path)
            if any(f'id: "{entity}"' in raw or f"id: '{entity}'" in raw for entity in source_entities):
                matched.append(str(path.relative_to(self.root.resolve())))
        return matched


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


def _state_value(states, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    state = states.get(entity_id)
    if state is None:
        return None
    return str(state.get("state", "")).strip()


def _state_on(states, entity_id: str | None) -> bool:
    if not entity_id:
        return False
    state = states.get(entity_id)
    return state is not None and state.get("state") == "on"


def _state_attr(states, entity_id: str | None, attribute: str) -> str | None:
    if not entity_id:
        return None
    state = states.get(entity_id)
    if state is None:
        return None
    value = state.get("attributes", {}).get(attribute)
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


def snapshot_registry_states(hass) -> dict[str, dict[str, Any]]:
    """Copy only registry display fields on the Home Assistant event loop."""
    async_all = getattr(hass.states, "async_all", None)
    if async_all is None:
        return {}
    return {
        state.entity_id: {
            "state": str(state.state),
            "attributes": {
                key: str(value)
                for key in ("state_ru", "title_ru")
                if (value := state.attributes.get(key)) is not None
            },
        }
        for state in async_all()
    }


@dataclass(frozen=True)
class _YamlReference:
    tag: str
    value: str


class _RegistryLoader(yaml.SafeLoader):
    """Preserve HA tags as inert references; never resolve !secret or templates."""


def _unknown_yaml_tag(loader, node):
    value = loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else ""
    return _YamlReference(node.tag, value)


_RegistryLoader.add_constructor(None, _unknown_yaml_tag)


def _load_config_documents(root: Path, issues: list[dict[str, str]]) -> dict[Path, Any]:
    """Read bounded local YAML definitions and explicit structural includes."""
    root = root.resolve()
    documents: dict[Path, Any] = {}
    visited: set[Path] = set()
    include_keys = {"automation", "script", "template", "packages", "action", "actions", "sequence", "choose", "then", "else", "default", "repeat"}
    include_tags = {"!include", "!include_dir_list", "!include_dir_named", "!include_dir_merge_list", "!include_dir_merge_named"}

    def issue(path: Path, reason: str) -> None:
        # Only report root-relative references; never echo secret values/paths.
        try:
            name = str(path.relative_to(root))
        except ValueError:
            name = "<outside config>"
        entry = {"file": name, "reason": reason}
        if entry not in issues:
            issues.append(entry)

    def allowed(path: Path, *, directory: bool = False) -> bool:
        try:
            resolved = path.resolve()
            relative = resolved.relative_to(root)
        except (OSError, ValueError, RuntimeError):
            return False
        if any(part.startswith(".") for part in relative.parts):
            return False
        if resolved.stem.lower().startswith("secrets"):
            return False
        return directory or resolved.suffix.lower() in {".yaml", ".yml"}

    def follow(value: Any, source: Path, *, structural: bool = False, package_map: bool = False, seen: set[int] | None = None) -> None:
        seen = set() if seen is None else seen
        if isinstance(value, _YamlReference):
            if value.tag == "!secret":
                return
            if value.tag not in include_tags or not structural or not _is_literal(value.value):
                issue(source, "unsupported_yaml_tag_or_include")
                return
            target = source.parent / value.value
            directory = value.tag != "!include"
            if not allowed(target, directory=directory):
                issue(source, "unsafe_include")
                return
            if directory:
                if not target.is_dir():
                    issue(source, "missing_include")
                    return
                for child in sorted(target.rglob("*")):
                    if child.is_file() and child.suffix.lower() in {".yaml", ".yml"}:
                        load(child)
            else:
                load(target)
            return
        if not isinstance(value, (dict, list)) or id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, list):
            for child in value:
                follow(child, source, structural=structural, seen=seen)
            return
        for key, child in value.items():
            if str(key) in {"data", "data_template", "variables"}:
                # Service data includes are not needed for static registry discovery.
                continue
            section = str(key).split(" ", maxsplit=1)[0]
            selected_section = package_map or section in include_keys
            follow(child, source, structural=selected_section, package_map=section == "packages", seen=seen)

    def load(path: Path) -> None:
        if not allowed(path):
            issue(path, "unsafe_include")
            return
        path = path.resolve()
        if path in visited:
            return
        visited.add(path)
        if len(visited) > 512:
            issue(path, "scan_file_limit")
            return
        try:
            with path.open(encoding="utf-8") as stream:
                raw = stream.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                issue(path, "scan_size_limit")
                return
            payload = yaml.load(raw, Loader=_RegistryLoader)
        except (OSError, UnicodeError, yaml.YAMLError, RecursionError):
            issue(path, "unreadable_yaml")
            return
        documents[path] = payload
        follow(payload, path, structural=True)

    for stem in ("configuration", "automations", "scripts"):
        for suffix in (".yaml", ".yml"):
            path = root / f"{stem}{suffix}"
            if path.is_file():
                load(path)
    for dirname in ("automations", "scripts", "packages", "templates"):
        for path in sorted((root / dirname).rglob("*")):
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}:
                load(path)
    return documents


def _walk_mappings(value: Any, seen: set[int] | None = None, *, skip_service_data: bool = False):
    """Traverse YAML objects once, including recursive aliases safely."""
    seen = set() if seen is None else seen
    if not isinstance(value, (dict, list)) or id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, dict):
        yield value
        children = (
            child for key, child in value.items()
            if not skip_service_data or key not in {"data", "data_template", "variables"}
        )
    else:
        children = value
    for child in children:
        yield from _walk_mappings(child, seen, skip_service_data=skip_service_data)


def _is_literal(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) and not any(
        marker in str(value) for marker in ("{{", "{%", "{#")
    )


def _merge_registry_entry(registry: dict[str, dict[str, Any]], key: str, entry: dict[str, Any]) -> None:
    previous = registry.get(key)
    if previous is None:
        registry[key] = entry
        return
    source_files = sorted(set(previous.get("source_files", [])) | set(entry.get("source_files", [])))
    merged = {**previous, **entry, "source_files": source_files, "source_count": len(source_files)}
    merged["defaults_dynamic"] = bool(previous.get("defaults_dynamic") or entry.get("defaults_dynamic"))
    for field_name in ("default_channels", "default_level", "default_flow"):
        if previous.get(field_name) != entry.get(field_name):
            merged[field_name] = [] if field_name == "default_channels" else None
            merged["defaults_ambiguous"] = True
    if previous.get("preview_request") != entry.get("preview_request"):
        merged.pop("preview_request", None)
        merged["defaults_ambiguous"] = True
    merged["preview_unknown_fields"] = sorted(set(previous.get("preview_unknown_fields", [])) | set(entry.get("preview_unknown_fields", [])))
    registry[key] = merged


def _items_as_mappings(value):
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []
