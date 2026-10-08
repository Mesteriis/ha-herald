"""Delivery boundaries and file export regression tests."""
import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.herald.coordinator import HeraldCoordinator
from custom_components.herald.models import HeraldConfig, NotificationContext, PresenceSnapshot
from custom_components.herald.router import HeraldRouter


def context(**kwargs):
    return replace(NotificationContext(flow="system_events", title="Test", message="Message", level="warning", source="test", timestamp="2026-09-30T12:00:00+00:00", rewrite=False), **kwargs)


def router_for(channels, *, people_home=None, states=None, away=None, presence_config=None, occupied=None, absence_confirmed=False):
    config = HeraldConfig.from_raw({"channels": channels, "flows": {"system_events": {"channels": list(channels)}}, "presence": presence_config or {}})
    presence = PresenceSnapshot(people_home=people_home or [], nobody_home=not people_home, absence_confirmed=absence_confirmed, occupied_rooms=occupied or [], primary_room="office")
    hass = SimpleNamespace(states=SimpleNamespace(get=lambda key: (states or {}).get(key)), services=SimpleNamespace(async_call=AsyncMock()))
    controls = SimpleNamespace(is_channel_type_enabled=lambda _: True, room_audio_target=lambda *args, **kwargs: "auto", user_language=lambda *args, **kwargs: "en", user_character=lambda *args, **kwargs: "hestia")
    resolver = SimpleNamespace(async_resolve=AsyncMock(return_value=presence), away_channels=lambda: away or [])
    ai = SimpleNamespace(async_rewrite_payload=AsyncMock(return_value={"title": "Test", "message": "Message"}))
    return HeraldRouter(hass, config, ai, resolver, controls), config.flows["system_events"], presence


def test_explicit_empty_channels_cannot_fall_back_to_flow():
    router, flow, presence = router_for({"tray": {"type": "persistent_notification"}})
    assert router._resolve_channel_names(context(channels=[], metadata={"channels_explicit": True}), flow, presence) == []


def test_flow_channel_override_preserves_default_severity_and_summary_policy():
    flow = HeraldConfig.from_raw({"flows": {"security_alerts": {"channels": ["voice_auto"]}}}).flows["security_alerts"]
    assert flow.channels == ["voice_auto"]
    assert flow.severity == "security"
    assert flow.allow_summary is False


def test_away_route_cannot_widen_explicit_channels():
    router, flow, presence = router_for({"tray": {"type": "persistent_notification"}, "other": {"type": "telegram"}}, away=["other"])
    assert router._resolve_channel_names(context(channels=["tray"], metadata={"channels_explicit": True}), flow, presence) == []


@pytest.mark.parametrize("bad", [{"enabled": False}, {"min_level": "critical"}])
def test_ineligible_local_channel_cannot_displace_working_channel(bad):
    channels = {
        "a": {"type": "tts", "room": "office", "entity_id": "media_player.a", **bad},
        "b": {"type": "tts", "room": "office", "entity_id": "media_player.b"},
    }
    router, flow, presence = router_for(channels, people_home=["person.alice"])
    assert router._resolve_channel_names(context(room="office"), flow, presence) == ["b"]


def test_mixed_household_targets_away_mobile_and_local_voice():
    router, flow, presence = router_for({
        "alice": {"type": "mobile_app", "user": "alice", "service": "notify.alice"},
        "bob": {"type": "mobile_app", "user": "bob", "service": "notify.bob"},
        "speaker": {"type": "tts", "room": "office", "entity_id": "media_player.office"},
    }, people_home=["person.alice"])
    ctx = context(users=["person.alice", "person.bob"], metadata={"audience_resolved": True})
    assert set(router._resolve_channel_names(ctx, flow, presence)) == {"bob", "speaker"}


