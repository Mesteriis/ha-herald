"""Tests for portable runtime channel discovery from Home Assistant registries."""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from custom_components.herald.discovery import async_discover_runtime_channels, discover_runtime_channels


def _state(entity_id, state="idle", **attributes):
    return SimpleNamespace(entity_id=entity_id, state=state, attributes=attributes)


def _entry(entry_id, domain, **kwargs):
    return SimpleNamespace(entry_id=entry_id, domain=domain, disabled_by=None, data={}, subentries={}, **kwargs)


def _hass(tmp_path, *, entries=()):
    states = {
        item.entity_id: item for item in (
            _state("tts.local_engine"),
            _state("media_player.yandex_station_synthetic", friendly_name="Living Room speaker"),
            _state("media_player.homepod_living_room", friendly_name="HomePod", model="HomePod mini"),
            _state("media_player.tv", state="playing", friendly_name="TV"),
            _state("person.alice", state="home", device_trackers=["device_tracker.renamed_phone"]),
        )
    }
    services = {"notify": {"mobile_app_portable_phone": {}, "tv": {}}, "tts": {"speak": {}, "yandex_station_say": {}}, "telegram_bot": {"send_message": {}}}
    return SimpleNamespace(states=SimpleNamespace(get=states.get, async_all=lambda domain: [state for key, state in states.items() if key.startswith(domain + ".")]), services=SimpleNamespace(async_services=lambda: services), config=SimpleNamespace(path=lambda path: str(tmp_path / path)), config_entries=SimpleNamespace(async_entries=lambda domain: [entry for entry in entries if entry.domain == domain]), raw_states=states, raw_services=services)


def _registries(monkeypatch):
    entities = {
        "media_player.tv": SimpleNamespace(entity_id="media_player.tv", device_id="tv-device", area_id=None, config_entry_id="tv-entry"),
        "media_player.homepod_living_room": SimpleNamespace(entity_id="media_player.homepod_living_room", device_id=None, area_id="living_room", config_entry_id="homepod-entry"),
        "device_tracker.renamed_phone": SimpleNamespace(entity_id="device_tracker.renamed_phone", device_id="phone-device", area_id=None, config_entry_id="tracker-entry"),
    }
    devices = {
        "tv-device": SimpleNamespace(area_id="living_room", config_entries={"tv-entry"}),
        "phone-device": SimpleNamespace(area_id=None, config_entries={"mobile-entry", "tracker-entry"}),
    }
    monkeypatch.setattr("custom_components.herald.discovery.er.async_get", lambda hass: SimpleNamespace(entities=entities))
    monkeypatch.setattr("custom_components.herald.discovery.dr.async_get", lambda hass: SimpleNamespace(async_get=devices.get))
    return entities, devices


def _mobile_entry():
    entry = _entry("mobile-entry", "mobile_app")
    entry.data = {"device_name": "Portable Phone", "token": "synthetic-secret-not-read"}
    return entry


def _telegram_entry(chat_ids):
    entry = _entry("telegram-entry", "telegram_bot")
    entry.subentries = {str(index): SimpleNamespace(subentry_type="allowed_chat_ids", data={"chat_id": chat_id}) for index, chat_id in enumerate(chat_ids)}
    return entry


def test_discovery_uses_registered_services_and_exact_registry_ownership(tmp_path, monkeypatch) -> None:
    _registries(monkeypatch)
    hass = _hass(tmp_path, entries=[_mobile_entry(), _telegram_entry([-100123])])
    channels = discover_runtime_channels(hass)
    assert channels["mobile_portable_phone"]["service"] == "notify.mobile_app_portable_phone"
    assert channels["mobile_portable_phone"]["user"] == "alice"
    assert len([channel for channel in channels.values() if channel["type"] == "mobile_app"]) == 1
    assert channels["telegram_default"]["data"] == {"config_entry_id": "telegram-entry"}
    assert channels["telegram_default"]["chat_id"] == -100123
    assert channels["tv_auto"]["service"] == "notify.tv"
    assert channels["tv_auto"]["data"]["delivery"] == "overlay"
    assert channels["tv_living_room"]["entity_id"] == "media_player.tv"
    assert [target["kind"] for target in channels["voice_auto"]["data"]["audio_targets"]["living_room"]] == ["alisa", "homepod"]
    assert channels["voice_auto"]["entity_id"] == "media_player.yandex_station_synthetic"


def test_discovery_does_not_invent_mobile_or_voice_services(tmp_path, monkeypatch) -> None:
    _registries(monkeypatch)
    hass = _hass(tmp_path, entries=[_mobile_entry()])
    hass.raw_services.clear()
    assert discover_runtime_channels(hass) == {}


def test_discovery_keeps_ambiguous_mobile_owner_unassigned(tmp_path, monkeypatch) -> None:
    _registries(monkeypatch)
    hass = _hass(tmp_path, entries=[_mobile_entry()])
    hass.raw_states["person.bob"] = _state("person.bob", device_trackers=["device_tracker.renamed_phone"])
    assert "user" not in discover_runtime_channels(hass)["mobile_portable_phone"]


