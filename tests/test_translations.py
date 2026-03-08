"""Tests for Herald translation helpers."""

from __future__ import annotations

from custom_components.herald.translations import action_feedback_text


def test_action_feedback_text_localizes_snooze() -> None:
    assert action_feedback_text(language="en", kind="snooze", minutes=30) == "Flow snoozed for 30 min."
    assert "30" in action_feedback_text(language="ru", kind="snooze", minutes=30)
