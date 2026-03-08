"""Tests for Herald-owned runtime controls."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.herald.controls import (
    HeraldControlManager,
    ai_enabled_control_key,
    channel_enabled_control_key,
    channel_min_level_control_key,
    channel_test_button_key,
    dashboard_sidebar_control_key,
    flow_enabled_control_key,
    flow_summary_window_control_key,
    level_test_button_key,
    maintenance_mode_control_key,
    mute_all_control_key,
    room_audio_target_control_key,
    room_presence_control_key,
    user_language_control_key,
)
from custom_components.herald.models import HeraldConfig, RuntimeState
from custom_components.herald.presence import PresenceResolver


class _FakeStates:
    def __init__(self, mapping: dict[str, str], attributes: dict[str, dict] | None = None) -> None:
        self._mapping = mapping
        self._attributes = attributes or {}

    def get(self, entity_id: str):
        state = self._mapping.get(entity_id)
        if state is None:
            return None
        return SimpleNamespace(
            state=state,
            entity_id=entity_id,
            attributes=self._attributes.get(entity_id, {}),
        )

    def async_all(self, domain: str | None = None):
        entities = []
        for entity_id, state in self._mapping.items():
            if domain is not None and not entity_id.startswith(f"{domain}."):
                continue
            entities.append(
                SimpleNamespace(
                    state=state,
                    entity_id=entity_id,
                    attributes=self._attributes.get(entity_id, {}),
                )
            )
        return entities


class _FakeHass:
    def __init__(self, mapping: dict[str, str], attributes: dict[str, dict] | None = None) -> None:
        self.states = _FakeStates(mapping, attributes)


class _FakeCharacterProfile:
    def __init__(self, key: str) -> None:
        self.key = key


class _FakeCharacters:
    def list_character_keys(self) -> list[str]:
        return ["hestia", "domovoy"]

    def get(self, key: str | None):
        return _FakeCharacterProfile("hestia")


def test_controls_build_dynamic_specs_and_migrate_legacy_values() -> None:
    hass = _FakeHass(
        {
            "person.aleksandr_meshcheriakov": "home",
            "binary_sensor.room_gostinaia_occupied": "on",
            "input_boolean.herald_ai_enabled": "off",
            "input_select.herald_user_aleksandr_meshcheriakov_language": "en",
        },
        {"person.aleksandr_meshcheriakov": {"friendly_name": "Aleksandr Meshcheriakov"}},
    )
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "alex_phone": {
                    "type": "mobile_app",
                    "service": "notify.mobile_app_alex",
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["alex_phone"],
                }
            },
        }
    )
    state = RuntimeState(current_day="2026-03-08", flow_overrides={"system_events": False})
    presence = PresenceResolver(hass, config)
    controls = HeraldControlManager(hass, config, presence, _FakeCharacters(), lambda: state)

    changed = controls.ensure_defaults()
    summary = controls.summary()

    assert changed is True
    assert "switch.herald_room_living_room_presence" in summary["rooms"]
    assert "select.herald_user_aleksandr_meshcheriakov_language" in summary["users"]
    assert "switch.herald_maintenance_mode" in summary["router"]
    assert "switch.herald_mute_all" in summary["router"]
    assert "switch.herald_dashboard_sidebar" in summary["router"]
    assert "button.herald_test_level_warning" in summary["tests"]
    assert "button.herald_test_channel_alex_phone" in summary["tests"]
    assert state.control_values[ai_enabled_control_key()] is False
    assert state.control_values[maintenance_mode_control_key()] is False
    assert state.control_values[mute_all_control_key()] is False
    assert state.control_values[dashboard_sidebar_control_key()] is True
    assert state.control_values[user_language_control_key("aleksandr_meshcheriakov")] == "en"
    assert state.control_values[flow_enabled_control_key("system_events")] is False
    assert config.flows["system_events"].enabled is False


def test_controls_sync_runtime_config_updates_channel_and_flow_values() -> None:
    hass = _FakeHass({})
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "alex_phone": {
                    "type": "mobile_app",
                    "service": "notify.mobile_app_alex",
                    "min_level": "info",
                }
            },
            "flows": {
                "device_alerts": {
                    "channels": ["alex_phone"],
                    "summary_window_seconds": 60,
                }
            },
        }
    )
    state = RuntimeState(current_day="2026-03-08")
    presence = PresenceResolver(hass, config)
    controls = HeraldControlManager(hass, config, presence, _FakeCharacters(), lambda: state)
    controls.ensure_defaults()

    assert controls.set_value(channel_enabled_control_key("alex_phone"), False) is True
    assert controls.set_value(channel_min_level_control_key("alex_phone"), "critical") is True
    assert controls.set_value(flow_summary_window_control_key("device_alerts"), 180) is True

    assert config.channels["alex_phone"].enabled is False
    assert config.channels["alex_phone"].min_level == "critical"
    assert config.flows["device_alerts"].summary_window_seconds == 180


def test_controls_room_presence_fallback_is_read_from_control_state() -> None:
    hass = _FakeHass({})
    config = HeraldConfig()
    state = RuntimeState(current_day="2026-03-08")
    presence = PresenceResolver(hass, config)
    controls = HeraldControlManager(hass, config, presence, _FakeCharacters(), lambda: state)
    controls.ensure_defaults()

    controls.set_value(room_presence_control_key("living_room"), True)

    assert controls.room_presence("living_room") is True


def test_controls_define_button_specs_without_persisted_values() -> None:
    hass = _FakeHass({})
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "alex_phone": {
                    "type": "mobile_app",
                    "service": "notify.mobile_app_alex",
                }
            }
        }
    )
    state = RuntimeState(current_day="2026-03-08")
    presence = PresenceResolver(hass, config)
    controls = HeraldControlManager(hass, config, presence, _FakeCharacters(), lambda: state)

    controls.ensure_defaults()

    assert controls.spec(level_test_button_key("critical")) is not None
    assert controls.spec(channel_test_button_key("alex_phone")) is not None
    assert level_test_button_key("critical") not in state.control_values
    assert channel_test_button_key("alex_phone") not in state.control_values


def test_controls_create_room_audio_select_only_for_rooms_with_multiple_targets() -> None:
    hass = _FakeHass(
        {
            "binary_sensor.room_gostinaia_occupied": "on",
        }
    )
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "voice_auto": {
                    "type": "tts",
                    "service": "tts.yandex_station_say",
                    "data": {
                        "audio_targets": {
                            "living_room": [
                                {"kind": "alisa", "entity_id": "media_player.alisa_living_room"},
                                {"kind": "homepod", "entity_id": "media_player.homepod_living_room"},
                            ],
                            "bedroom": [
                                {"kind": "alisa", "entity_id": "media_player.alisa_bedroom"},
                            ],
                        }
                    },
                }
            }
        }
    )
    state = RuntimeState(current_day="2026-03-08")
    presence = PresenceResolver(hass, config)
    controls = HeraldControlManager(hass, config, presence, _FakeCharacters(), lambda: state)

    changed = controls.ensure_defaults()
    summary = controls.summary()

    assert changed is True
    assert "select.herald_room_living_room_audio_target" in summary["rooms"]
    assert "select.herald_room_bedroom_audio_target" not in summary["rooms"]
    assert state.control_values[room_audio_target_control_key("living_room")] == "auto"
