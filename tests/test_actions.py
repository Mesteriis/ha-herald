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

    assert token == "ack|notif_123"
    assert parse_action_token(token) == {"kind": "ack", "notification_id": "notif_123"}


def test_snooze_action_roundtrip() -> None:
    token = build_snooze_action("energy_events", minutes=45, notification_id="notif_123")

    assert token == "snz|energy_events|45|notif_123"
    assert parse_action_token(token) == {
        "kind": "snooze",
        "flow": "energy_events",
        "minutes": 45,
        "notification_id": "notif_123",
    }


def test_parse_legacy_action_tokens_for_backward_compatibility() -> None:
    assert parse_action_token("HERALD_ACK|notif_123") == {
        "kind": "ack",
        "notification_id": "notif_123",
    }
    assert parse_action_token("HERALD_SNOOZE|security_alerts|30|notif_123") == {
        "kind": "snooze",
        "flow": "security_alerts",
        "minutes": 30,
        "notification_id": "notif_123",
    }


def test_compact_snooze_token_fits_telegram_callback_limit() -> None:
    token = build_snooze_action(
        "security_alerts",
        minutes=30,
        notification_id="security_alerts_20260308150008_b5f15414",
    )

    assert len(token) <= 64