def test_occupied_rooms_receive_separate_voice_and_active_tv_while_remote_stays_away_only():
    channels = {
        "voice_auto": {"type": "tts", "entity_id": "media_player.fallback"},
        "voice_bedroom": {"type": "tts", "room": "bedroom", "entity_id": "media_player.bedroom", "data": {"audio_targets": {"bedroom": [{"kind": "alisa", "entity_id": "media_player.bedroom", "service": "tts.yandex_station_say"}]}}},
        "voice_living_room": {"type": "tts", "room": "living_room", "entity_id": "media_player.living", "data": {"audio_targets": {"living_room": [{"kind": "alisa", "entity_id": "media_player.living", "service": "tts.yandex_station_say"}]}}},
        "tv_living_room": {"type": "tv", "room": "living_room", "entity_id": "media_player.tv", "service": "notify.livingroom_tv", "data": {"active_only": True}},
        "phone": {"type": "mobile_app", "service": "notify.phone"},
        "telegram": {"type": "telegram", "service": "notify.send_message", "entity_id": "notify.telegram"},
    }
    states = {name: SimpleNamespace(state="idle") for name in ("media_player.bedroom", "media_player.living")}
    states["media_player.tv"] = SimpleNamespace(state="playing")
    router, flow, presence = router_for(
        channels, people_home=["person.alice"], states=states,
        presence_config={"occupied_room_routing": True, "remote_channels_away_only": True},
        occupied=["bedroom", "living_room"],
    )
    flow.channels = ["voice_auto", "phone", "telegram"]
    selected = router._resolve_channel_names(context(), flow, presence)
    assert set(selected) == {"voice_bedroom", "voice_living_room", "tv_living_room"}
    inferred_room = context(room="bedroom", metadata={"room_explicit": False})
    assert set(router._resolve_channel_names(inferred_room, flow, presence)) == set(selected)
    explicit_room = context(room="bedroom", metadata={"room_explicit": True})
    assert router._resolve_channel_names(explicit_room, flow, presence) == ["voice_bedroom"]
    preview = router.build_route_preview(context(), flow, presence)
    assert {item["target_entity_id"] for item in preview["deliveries"]} == {
        "media_player.bedroom", "media_player.living", "media_player.tv",
    }
    assert {item["reason"] for item in preview["channel_decisions"] if not item["selected"]} == {"presence"}

    states["media_player.tv"] = SimpleNamespace(state="off")
    assert set(router._resolve_channel_names(context(), flow, presence)) == {"voice_bedroom", "voice_living_room"}

    presence.people_home = []
    presence.nobody_home = True
    presence.absence_confirmed = True
    presence.occupied_rooms = []
    assert set(router._resolve_channel_names(context(), flow, presence)) == {"phone", "telegram"}
    presence.absence_confirmed = False
    assert router._resolve_channel_names(context(), flow, presence) == []


@pytest.mark.asyncio
async def test_away_only_remote_channel_cannot_be_forced_at_home():
    router, flow, presence = router_for({"phone": {"type": "mobile_app", "service": "notify.phone"}},
        people_home=["person.alice"], presence_config={"remote_channels_away_only": True})
    ctx = context(channels=["phone"], metadata={"channels_explicit": True, "bypass_channel_policy": True})
    assert router._resolve_channel_names(ctx, flow, presence) == []
    assert await router.async_route(ctx, flow) == []
    router._hass.services.async_call.assert_not_awaited()


def test_remote_allowlist_rejects_old_explicit_app_channel():
    router, flow, presence = router_for({
        "old_phone": {"type": "mobile_app", "service": "notify.old_phone"},
        "phone": {"type": "mobile_app", "service": "notify.phone"},
    }, presence_config={"remote_channels_away_only": True, "allowed_remote_channels": ["phone"]},
        absence_confirmed=True)
    ctx = context(channels=["old_phone", "phone"], metadata={"channels_explicit": True})
    assert router._resolve_channel_names(ctx, flow, presence) == ["phone"]


@pytest.mark.asyncio
async def test_telegram_notify_entity_uses_notify_send_message_schema():
    router, _, presence = router_for({"telegram": {"type": "telegram", "service": "notify.send_message", "entity_id": "notify.telegram"}})
    result = await router._async_send_telegram(router._config.channels["telegram"], "Title", "Body", context(), presence, "ru")
    assert result["target_entity_id"] == "notify.telegram"
    assert router._hass.services.async_call.await_args.args[:3] == (
        "notify", "send_message", {"entity_id": "notify.telegram", "title": "Title", "message": "Body"},
    )


def test_explicit_away_audience_does_not_play_local_speech():
    router, flow, presence = router_for({"speaker": {"type": "tts", "entity_id": "media_player.office"}}, people_home=["person.alice"])
    ctx = context(users=["person.bob"], user="person.bob", metadata={"audience_explicit": True, "audience_resolved": True})
    assert router._resolve_channel_names(ctx, flow, presence) == []


