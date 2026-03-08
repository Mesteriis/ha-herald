"""Tests for Herald translation helpers."""

from __future__ import annotations

from custom_components.herald.translations import action_feedback_text, runtime_control_change_text


def test_action_feedback_text_localizes_snooze() -> None:
    assert action_feedback_text(language="en", kind="snooze", minutes=30) == "Flow snoozed for 30 min."
    assert "30" in action_feedback_text(language="ru", kind="snooze", minutes=30)


def test_runtime_control_change_text_localizes_switch_and_select_changes() -> None:
    assert "maintenance" in runtime_control_change_text(
        language="en",
        key="maintenance_mode",
        value=True,
    ).lower()
    assert "канала" in runtime_control_change_text(
        language="ru",
        key="channel_min_level:voice_auto",
        value="critical",
    ).lower()
    assert "комнаты" in runtime_control_change_text(
        language="ru",
        key="room_audio_target:living_room",
        value="homepod",
    ).lower()
