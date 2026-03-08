"""Tests for Herald actionable notification helpers."""

from __future__ import annotations

from custom_components.herald.actions import (
    build_ack_action,
    build_snooze_action,
    ensure_notification_id,
    parse_action_token,
)


def test_notification_id_generation_is_stable_enough() -> None:
    notification_id = ensure_notification_id(None, "timer_notifications", "2026-03-08T12:00:00+00:00")

    assert notification_id.startswith("timer_notifications_20260308120000")


def test_ack_action_roundtrip() -> None:
    token = build_ack_action("notif_123")

    assert parse_action_token(token) == {"kind": "ack", "notification_id": "notif_123"}


def test_snooze_action_roundtrip() -> None:
    token = build_snooze_action("energy_events", minutes=45, notification_id="notif_123")

    assert parse_action_token(token) == {
        "kind": "snooze",
        "flow": "energy_events",
        "minutes": 45,
        "notification_id": "notif_123",
    }
