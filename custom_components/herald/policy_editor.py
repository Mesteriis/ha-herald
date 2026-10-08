"""Pure rule-editor helpers shared by saved rules and unsaved previews."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .notification_policies import NotificationPolicyOverride

POLICY_FIELDS = (
    "enabled", "delivery_mode", "channels", "level_override", "cooldown_override", "notes",
    "users", "target_room", "presence", "quiet_hours",
)


def merge_policy(current: dict[str, Any] | None, changes: dict[str, Any], channels: dict) -> NotificationPolicyOverride:
    """Normalize a partial edit without modifying its saved baseline."""
    merged = {**dict(current or {}), **{key: value for key, value in changes.items() if key in POLICY_FIELDS}}
    policy = NotificationPolicyOverride.from_dict(merged)
    policy.channels = list(dict.fromkeys(name for name in policy.channels if name in channels))
    return policy


def build_preview_request(entry: dict[str, Any], message: str | None) -> tuple[dict[str, Any], list[str]]:
    """Build an explicitly bounded example from scanned routing defaults."""
    values = deepcopy(entry.get("preview_request") or {})
    warnings = ["Триггеры и условия автоматизации не выполняются; проверяется только маршрутизация Herald."]
    if "preview_request" not in entry:
        if entry.get("default_channels"):
            values["channels"] = list(entry["default_channels"])
        if entry.get("default_flow"):
            values["flow"] = entry["default_flow"]
        if entry.get("default_level"):
            values["level"] = entry["default_level"]
        warnings.append("Полный вызов автоматизации неизвестен: используются доступные значения реестра и текущий контекст Herald.")
    if entry.get("defaults_ambiguous") or entry.get("defaults_dynamic") or entry.get("preview_unknown_fields"):
        warnings.append("Часть параметров задаётся шаблонами или различается между источниками; это пример, а не точное воспроизведение события.")
    if not message:
        warnings.append("Используется пример текста. Проверка повторов зависит от точного текста настоящего уведомления.")
    key = str(entry["notification_key"])
    values.setdefault("event", values.get("title") or key)
    values.update({"message": message or f"Проверка правила: {entry.get('title') or key}",
                   "metadata": {"notification_key": key}, "rewrite": False})
    return values, warnings
