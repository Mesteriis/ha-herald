"""Tests for Herald dashboard rendering."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.herald.coordinator import HeraldCoordinator
from custom_components.herald.models import (
    ChannelConfig,
    HeraldConfig,
    NotificationContext,
    PresenceSnapshot,
    RuntimeState,
)


class _FakePresence:
    def room_sensors(self) -> dict[str, str]:
        return {
            "living_room": "binary_sensor.room_gostinaia_occupied",
            "bedroom": "binary_sensor.room_spalnia_occupied",
        }


def test_dashboard_yaml_includes_room_sensors_and_fallback_switches() -> None:
    fake = SimpleNamespace(
        config=HeraldConfig.from_raw(
            {
                "users": {
                    "aleksandr_meshcheriakov": {"name": "Aleksandr Meshcheriakov"},
                },
                "flows": {
                    "system_events": {"channels": ["persistent_default"]},
                }
            }
        ),
        presence=_FakePresence(),
        plugins=SimpleNamespace(
            dashboard_cards=lambda: [],
            diagnostic_summary=lambda: {},
        ),
        _control_summary=lambda: {
            "ai": ["switch.herald_ai_enabled"],
            "levels": ["switch.herald_level_info"],
            "rooms": [
                "switch.herald_room_living_room_presence",
                "switch.herald_room_bedroom_presence",
                "select.herald_room_living_room_audio_target",
            ],
            "users": ["select.herald_user_aleksandr_meshcheriakov_language"],
            "channels": ["switch.herald_channel_push"],
            "flows": ["switch.herald_flow_system_events_enabled"],
            "router": [
                "switch.herald_maintenance_mode",
                "switch.herald_mute_all",
                "switch.herald_dashboard_sidebar",
                "select.herald_maintenance_min_level",
            ],
            "tests": [
                "button.herald_test_level_warning",
                "button.herald_test_channel_persistent_default",
            ],
        },
    )

    rendered = HeraldCoordinator._build_dashboard_yaml(fake, title="Herald Control Center", preset="rooms")

    assert "type: custom:herald-card" not in rendered
    assert "binary_sensor.herald_room_living_room_presence" in rendered
    assert "switch.herald_room_living_room_presence" in rendered
    assert "select.herald_room_living_room_audio_target" in rendered
    assert "title: Комнаты" in rendered
    assert "title: Операции" in rendered
    assert "title: Аналитика" in rendered
    assert "switch.herald_maintenance_mode" in rendered
    assert "switch.herald_mute_all" in rendered
    assert "switch.herald_dashboard_sidebar" in rendered
    assert "button.herald_test_level_warning" in rendered
    assert "select.herald_user_aleksandr_meshcheriakov_language" in rendered
    assert "sensor.herald_notification_center_deliveries_today" in rendered
    assert "sensor.herald_notification_center_ai_requests_today" in rendered


def test_dashboard_feed_is_persisted_in_snapshot() -> None:
    traces: list[dict[str, object]] = []
    state = RuntimeState(
        current_day="2026-03-08",
        queued_notifications=[
            {
                "flow": "system_events",
                "event": "queued_item",
                "title": "Queued",
                "message": "Still waiting",
                "level": "info",
                "notification_id": "queued_1",
                "channels": ["dashboard_default"],
                "timestamp": "2026-03-08T11:59:00+00:00",
                "enqueued_at": "2026-03-08T11:59:10+00:00",
                "summary_window_seconds": 60,
            }
        ],
        queue_size=1,
    )
    fake = SimpleNamespace(
        _state=state,
        config=HeraldConfig.from_raw(
            {
                "flows": {
                    "system_events": {"channels": ["dashboard_default"]},
                },
                "channels": {
                    "dashboard_default": {"type": "dashboard"},
                },
            }
        ),
        characters=SimpleNamespace(list_character_keys=lambda: ["hestia"]),
        presence=_FakePresence(),
        plugins=SimpleNamespace(
            dashboard_cards=lambda: [],
            diagnostic_summary=lambda: {},
        ),
        controls=SimpleNamespace(is_mute_all_enabled=lambda: False),
        _append_trace=lambda item: traces.append(item),
        _history_limit=lambda: 20,
        _control_summary=lambda: {
            "ai": ["switch.herald_ai_enabled"],
            "levels": ["switch.herald_level_info"],
            "rooms": ["switch.herald_room_living_room_presence"],
            "users": ["select.herald_user_aleksandr_meshcheriakov_language"],
            "channels": ["switch.herald_channel_push"],
            "flows": ["switch.herald_flow_system_events_enabled"],
            "router": [
                "switch.herald_maintenance_mode",
                "switch.herald_mute_all",
                "switch.herald_dashboard_sidebar",
                "select.herald_maintenance_min_level",
            ],
            "tests": ["button.herald_test_level_warning"],
        },
        is_flow_enabled=lambda name: True,
        _maintenance_mode_active=lambda: False,
        _runtime_status=lambda presence: "ready",
    )
    context = NotificationContext(
        flow="system_events",
        event="door_open",
        title="Door",
        message="Front door opened",
        level="warning",
        source="automation.door",
        timestamp="2026-03-08T12:00:00+00:00",
        notification_id="notif_42",
        users=["person.aleksandr_meshcheriakov"],
        room="living_room",
    )
    feed_meta = HeraldCoordinator._record_dashboard_delivery(
        fake,
        channel=ChannelConfig(name="dashboard_default", channel_type="dashboard"),
        title="Door",
        message="Front door opened",
        language="ru",
        context=context,
        presence=PresenceSnapshot(primary_room="living_room"),
    )

    snapshot = HeraldCoordinator._build_snapshot(
        fake,
        PresenceSnapshot(people_home=["person.aleksandr_meshcheriakov"], home_mode="home"),
    )

    assert feed_meta["feed_entry_id"]
    assert snapshot["dashboard_feed"][0]["channel"] == "dashboard_default"
    assert snapshot["dashboard_feed"][0]["notification_id"] == "notif_42"
    assert snapshot["dashboard_feed"][0]["room"] == "living_room"
    assert snapshot["queued_notifications"][0]["notification_id"] == "queued_1"
    assert traces[0]["stage"] == "dashboard_feed"


def test_dashboard_yaml_appends_plugin_cards() -> None:
    fake = SimpleNamespace(
        config=HeraldConfig.from_raw(
            {
                "flows": {
                    "system_events": {"channels": ["persistent_default"]},
                }
            }
        ),
        presence=_FakePresence(),
        plugins=SimpleNamespace(
            dashboard_cards=lambda: [
                {
                    "type": "markdown",
                    "title": "Plugin Diagnostics",
                    "content": "Loaded from plugin",
                }
            ],
            diagnostic_summary=lambda: {
                "ops": {"enabled": True, "dashboard_cards": 1}
            },
        ),
        _control_summary=lambda: {
            "ai": ["switch.herald_ai_enabled"],
            "levels": ["switch.herald_level_info"],
            "rooms": ["switch.herald_room_living_room_presence"],
            "users": ["select.herald_user_aleksandr_meshcheriakov_language"],
            "channels": ["switch.herald_channel_push"],
            "flows": ["switch.herald_flow_system_events_enabled"],
            "router": [
                "switch.herald_maintenance_mode",
                "switch.herald_mute_all",
                "switch.herald_dashboard_sidebar",
                "select.herald_maintenance_min_level",
            ],
            "tests": ["button.herald_test_level_warning"],
        },
    )

    rendered = HeraldCoordinator._build_dashboard_yaml(fake, title="Herald Control Center", preset="overview")

    assert "Plugin Diagnostics" in rendered
    assert "Loaded from plugin" in rendered
    assert "title: Диагностика" in rendered