def test_all_silent_users_do_not_enable_default_local_audience():
    router, flow, presence = router_for({"speaker": {"type": "tts"}, "phone": {"type": "mobile_app", "user": "alice"}}, people_home=["person.alice"])
    ctx = context(metadata={"audience_resolved": True}, context_data={"users": [{"slug": "alice", "silent": True, "home": True}]})
    assert router._resolve_channel_names(ctx, flow, presence) == []


@pytest.mark.asyncio
async def test_preview_and_delivery_both_reject_disabled_channel():
    router, flow, presence = router_for({"tray": {"type": "persistent_notification", "enabled": False}})
    assert router.build_route_preview(context(), flow, presence)["deliveries"] == []
    assert await router.async_route(context(), flow) == []
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_tts_fallback_and_service_payload_exclude_routing_metadata():
    router, _, _ = router_for({"voice": {"type": "tts", "data": {
        "room_targets": {"office": "media_player.a"},
        "audio_targets": {"office": [
            {"kind": "alisa", "entity_id": "media_player.a", "service": "tts.say"},
            {"kind": "homepod", "entity_id": "media_player.b", "service": "tts.speak", "engine_entity_id": "tts.engine"},
        ]},
    }}}, states={key: SimpleNamespace(state="idle") for key in ["media_player.a", "media_player.b"]})
    router._hass.services.async_call.side_effect = [ValueError("Rejected"), None]
    result = await router._async_send_tts(router._config.channels["voice"], "Test", "Message", context(room="office"), delivery_room="office")
    calls = router._hass.services.async_call.await_args_list
    assert result["target_entity_id"] == "media_player.b"
    assert result["attempted_targets"] == ["media_player.a", "media_player.b"]
    assert set(calls[0].args[2]) == {"message", "entity_id", "cache"}
    assert calls[1].args[2]["entity_id"] == "tts.engine"
    assert calls[1].args[2]["media_player_entity_id"] == "media_player.b"


@pytest.mark.asyncio
async def test_tts_does_not_retry_ambiguous_timeout():
    router, _, _ = router_for({"voice": {"type": "tts", "data": {"audio_targets": {"office": [
        {"entity_id": "media_player.a"}, {"entity_id": "media_player.b"},
    ]}}}}, states={key: SimpleNamespace(state="idle") for key in ["media_player.a", "media_player.b"]})
    router._hass.services.async_call.side_effect = TimeoutError()
    with pytest.raises(TimeoutError):
        await router._async_send_tts(router._config.channels["voice"], "Test", "Message", context(), delivery_room="office")
    assert router._hass.services.async_call.await_count == 1


@pytest.mark.asyncio
async def test_service_call_timeout_does_not_hold_notification_queue(monkeypatch):
    router, _, _ = router_for({"voice": {"type": "tts", "service": "tts.yandex_station_say", "entity_id": "media_player.office"}})
    monkeypatch.setattr("custom_components.herald.router._SERVICE_CALL_TIMEOUT_SECONDS", 0.01)
    never_returns = asyncio.Event()

    async def stalled_service(*args, **kwargs):
        await never_returns.wait()

    router._hass.services.async_call.side_effect = stalled_service
    with pytest.raises(TimeoutError):
        await router._async_call_service("tts.yandex_station_say", {"message": "test"})
    assert router._hass.services.async_call.await_count == 1


@pytest.mark.parametrize("path", ["../escape.yaml", "/tmp/escape.yaml", "configuration.yaml", "dashboards/file.py", "dashboards/../configuration.yaml"])
def test_dashboard_export_rejects_escape(tmp_path, path):
    with pytest.raises(ValueError):
        HeraldCoordinator._write_dashboard_file(str(tmp_path), path, "content")
    assert list(tmp_path.iterdir()) == []


def test_dashboard_export_rejects_symlinks_and_writes_valid_yaml(tmp_path):
    outside = tmp_path / "other"
    outside.mkdir()
    (tmp_path / "dashboards").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        HeraldCoordinator._write_dashboard_file(str(tmp_path), "dashboards/herald.yaml", "content")
    (tmp_path / "dashboards").unlink()
    path = HeraldCoordinator._write_dashboard_file(str(tmp_path), "dashboards/herald.yaml", "title: Herald\n")
    from pathlib import Path
    assert Path(path).read_text() == "title: Herald\n"
    (tmp_path / "dashboards" / "escape.yaml").symlink_to(outside / "target.yaml")
    with pytest.raises(ValueError):
        HeraldCoordinator._write_dashboard_file(str(tmp_path), "dashboards/escape.yaml", "content")
