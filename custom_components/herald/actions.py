"""Helpers for Herald actionable notifications."""

from __future__ import annotations

from uuid import uuid4

from .const import ACTION_ACK, ACTION_SNOOZE, DEFAULT_SNOOZE_MINUTES

_ACTION_SEPARATOR = "|"
_COMPACT_ACTION_ACK = "ack"
_COMPACT_ACTION_SNOOZE = "snz"
_ACK_TOKENS = {ACTION_ACK, _COMPACT_ACTION_ACK}
_SNOOZE_TOKENS = {ACTION_SNOOZE, _COMPACT_ACTION_SNOOZE}


def ensure_notification_id(notification_id: str | None, flow: str, timestamp: str) -> str:
    """Return a stable notification id or generate a new one."""
    if notification_id:
        return notification_id
    compact_timestamp = (
        timestamp.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("+", "")
        .replace("T", "")
    )[:14]
    suffix = uuid4().hex[:8]
    return f"{flow}_{compact_timestamp}_{suffix}"


def build_ack_action(notification_id: str) -> str:
    """Build the action token for acknowledging a notification."""
    return _ACTION_SEPARATOR.join((_COMPACT_ACTION_ACK, notification_id))


def build_snooze_action(
    flow: str,
    *,
    minutes: int = DEFAULT_SNOOZE_MINUTES,
    notification_id: str,
) -> str:
    """Build the action token for snoozing a flow."""
    return _ACTION_SEPARATOR.join((_COMPACT_ACTION_SNOOZE, flow, str(minutes), notification_id))


def parse_action_token(raw: str | None) -> dict[str, str | int] | None:
    """Parse a mobile-app or Telegram action token."""
    if not raw:
        return None

    token = raw.removeprefix("/")
    parts = token.split(_ACTION_SEPARATOR)
    if not parts:
        return None

    if parts[0] in _ACK_TOKENS and len(parts) >= 2:
        return {
            "kind": "ack",
            "notification_id": parts[1],
        }

    if parts[0] in _SNOOZE_TOKENS and len(parts) >= 4:
        try:
            minutes = int(parts[2])
        except ValueError:
            minutes = DEFAULT_SNOOZE_MINUTES
        return {
            "kind": "snooze",
            "flow": parts[1],
            "minutes": minutes,
            "notification_id": parts[3],
        }

    return None
