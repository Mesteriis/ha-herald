"""Tests for Herald routing helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from custom_components.herald.models import HeraldConfig, NotificationContext, PresenceSnapshot
from custom_components.herald.router import HeraldRouter


class _FakeStates:
    def __init__(self, entities=None) -> None:
        self._entities = entities or {}

    def get(self, entity_id: str):
        return self._entities.get(entity_id)


class _FakeState:
    def __init__(self, state: str, attributes=None) -> None:
        self.state = state
        self.attributes = attributes or {}


class _FakeServices:
    def __init__(self) -> None:
        self.async_call = AsyncMock()


class _FakeHass:
    def __init__(self, entities=None) -> None:
        self.states = _FakeStates(entities)
        self.services = _FakeServices()


class _FakeControls:
    def __init__(
        self,
        *,
        channel_type_enabled: bool = True,
        room_audio_targets: dict[str, str] | None = None,
    ) -> None:
        self._channel_type_enabled = channel_type_enabled
        self._room_audio_targets = room_audio_targets or {}

    def is_channel_type_enabled(self, channel_type: str) -> bool:
        return self._channel_type_enabled

    def user_language(self, user_slug: str, *, default: str = "ru") -> str:
        return default

    def user_character(self, user_slug: str, *, default: str | None = None) -> str:
        return default or "hestia"

    def room_audio_target(self, room_name: str, *, default: str = "auto") -> str:
        return self._room_audio_targets.get(room_name, default)


class _FakePresence:
    def __init__(self, snapshot: PresenceSnapshot) -> None:
        self._snapshot = snapshot

    async def async_resolve(self, context: NotificationContext) -> PresenceSnapshot:
        return self._snapshot

    def away_channels(self) -> list[str]:
        return []


def test_quiet_hours_override_allows_tts_channel() -> None:
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
                    "channels": ["bedroom_tts"],
                }
            },
        }
    )
    snapshot = PresenceSnapshot(quiet_hours=True, people_home=["person.alex"], primary_room="bedroom")
    router = HeraldRouter(_FakeHass(), config, AsyncMock(), _FakePresence(snapshot), _FakeControls())
    context = NotificationContext(
        flow="system_events",
        title="System",
        message="Night summary",
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
    )

    channel_names = router._resolve_channel_names(context, config.flows["system_events"], snapshot)

    assert channel_names == ["bedroom_tts"]


def test_mobile_actions_contain_notification_feedback_tokens() -> None:
    config = HeraldConfig.from_raw(None)
    router = HeraldRouter(
        _FakeHass(),
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot()),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="security_alerts",
        title="Door",
        message="Front door opened",
        level="warning",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        notification_id="notif_123",
        include_actions=True,
    )

    actions = router._build_mobile_actions(context, "en")

    assert actions[0]["title"] == "Acknowledge"
    assert actions[0]["action"] == "ack|notif_123"
    assert actions[1]["action"] == "snz|security_alerts|30|notif_123"


def test_channel_min_level_drops_send() -> None:
    hass = _FakeHass()
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "alex_phone": {
                    "type": "mobile_app",
                    "service": "notify.mobile_app_alex",
                    "min_level": "critical",
                }
            },
            "flows": {
                "device_alerts": {
                    "channels": ["alex_phone"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot()),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="device_alerts",
        title="Power",
        message="Spike detected",
        level="warning",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["alex_phone"],
            title="Power",
            message="Spike detected",
            language="en",
            context=context,
            flow=config.flows["device_alerts"],
            presence=PresenceSnapshot(),
            delivery_room=None,
        )
    )

    assert result["status"] == "dropped"
    assert result["reason"] == "channel_min_level"
    hass.services.async_call.assert_not_awaited()


def test_direct_channel_test_bypasses_disabled_channel_type_and_min_level() -> None:
    hass = _FakeHass()
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "alex_phone": {
                    "type": "mobile_app",
                    "service": "notify.mobile_app_alex",
                    "enabled": False,
                    "min_level": "critical",
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["alex_phone"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot()),
        _FakeControls(channel_type_enabled=False),
    )
    context = NotificationContext(
        flow="system_events",
        title="Channel Test",
        message="Herald control-plane test",
        level="info",
        source="herald.control_test.channel",
        timestamp="2026-03-08T11:00:00+00:00",
        channels=["alex_phone"],
        force=True,
        metadata={
            "control_test": "channel",
            "control_test_channel": "alex_phone",
        },
    )

    channel_names = router._resolve_channel_names(context, config.flows["system_events"], PresenceSnapshot())
    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["alex_phone"],
            title="Channel Test",
            message="Herald control-plane test",
            language="en",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(),
            delivery_room=None,
        )
    )

    assert router._channel_available_for_context(config.channels["alex_phone"], context) is True
    assert channel_names == ["alex_phone"]
    assert result["status"] == "sent"
    hass.services.async_call.assert_awaited()


def test_voice_channel_uses_existing_room_targets() -> None:
    hass = _FakeHass()
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "voice_auto": {
                    "type": "tts",
                    "service": "tts.yandex_station_say",
                    "entity_id": "group.voice_notification_targets",
                    "data": {
                        "room_targets": {
                            "living_room": "media_player.yandex_station_x11jdn200bwyse",
                            "bedroom": "media_player.yandex_station_lp000000000000472311000094e3cf79",
                        }
                    },
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["voice_auto"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="bedroom")),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="system_events",
        title="Voice",
        message="Room-routed speech",
        level="info",
        source="legacy.voice_notify_router",
        timestamp="2026-03-08T11:00:00+00:00",
        room="Гостиная",
        metadata={"legacy_target_group": "group.voice_notification_targets"},
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["voice_auto"],
            title="Voice",
            message="Room-routed speech",
            language="ru",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(primary_room="bedroom"),
            delivery_room="living_room",
        )
    )

    _, _, data = hass.services.async_call.await_args.args
    assert data["entity_id"] == "group.voice_notification_targets"
    assert result["service"] == "tts.yandex_station_say"
    assert result["target_entity_id"] == "group.voice_notification_targets"
    assert result["requested_room"] == "living_room"

    context.metadata["legacy_target_group"] = ""
    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["voice_auto"],
            title="Voice",
            message="Room-routed speech",
            language="ru",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(primary_room="bedroom"),
            delivery_room="living_room",
        )
    )

    _, _, data = hass.services.async_call.await_args.args
    assert data["entity_id"] == "media_player.yandex_station_x11jdn200bwyse"
    assert result["target_entity_id"] == "media_player.yandex_station_x11jdn200bwyse"


def test_voice_channel_prefers_selected_room_audio_target_when_available() -> None:
    hass = _FakeHass(
        {
            "media_player.alisa_living_room": _FakeState("idle", {"friendly_name": "Living Room Alice"}),
            "media_player.homepod_living_room": _FakeState("playing", {"friendly_name": "Living Room HomePod"}),
        }
    )
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "voice_auto": {
                    "type": "tts",
                    "service": "tts.yandex_station_say",
                    "entity_id": "media_player.alisa_living_room",
                    "data": {
                        "audio_targets": {
                            "living_room": [
                                {
                                    "kind": "alisa",
                                    "entity_id": "media_player.alisa_living_room",
                                    "service": "tts.yandex_station_say",
                                    "priority": 1,
                                },
                                {
                                    "kind": "homepod",
                                    "entity_id": "media_player.homepod_living_room",
                                    "service": "tts.speak",
                                    "engine_entity_id": "tts.google_translate_en_com",
                                    "priority": 2,
                                },
                            ]
                        }
                    },
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["voice_auto"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room")),
        _FakeControls(room_audio_targets={"living_room": "homepod"}),
    )
    context = NotificationContext(
        flow="system_events",
        title="Voice",
        message="Selected target",
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        room="living_room",
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["voice_auto"],
            title="Voice",
            message="Selected target",
            language="en",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(primary_room="living_room"),
            delivery_room="living_room",
        )
    )

    _, _, data = hass.services.async_call.await_args.args
    assert result["service"] == "tts.speak"
    assert result["target_entity_id"] == "media_player.homepod_living_room"
    assert result["tts_entity_id"] == "tts.google_translate_en_com"
    assert result["target_kind"] == "homepod"
    assert data["entity_id"] == "tts.google_translate_en_com"
    assert data["media_player_entity_id"] == "media_player.homepod_living_room"


def test_voice_channel_falls_back_to_next_available_room_audio_target() -> None:
    hass = _FakeHass(
        {
            "media_player.alisa_living_room": _FakeState("unavailable", {"friendly_name": "Living Room Alice"}),
            "media_player.homepod_living_room": _FakeState("off", {"friendly_name": "Living Room HomePod"}),
            "media_player.tv_living_room": _FakeState("playing", {"friendly_name": "Living Room TV"}),
        }
    )
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "voice_auto": {
                    "type": "tts",
                    "service": "tts.yandex_station_say",
                    "entity_id": "media_player.alisa_living_room",
                    "data": {
                        "audio_targets": {
                            "living_room": [
                                {
                                    "kind": "alisa",
                                    "entity_id": "media_player.alisa_living_room",
                                    "service": "tts.yandex_station_say",
                                    "priority": 1,
                                },
                                {
                                    "kind": "homepod",
                                    "entity_id": "media_player.homepod_living_room",
                                    "service": "tts.speak",
                                    "engine_entity_id": "tts.google_translate_en_com",
                                    "priority": 2,
                                },
                                {
                                    "kind": "tv",
                                    "entity_id": "media_player.tv_living_room",
                                    "service": "tts.speak",
                                    "engine_entity_id": "tts.google_translate_en_com",
                                    "active_only": True,
                                    "priority": 3,
                                },
                            ]
                        }
                    },
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["voice_auto"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room")),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="system_events",
        title="Voice",
        message="Fallback target",
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        room="living_room",
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["voice_auto"],
            title="Voice",
            message="Fallback target",
            language="en",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(primary_room="living_room"),
            delivery_room="living_room",
        )
    )

    _, _, data = hass.services.async_call.await_args.args
    assert result["service"] == "tts.speak"
    assert result["target_entity_id"] == "media_player.tv_living_room"
    assert result["target_kind"] == "tv"
    assert data["media_player_entity_id"] == "media_player.tv_living_room"


def test_telegram_channel_reports_existing_delivery_settings() -> None:
    hass = _FakeHass()
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "telegram_default": {
                    "type": "telegram",
                    "service": "telegram_bot.send_message",
                    "chat_id": -1002601312925,
                    "thread_id": 48,
                    "data": {
                        "config_entry_id": "01KJXJAQECTCZBJJE3ZR9T2VAG",
                    },
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["telegram_default"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room", nobody_home=True)),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="system_events",
        title="Telegram",
        message="Existing telegram settings",
        level="warning",
        source="legacy.system_notify",
        timestamp="2026-03-08T11:00:00+00:00",
        notification_id="notif_123",
        include_actions=True,
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["telegram_default"],
            title="Telegram",
            message="Existing telegram settings",
            language="ru",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(primary_room="living_room", nobody_home=True),
            delivery_room="living_room",
        )
    )

    _, _, data = hass.services.async_call.await_args.args
    assert data["chat_id"] == [-1002601312925]
    assert data["message_thread_id"] == 48
    assert result["service"] == "telegram_bot.send_message"
    assert result["chat_id"] == -1002601312925
    assert result["thread_id"] == 48
    assert result["config_entry_id"] == "01KJXJAQECTCZBJJE3ZR9T2VAG"


def test_dashboard_channel_records_feed_entry() -> None:
    hass = _FakeHass()
    recorded: list[dict[str, object]] = []

    def _record_dashboard_delivery(**payload):
        recorded.append(payload)
        return {"feed_entry_id": "feed_123"}

    config = HeraldConfig.from_raw(
        {
            "channels": {
                "dashboard_default": {
                    "type": "dashboard",
                }
            },
            "flows": {
                "system_events": {
                    "channels": ["dashboard_default"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room")),
        _FakeControls(),
        _record_dashboard_delivery,
    )
    context = NotificationContext(
        flow="system_events",
        title="Dashboard",
        message="Rendered in feed",
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        event="dashboard_smoke",
        notification_id="notif_dashboard_1",
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["dashboard_default"],
            title="Dashboard",
            message="Rendered in feed",
            language="ru",
            context=context,
            flow=config.flows["system_events"],
            presence=PresenceSnapshot(primary_room="living_room"),
            delivery_room="living_room",
        )
    )

    assert result["status"] == "sent"
    assert result["service"] == "dashboard.feed"
    assert result["feed_entry_id"] == "feed_123"


def test_tv_channel_uses_existing_tts_speak_stack() -> None:
    hass = _FakeHass(
        {
            "media_player.tv": _FakeState("playing", {"friendly_name": "TV"}),
        }
    )
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "tv_auto": {
                    "type": "tv",
                    "service": "tts.speak",
                    "entity_id": "media_player.tv",
                    "data": {
                        "engine_entity_id": "tts.google_translate_en_com",
                        "active_only": True,
                        "announce": True,
                    },
                }
            },
            "flows": {
                "camera_alerts": {
                    "channels": ["tv_auto"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room")),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="camera_alerts",
        title="Camera",
        message="Movement detected",
        level="warning",
        source="automation.camera",
        timestamp="2026-03-08T11:00:00+00:00",
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["tv_auto"],
            title="Camera",
            message="Movement detected",
            language="en",
            context=context,
            flow=config.flows["camera_alerts"],
            presence=PresenceSnapshot(primary_room="living_room"),
            delivery_room="living_room",
        )
    )

    _, _, data = hass.services.async_call.await_args.args
    assert result["status"] == "sent"
    assert result["service"] == "tts.speak"
    assert result["target_entity_id"] == "media_player.tv"
    assert result["tts_entity_id"] == "tts.google_translate_en_com"
    assert data["entity_id"] == "tts.google_translate_en_com"
    assert data["media_player_entity_id"] == "media_player.tv"
    assert data["message"] == "Camera. Movement detected"


def test_tv_channel_drops_when_player_is_inactive() -> None:
    hass = _FakeHass(
        {
            "media_player.tv": _FakeState("off", {"friendly_name": "TV"}),
        }
    )
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "tv_auto": {
                    "type": "tv",
                    "service": "tts.speak",
                    "entity_id": "media_player.tv",
                    "data": {
                        "engine_entity_id": "tts.google_translate_en_com",
                        "active_only": True,
                    },
                }
            },
            "flows": {
                "camera_alerts": {
                    "channels": ["tv_auto"],
                }
            },
        }
    )
    router = HeraldRouter(
        hass,
        config,
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room")),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="camera_alerts",
        title="Camera",
        message="Movement detected",
        level="warning",
        source="automation.camera",
        timestamp="2026-03-08T11:00:00+00:00",
    )

    result = asyncio.run(
        router._async_send_channel(
            channel=config.channels["tv_auto"],
            title="Camera",
            message="Movement detected",
            language="en",
            context=context,
            flow=config.flows["camera_alerts"],
            presence=PresenceSnapshot(primary_room="living_room"),
            delivery_room="living_room",
        )
    )

    assert result["status"] == "dropped"
    assert result["reason"] == "tv_inactive"
    hass.services.async_call.assert_not_awaited()


def test_router_prefers_user_room_from_context_profiles() -> None:
    router = HeraldRouter(
        _FakeHass(),
        HeraldConfig.from_raw(None),
        AsyncMock(),
        _FakePresence(PresenceSnapshot(primary_room="living_room")),
        _FakeControls(),
    )
    context = NotificationContext(
        flow="system_events",
        title="Presence",
        message="Per-user room",
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        user="person.aleksandr_meshcheriakov",
        users=["person.aleksandr_meshcheriakov"],
        context_data={
            "users": [
                {
                    "person_entity_id": "person.aleksandr_meshcheriakov",
                    "slug": "aleksandr_meshcheriakov",
                    "current_room": "bedroom",
                }
            ]
        },
    )

    resolved_room = router._resolve_delivery_room(
        "aleksandr_meshcheriakov",
        context,
        PresenceSnapshot(primary_room="living_room"),
    )

    assert resolved_room == "bedroom"
