"""Tests for runtime channel discovery."""

from __future__ import annotations

from pathlib import Path

from custom_components.herald.discovery import discover_runtime_channels


class _State:
    def __init__(self, state: str = "unknown", attributes=None):
        self.state = state
        self.attributes = attributes or {}


class _States:
    def __init__(self, entities: dict[str, _State]) -> None:
        self._entities = entities

    def get(self, entity_id: str):
        return self._entities.get(entity_id)


class _Services:
    def __init__(self, payload):
        self._payload = payload

    def async_services(self):
        return self._payload


class _Config:
    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, value: str) -> str:
        return str(self._root / value)


class _Hass:
    def __init__(self, root: Path) -> None:
        self.states = _States(
            {
                "group.voice_notification_targets": _State(),
                "tts.google_translate_en_com": _State(),
                "media_player.yandex_station_x11jdn200bwyse": _State(state="idle", attributes={"friendly_name": "Living Room Alice"}),
                "media_player.homepod_living_room": _State(state="playing", attributes={"friendly_name": "Living Room HomePod", "model": "HomePod mini"}),
                "media_player.tv": _State(state="playing", attributes={"friendly_name": "TV"}),
            }
        )
        self.services = _Services(
            {
                "notify": {
                    "mobile_app_macbook": {},
                },
                "telegram_bot": {
                    "send_message": {},
                },
            }
        )
        self.config = _Config(root)


def test_discovery_uses_existing_telegram_and_mobile_settings(tmp_path: Path) -> None:
    (tmp_path / "secrets.yaml").write_text(
        "\n".join(
            [
                'telegram_bot_entry_id: "entry-1"',
                'telegram_history_chat_id: "-100123"',
                'telegram_history_iot_thread_id: "48"',
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".storage").mkdir()
    (tmp_path / ".storage/core.config_entries").write_text('{"data":{"entries":[]}}', encoding="utf-8")
    (tmp_path / ".storage/core.device_registry").write_text(
        (
            '{"data":{"devices":['
            '{"id":"device-tv","area_id":"gostinaia"}'
            "]}}"
        ),
        encoding="utf-8",
    )
    (tmp_path / ".storage/core.entity_registry").write_text(
        (
            '{"data":{"entities":['
            '{"entity_id":"media_player.tv","device_id":"device-tv"}'
            "]}}"
        ),
        encoding="utf-8",
    )

    channels = discover_runtime_channels(_Hass(tmp_path))

    assert channels["voice_auto"]["entity_id"] == "group.voice_notification_targets"
    assert channels["mobile_macbook"]["service"] == "notify.mobile_app_macbook"
    assert channels["telegram_default"]["data"]["config_entry_id"] == "entry-1"
    assert channels["telegram_default"]["chat_id"] == -100123
    assert channels["telegram_default"]["thread_id"] == 48
    assert channels["tv_auto"]["service"] == "tts.speak"
    assert channels["tv_auto"]["data"]["engine_entity_id"] == "tts.google_translate_en_com"
    assert channels["tv_auto"]["data"]["room_targets"]["living_room"] == "media_player.tv"
    assert channels["tv_living_room"]["entity_id"] == "media_player.tv"
    assert channels["voice_auto"]["data"]["audio_targets"]["living_room"][0]["kind"] == "alisa"
    assert channels["voice_auto"]["data"]["audio_targets"]["living_room"][1]["kind"] == "homepod"


def test_discovery_builds_room_audio_targets_only_for_known_media_rooms(tmp_path: Path) -> None:
    (tmp_path / "secrets.yaml").write_text("{}", encoding="utf-8")
    (tmp_path / ".storage").mkdir()
    (tmp_path / ".storage/core.config_entries").write_text('{"data":{"entries":[]}}', encoding="utf-8")
    (tmp_path / ".storage/core.device_registry").write_text(
        (
            '{"data":{"devices":['
            '{"id":"device-homepod","area_id":"gostinaia"},'
            '{"id":"device-tv","area_id":"gostinaia"}'
            "]}}"
        ),
        encoding="utf-8",
    )
    (tmp_path / ".storage/core.entity_registry").write_text(
        (
            '{"data":{"entities":['
            '{"entity_id":"media_player.homepod_living_room","device_id":"device-homepod"},'
            '{"entity_id":"media_player.tv","device_id":"device-tv"}'
            "]}}"
        ),
        encoding="utf-8",
    )

    channels = discover_runtime_channels(_Hass(tmp_path))

    assert "living_room" in channels["voice_auto"]["data"]["audio_targets"]
    assert [item["kind"] for item in channels["voice_auto"]["data"]["audio_targets"]["living_room"]] == [
        "alisa",
        "homepod",
        "tv",
    ]