def test_discovery_keeps_colliding_mobile_services_unassigned(tmp_path, monkeypatch) -> None:
    _registries(monkeypatch)
    second = _mobile_entry()
    second.entry_id = "other-entry"
    hass = _hass(tmp_path, entries=[_mobile_entry(), second])
    assert "user" not in discover_runtime_channels(hass)["mobile_portable_phone"]


def test_discovery_requires_unambiguous_telegram_chat(tmp_path, monkeypatch) -> None:
    _registries(monkeypatch)
    hass = _hass(tmp_path, entries=[_telegram_entry([-100123, -100456])])
    assert "telegram_default" not in discover_runtime_channels(hass)


@pytest.mark.asyncio
async def test_live_discovery_never_reads_secret_or_storage_files(tmp_path, monkeypatch) -> None:
    _registries(monkeypatch)
    hass = _hass(tmp_path, entries=[_mobile_entry(), _telegram_entry([-100123])])
    read = Mock(side_effect=AssertionError("live discovery must not read any files"))
    monkeypatch.setattr(Path, "read_text", read)
    channels = await async_discover_runtime_channels(hass)
    assert channels["mobile_portable_phone"]["user"] == "alice"
    read.assert_not_called()


@pytest.mark.asyncio
async def test_discovery_fallback_file_io_stays_in_executor(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("custom_components.herald.discovery.er.async_get", lambda hass: None)
    monkeypatch.setattr("custom_components.herald.discovery.dr.async_get", lambda hass: None)
    storage = tmp_path / ".storage"
    storage.mkdir()
    (storage / "core.entity_registry").write_text(json.dumps({"data": {"entities": [{"entity_id": "media_player.tv", "area_id": "living_room"}]}}))
    hass = _hass(tmp_path)
    thread_ids = []
    original_read = Path.read_text
    def read(path, *args, **kwargs):
        assert path.name in {"core.entity_registry", "core.device_registry"}
        thread_ids.append(threading.get_ident())
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read)
    async def execute(func, *args):
        return await asyncio.get_running_loop().run_in_executor(None, func, *args)
    hass.async_add_executor_job = execute
    channels = await async_discover_runtime_channels(hass)
    assert channels["tv_living_room"]["entity_id"] == "media_player.tv"
    assert thread_ids and all(thread_id != threading.get_ident() for thread_id in thread_ids)


def test_renamed_yandex_entity_is_discovered_from_platform_registry(tmp_path, monkeypatch) -> None:
    entities, _ = _registries(monkeypatch)
    entities["media_player.speaker"] = SimpleNamespace(entity_id="media_player.speaker", platform="yandex_station", area_id="office", device_id=None, config_entry_id="voice-entry")
    hass = _hass(tmp_path)
    hass.raw_states["media_player.speaker"] = _state("media_player.speaker")
    channels = discover_runtime_channels(hass)
    assert channels["voice_auto"]["data"]["room_targets"]["office"] == "media_player.speaker"


def test_discovery_resolves_opaque_area_ids_using_area_names(tmp_path, monkeypatch) -> None:
    entities, _ = _registries(monkeypatch)
    entities["media_player.homepod_living_room"].area_id = "opaque-area-id"
    monkeypatch.setattr("custom_components.herald.discovery.ar.async_get", lambda hass: SimpleNamespace(async_get_area=lambda area_id: SimpleNamespace(name="Guest Room") if area_id == "opaque-area-id" else None))
    channels = discover_runtime_channels(_hass(tmp_path))
    assert channels["voice_auto"]["data"]["room_targets"]["guest_room"] == "media_player.homepod_living_room"


def test_discovery_uses_current_device_entry_id_without_deprecated_property(tmp_path, monkeypatch) -> None:
    _, devices = _registries(monkeypatch)
    class CurrentDevice:
        area_id = None
        config_entry_id = "mobile-entry"
        @property
        def config_entries(self):
            raise AssertionError("deprecated shim must not be read")
    devices["phone-device"] = CurrentDevice()
    channels = discover_runtime_channels(_hass(tmp_path, entries=[_mobile_entry()]))
    assert channels["mobile_portable_phone"]["user"] == "alice"


@pytest.mark.asyncio
async def test_discovery_falls_back_when_registry_is_not_loaded(tmp_path, monkeypatch) -> None:
    def unavailable(hass):
        raise RuntimeError("registry has not loaded")
    monkeypatch.setattr("custom_components.herald.discovery.er.async_get", unavailable)
    hass = _hass(tmp_path)
    from unittest.mock import AsyncMock
    hass.async_add_executor_job = AsyncMock(return_value={"media_player_rooms": {}})
    channels = await async_discover_runtime_channels(hass)
    hass.async_add_executor_job.assert_awaited_once()
    assert "mobile_portable_phone" in channels
