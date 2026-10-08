"""Configuration reports use only local, safe data and never perform delivery."""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from custom_components.herald.configuration_check import MAX_CHANNELS, MAX_CHECKS, build_configuration_report
from custom_components.herald.models import ChannelConfig, HeraldConfig, PresenceSnapshot


class _Controls:
    def __init__(self, values=None):
        self.values = values or {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def is_mute_all_enabled(self):
        return self.value("mute_all", False)

    def maintenance_mode_enabled(self):
        return self.value("maintenance_mode", False)

    def is_level_enabled(self, level):
        return self.value(f"level_enabled:{level}", True)

    def effective_settings(self):
        raise AssertionError("Report must not inspect configuration layers or mutate the controls cache")


class _PrivateData(dict):
    """A provider payload whose credentials and arbitrary contents cannot be accessed."""

    def get(self, key, default=None):
        assert key in {"room_targets", "audio_targets", "notify_services", "media_player", "engine_entity_id", "active_only"}
        return super().get(key, default)

    def __iter__(self):
        raise AssertionError("No iteration of provider data")

    def items(self):
        raise AssertionError("No iteration of provider data")

    def keys(self):
        raise AssertionError("No copying of provider data")

    def __deepcopy__(self, memo):
        raise AssertionError("No copying of provider data")


def _build(channels, *, services=(), states=None, values=None, settings=None, presence=None, **kwargs):
    observed = {"services": [], "states": []}
    states = states or {}

    def service_exists(domain, service):
        observed["services"].append(f"{domain}.{service}")
        return f"{domain}.{service}" in services

    def get_state(entity_id):
        observed["states"].append(entity_id)
        return SimpleNamespace(state=states[entity_id]) if entity_id in states else None

    def forbidden(*args, **kwargs):
        raise AssertionError("No state mutation, delivery, discovery or external calls")

    hass = SimpleNamespace(states=SimpleNamespace(get=get_state, async_set=forbidden),
                           services=SimpleNamespace(has_service=service_exists, async_call=forbidden),
                           async_add_executor_job=forbidden)
    config = HeraldConfig(channels={channel.name: channel for channel in channels})
    config.router.update(kwargs.pop("router", {}))
    controls = _Controls(values)
    before = deepcopy(controls.values)
    report = build_configuration_report(hass, config, controls, presence or PresenceSnapshot(),
                                        control_entities=kwargs.pop("control_entities", {}), checked_at="2026-09-30T17:00:00Z",
                                        effective_settings=settings, **kwargs)
    assert controls.values == before
    return report, observed


def _codes(report):
    return {check["code"] for check in report["channels"][0]["checks"]}


def test_local_service_and_provenance_with_exact_parent_supplied_controls():
    settings = {"channel_enabled:phone": {"value": True, "source": "runtime", "inherited": False, "inherited_source": "yaml"},
                "channel_min_level:phone": {"value": "warning", "source": "options", "inherited": "info", "inherited_source": "entry"}}
    before = deepcopy(settings)
    report, _ = _build([ChannelConfig("phone", "mobile_app", service="notify.phone", user="alice")], services={"notify.phone"},
                       values={"channel_min_level:phone": "warning"}, settings=settings,
                       control_entities={"channel_enabled:phone": "switch.actual_phone", "channel_min_level:phone": "select.actual_phone_level"})
    channel = report["channels"][0]
    assert channel["status"] == "configured"
    assert channel["settings"]["enabled"] == settings["channel_enabled:phone"]
    assert channel["settings"]["min_level"] == settings["channel_min_level:phone"]
    assert channel["controls"] == {"enabled": "switch.actual_phone", "min_level": "select.actual_phone_level"}
    assert report["summary"] == {"total": 1, "enabled": 1, "attention": 0, "not_checked": 0}
    assert settings == before
    channel["settings"]["enabled"]["source"] = "changed"
    assert settings == before
    assert not report["truncated"] and report["schema_version"] == 1
    assert "Доставка уведомлений не выполнялась" in " ".join(report["limitations"])


def test_stale_provenance_does_not_attribute_runtime_change_to_old_source():
    report, _ = _build([ChannelConfig("log", "system_log")], services={"system_log.write"},
                       values={"channel_enabled:log": False}, settings={"channel_enabled:log": {"value": True, "source": "yaml"}})
    channel = report["channels"][0]
    assert channel["enabled"] is False
    assert channel["settings"]["enabled"] == {"value": False, "source": "unknown", "inherited": None, "inherited_source": "unknown"}
    assert channel["status"] == "configured"  # Disabled is not a configuration failure.
    assert "channel_disabled" in _codes(report)
    assert channel["controls"] == {"enabled": None, "min_level": None}


@pytest.mark.parametrize(("service", "code"), [(None, "service_missing"), ("invalid", "service_invalid"), ("notify.absent", "service_missing")])
def test_missing_or_malformed_service_never_looks_ready(service, code):
    report, _ = _build([ChannelConfig("phone", "mobile_app", service=service, user="alice")])
    assert report["channels"][0]["status"] == "attention"
    assert code in _codes(report)


@pytest.mark.parametrize(("state", "expected"), [(None, "target_missing"), ("unknown", "target_unavailable"),
                                                ("unavailable", "target_unavailable"), ("off", "target_inactive"),
                                                ("idle", "target_inactive"), ("playing", "target_available")])
def test_tv_state_and_active_only_are_reported_without_device_actions(state, expected):
    report, _ = _build([ChannelConfig("screen", "tv", entity_id="media_player.screen", service="notify.screen")],
                       services={"notify.screen"}, states={} if state is None else {"media_player.screen": state})
    assert expected in _codes(report)
    assert report["channels"][0]["status"] == ("configured" if state == "playing" else "attention")


def test_tts_speak_checks_engine_without_attempting_speech():
    channel = ChannelConfig("voice", "tts", entity_id="media_player.speaker", service="tts.speak")
    report, _ = _build([channel], services={"tts.speak"}, states={"media_player.speaker": "idle"})
    assert "tts_engine_missing" in _codes(report)
    channel.data["engine_entity_id"] = "tts.engine"
    report, _ = _build([channel], services={"tts.speak"}, states={"media_player.speaker": "idle", "tts.engine": "ready"})
    assert report["channels"][0]["status"] == "configured"


def test_room_audio_targets_use_their_service_and_engine_overrides():
    channel = ChannelConfig("voice", "tts", data={"audio_targets": {"Кухня": [
        {"entity_id": "media_player.speaker", "service": "tts.speak", "engine_entity_id": "tts.engine"},
    ]}})
    report, observed = _build([channel], services={"tts.speak"}, states={"media_player.speaker": "idle", "tts.engine": "ready"})
    assert report["channels"][0]["rooms"] == ["kitchen"]
    assert report["channels"][0]["status"] == "configured"
    assert observed["services"] == ["tts.speak"]


def test_ambiguous_room_aliases_and_malformed_target_shapes_are_explained():
    channel = ChannelConfig("voice", "tts", service="tts.speak", data={
        "room_targets": {"Кухня": "media_player.one", "kitchen": "media_player.two"}, "audio_targets": ["wrong"],
    })
    report, _ = _build([channel], services={"tts.speak"})
    assert {"room_mapping_ambiguous", "target_mapping_invalid", "tts_engine_missing"} <= _codes(report)
    assert report["channels"][0]["status"] == "attention"


def test_tv_cannot_use_audio_map_in_place_of_required_media_player():
    channel = ChannelConfig("screen", "tv", service="notify.screen", data={"audio_targets": {"kitchen": [
        {"entity_id": "media_player.speaker", "service": "tts.speak", "engine_entity_id": "tts.engine"},
    ]}})
    report, _ = _build([channel], services={"notify.screen", "tts.speak"}, states={"media_player.speaker": "idle", "tts.engine": "ready"})
    assert "target_missing" in _codes(report)


@pytest.mark.parametrize("kind", ["tts_hume", "telegram"])
def test_provider_secrets_and_recipient_ids_are_never_read_or_exported(kind):
    channel = ChannelConfig("provider", kind, entity_id="media_player.speaker", chat_id="private-chat", thread_id="private-thread",
                            data=_PrivateData(api_key="private-key", token="private-token", authorization="private-header"))
    report, _ = _build([channel], services={"media_player.play_media", "telegram_bot.send_message"}, states={"media_player.speaker": "idle"})
    assert report["channels"][0]["status"] == "not_checked"
    assert "private-" not in json.dumps(report)


def test_hume_room_mapping_does_not_replace_its_required_direct_target():
    channel = ChannelConfig("hume", "tts_hume", data=_PrivateData(room_targets={"kitchen": "media_player.speaker"}))
    report, _ = _build([channel], services={"media_player.play_media"}, states={"media_player.speaker": "idle"})
    assert "target_missing" in _codes(report)
    assert report["channels"][0]["status"] == "attention"


def test_active_restrictions_include_actual_controls_but_no_user_catalog():
    report, _ = _build([], values={"mute_all": True, "maintenance_mode": True, "channel_family:voice": False,
                                  "level_enabled:info": False, "user_silent:alice": True},
                       presence=PresenceSnapshot(quiet_hours=True, nobody_home=True),
                       control_entities={"mute_all": "switch.actual_mute", "channel_family:voice": "switch.actual_voice"})
    by_code = {item["code"]: item for item in report["restrictions"]}
    assert set(by_code) == {"mute_all", "maintenance", "quiet_hours", "away", "family_disabled:voice", "level_disabled:info"}
    assert by_code["mute_all"]["entity_id"] == "switch.actual_mute"
    assert "критические" in by_code["mute_all"]["detail"]
    assert "alice" not in json.dumps(report)


def test_explicit_maintenance_result_has_priority_over_control_value():
    report, _ = _build([], values={"maintenance_mode": True}, maintenance_active=False)
    assert not report["restrictions"]
    report, _ = _build([], maintenance_active=True)
    assert report["restrictions"][0]["code"] == "maintenance"


def test_external_maintenance_is_reported_without_linking_an_inactive_owned_switch():
    report, _ = _build([], router={"maintenance_mode_entity": "input_boolean.external"},
                       states={"input_boolean.external": "on"},
                       control_entities={"maintenance_mode": "switch.owned_maintenance"})
    restriction = report["restrictions"][0]
    assert restriction["code"] == "maintenance"
    assert "entity_id" not in restriction


def test_unknown_type_is_not_reported_as_an_unverified_custom_service():
    report, observed = _build([ChannelConfig("other", "typo", service="notify.ignored")], services={"system_log.write"})
    assert "channel_type_unknown" in _codes(report)
    assert observed["services"] == ["system_log.write"]
    assert report["channels"][0]["status"] == "attention"


def test_channel_limit_keeps_total_counts_and_marks_omitted_channels_unchecked():
    channels = [ChannelConfig(f"log_{i:03}", "system_log", enabled=i % 2 == 0) for i in range(MAX_CHANNELS + 5)]
    report, _ = _build(channels, services={"system_log.write"})
    assert len(report["channels"]) == MAX_CHANNELS
    assert report["summary"] == {"total": MAX_CHANNELS + 5, "enabled": 53, "attention": 0, "not_checked": 5}
    assert report["truncated"]


def test_large_target_lists_bound_registry_reads_and_explain_incomplete_check():
    targets = [f"media_player.target_{i}" for i in range(100)]
    report, observed = _build([ChannelConfig("voice", "tts", entity_id=targets, service="tts.speak")],
                              services={"tts.speak"}, states=dict.fromkeys(targets, "idle"))
    assert len(report["channels"][0]["checks"]) <= MAX_CHECKS
    assert len(observed["states"]) <= MAX_CHECKS
    # tts.speak rejects multi-target lists outright; generic TTS bounds enumeration.
    report, observed = _build([ChannelConfig("voice", "tts", entity_id=targets)],
                              services={"tts.yandex_station_say"}, states=dict.fromkeys(targets, "idle"))
    assert report["truncated"] and "checks_truncated" in _codes(report)
    assert len(report["channels"][0]["checks"]) <= MAX_CHECKS
    assert len(observed["states"]) <= MAX_CHECKS


def test_wrong_entity_domain_for_tts_engine_is_a_local_error():
    report, _ = _build([ChannelConfig("voice", "tts", entity_id="media_player.speaker", service="tts.speak", data={"engine_entity_id": "sensor.fake"})],
                       services={"tts.speak"}, states={"media_player.speaker": "idle", "sensor.fake": "ready"})
    assert "tts_engine_invalid" in _codes(report)


@pytest.mark.parametrize("kind", ["tts", "tts_hume", "tv"])
def test_media_transports_cannot_report_sensor_entity_as_valid_target(kind):
    channel = ChannelConfig("voice", kind, entity_id="sensor.fake", service="tts.speak", data={"engine_entity_id": "tts.engine"})
    report, _ = _build([channel], services={"tts.speak", "media_player.play_media"}, states={"sensor.fake": "ready", "tts.engine": "ready"})
    assert "target_domain_invalid" in _codes(report)
    assert report["channels"][0]["status"] == "attention"


def test_single_item_list_is_not_accepted_as_tts_speak_room_target():
    channel = ChannelConfig("voice", "tts", service="tts.speak", data={"room_targets": {"kitchen": ["media_player.speaker"]}, "engine_entity_id": "tts.engine"})
    report, _ = _build([channel], services={"tts.speak"}, states={"media_player.speaker": "idle", "tts.engine": "ready"})
    assert "target_invalid" in _codes(report)


def test_hume_ignored_room_map_is_not_checked_as_a_real_target():
    channel = ChannelConfig("hume", "tts_hume", entity_id="media_player.speaker", data=_PrivateData(room_targets={"kitchen": "media_player.ignored"}))
    report, observed = _build([channel], services={"media_player.play_media"}, states={"media_player.speaker": "idle"})
    assert "media_player.ignored" not in observed["states"]
    assert "target_mapping_ignored" in _codes(report)
    assert report["channels"][0]["rooms"] == []
