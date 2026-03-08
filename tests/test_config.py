"""Tests for Herald config defaults."""

from __future__ import annotations

from custom_components.herald.models import HeraldConfig


def test_default_config_builds_channels_and_flows() -> None:
    config = HeraldConfig.from_raw(None)

    assert "persistent_default" in config.channels
    assert "system_events" in config.flows
    assert config.quiet_hours.start == "23:00"
    assert config.presence["family_group"] == "group.family"


def test_config_supports_quiet_hours_policy_and_summary_personality() -> None:
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "bedroom_tts": {
                    "type": "tts",
                    "entity_id": "media_player.bedroom",
                    "quiet_hours_policy": "allow",
                }
            },
            "flows": {
                "system_events": {
                    "summary_personality": "Jarvis",
                }
            },
        }
    )

    assert config.channels["bedroom_tts"].quiet_hours_policy == "allow"
    assert config.flows["system_events"].summary_personality == "Jarvis"
