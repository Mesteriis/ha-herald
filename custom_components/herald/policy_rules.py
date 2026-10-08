"""Pure per-notification constraints shared by preview, admission, and delivery."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import NotificationContext, PresenceSnapshot
from .presence import canonical_room_name

PRESENCE_OPTIONS = ("any", "someone_home", "nobody_home")
QUIET_HOURS_OPTIONS = ("inherit", "text_only", "mute")


def normalize_user(value: Any) -> str:
    """Use a person entity ID for both stored selections and matching aliases."""
    if not isinstance(value, str):
        return ""
    text = value.strip().lower()
    if not text:
        return ""
    return f"person.{text.removeprefix('person.')}"


def normalize_users(value: Any) -> list[str] | None:
    """Preserve inheritance, explicit emptiness, and unknown stored selections."""
    if value is None:
        return None
    values = value if isinstance(value, list) else [value]
    return list(dict.fromkeys(normalize_user(item) for item in values))


def normalize_room(value: Any) -> str:
    """Use the same room aliases as presence and routing without discovering rooms."""
    return canonical_room_name(str(value)) or ""


def has_rule_constraints(policy: Mapping[str, Any]) -> bool:
    """Return whether a policy requires fresh rule evaluation, including invalid data."""
    return (
        policy.get("users") is not None
        or policy.get("target_room") is not None
        or policy.get("presence", "any") != "any"
        or policy.get("quiet_hours", "inherit") != "inherit"
    )


def apply_rule(
    context: NotificationContext,
    policy: Mapping[str, Any],
    presence: PresenceSnapshot,
    *,
    known_users: Iterable[str] | None = None,
    known_rooms: Iterable[str] | None = None,
) -> str | None:
    """Constrain a disposable/request context, returning a blocking reason if needed.

    The coordinator supplies the current person/room catalogs, including people
    away from home and unoccupied rooms. Without catalogs, only selections already
    present in the context/snapshot can be verified. Never resolve new recipients:
    intersect the current audience so repeated calls cannot resurrect recipients
    removed by explicit targeting, silent mode, or an earlier evaluation.
    """
    context.metadata.pop("policy_text_only", None)
    context.metadata.pop("policy_target_room", None)
    users = normalize_users(policy.get("users"))
    room = None if policy.get("target_room") is None else normalize_room(policy["target_room"])
    presence_rule = policy.get("presence", "any")
    quiet_rule = policy.get("quiet_hours", "inherit")

    if users is not None:
        context.metadata["policy_users_explicit"] = True
        context.metadata["audience_resolved"] = True
        catalog = {normalize_user(user) for user in (context.users if known_users is None else known_users)}
        selected = set(users)
        context.users = list(dict.fromkeys(
            normalize_user(user) for user in context.users if normalize_user(user) in selected
        ))
        context.user = context.users[0] if context.users else None
        if any(not user or user not in catalog for user in users):
            return "policy_unknown_user"
        if not context.users:
            return "notification_policy_no_recipients"
    if presence_rule not in PRESENCE_OPTIONS:
        return "policy_invalid_presence"
    if quiet_rule not in QUIET_HOURS_OPTIONS:
        return "policy_invalid_quiet_hours"
    if room is not None:
        room_catalog = (
            [context.room, presence.primary_room, *presence.occupied_rooms]
            if known_rooms is None else known_rooms
        )
        if not room or room not in {normalize_room(item) for item in room_catalog if item}:
            return "policy_unknown_room"

    if room is not None:
        context.room = room
        context.metadata["policy_target_room"] = room

    if presence_rule == "someone_home" and presence.nobody_home:
        return "policy_someone_home"
    if presence_rule == "nobody_home" and not presence.nobody_home:
        return "policy_nobody_home"
    if presence.quiet_hours:
        if quiet_rule == "mute":
            return "policy_quiet_hours"
        if quiet_rule == "text_only":
            context.metadata["policy_text_only"] = True
    return None
