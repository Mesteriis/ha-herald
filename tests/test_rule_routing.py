"""Rule scopes remain hard boundaries in previews and real mocked delivery."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from test_routing_regressions import context, router_for

from custom_components.herald.decisions import explain_outcome, explain_route
from custom_components.herald.policy_rules import apply_rule
from custom_components.herald.router import HeraldRouter


def rule_context(policy, **kwargs):
    return context(metadata={"notification_policy": policy, "channels_explicit": True}, **kwargs)


def install_checker(router):
    router._rule_checker = lambda ctx, presence: apply_rule(
        ctx, ctx.metadata["notification_policy"], presence,
        known_users=["person.alice", "person.bob"], known_rooms=["kitchen", "bedroom", "living_room"],
    )


def apply_for_preview(router, ctx, presence):
    if router._rule_checker:
        assert router._rule_checker(ctx, presence) is None
    return router.build_route_preview(ctx, router._config.flows[ctx.flow], presence)


@pytest.mark.asyncio
@pytest.mark.parametrize("bypass", [False, True])
async def test_quiet_text_only_removes_all_local_types_without_adding_channels(bypass):
    router, flow, presence = router_for({
        "voice": {"type": "tts", "entity_id": "media_player.kitchen"},
        "hume": {"type": "tts_hume", "entity_id": "media_player.kitchen"},
        "tv": {"type": "tv", "entity_id": "media_player.kitchen_tv"},
        "selected": {"type": "persistent_notification"},
        "unselected": {"type": "persistent_notification"},
    }, people_home=["person.alice"])
    presence.quiet_hours = True
    install_checker(router)
    ctx = rule_context({"quiet_hours": "text_only"}, channels=["voice", "hume", "tv", "selected"], force=True, level="critical")
    ctx.metadata["bypass_channel_policy"] = bypass
    router._hume_tts.async_deliver = AsyncMock()

    preview = apply_for_preview(router, ctx, presence)
    results = await router.async_route(ctx, flow)

    assert preview["resolved"]["final_channels"] == ["selected"]
    assert {item["reason"] for item in preview["channel_decisions"] if not item["selected"]} == {"policy_text_only"}
    assert [(item["channel"], item["status"]) for item in results] == [("selected", "sent")]
    router._hume_tts.async_deliver.assert_not_awaited()
    assert router._hass.services.async_call.await_args.args[:2] == ("persistent_notification", "create")


@pytest.mark.asyncio
async def test_rule_explicit_empty_channels_stays_empty_with_text_only():
    router, flow, presence = router_for({"unselected": {"type": "persistent_notification"}})
    presence.quiet_hours = True
    install_checker(router)
    ctx = rule_context({"quiet_hours": "text_only", "delivery_mode": "custom", "channels": []}, channels=[])
    preview = apply_for_preview(router, ctx, presence)
    assert explain_route(preview)["status"] == "no_targets"
    assert await router.async_route(ctx, flow) == []
    router._ai_client.async_rewrite_payload.assert_not_awaited()
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("bypass", [False, True])
async def test_selected_room_overrides_legacy_device_and_group(bypass):
    router, flow, presence = router_for({"auto_voice": {
        "type": "tts", "entity_id": "media_player.bedroom",
        "data": {"room_targets": {"kitchen": "media_player.kitchen", "bedroom": "media_player.bedroom"}},
    }}, people_home=["person.alice"])
    install_checker(router)
    ctx = rule_context({"target_room": "kitchen"}, channels=["auto_voice"], room="bedroom", device="media_player.bedroom")
    ctx.metadata.update({"legacy_target_group": "group.all_speakers", "bypass_channel_policy": bypass})
    preview = apply_for_preview(router, ctx, presence)
    results = await router.async_route(ctx, flow)
    assert preview["deliveries"][0]["target_entity_id"] == "media_player.kitchen"
    assert results[0]["target_entity_id"] == "media_player.kitchen"
    assert router._hass.services.async_call.await_args.args[2]["entity_id"] == "media_player.kitchen"


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["tts", "tts_hume", "tv"])
async def test_room_without_local_target_never_uses_other_room_default(kind):
    router, flow, presence = router_for({"wrong": {
        "type": kind, "room": "bedroom", "entity_id": "media_player.bedroom", "service": "notify.bedroom",
    }}, people_home=["person.alice"])
    install_checker(router)
    ctx = rule_context({"target_room": "kitchen"}, channels=["wrong"], device="media_player.bedroom")
    ctx.metadata["bypass_channel_policy"] = True
    preview = apply_for_preview(router, ctx, presence)
    assert preview["deliveries"] == []
    assert preview["channel_decisions"][0]["reason"] == "policy_target_room"
    assert await router.async_route(ctx, flow) == []
    router._hass.services.async_call.assert_not_awaited()
    router._ai_client.async_rewrite_payload.assert_not_awaited()


@pytest.mark.asyncio
async def test_room_audio_fallback_remains_in_selected_room():
    targets = {
        "kitchen": [{"kind": "alisa", "entity_id": "media_player.kitchen_a", "service": "tts.say"},
                    {"kind": "homepod", "entity_id": "media_player.kitchen_b", "service": "tts.say"}],
        "bedroom": [{"kind": "alisa", "entity_id": "media_player.bedroom", "service": "tts.say"}],
    }
    router, flow, presence = router_for({"voice": {
        "type": "tts", "entity_id": "media_player.bedroom", "data": {"audio_targets": targets},
    }}, people_home=["person.alice"], states={item["entity_id"]: SimpleNamespace(state="idle") for group in targets.values() for item in group})
    install_checker(router)
    ctx = rule_context({"target_room": "kitchen"}, channels=["voice"], device="media_player.bedroom")
    preview = apply_for_preview(router, ctx, presence)
    router._hass.services.async_call.side_effect = [ValueError("Rejected"), None]
    results = await router.async_route(ctx, flow)
    assert preview["deliveries"][0]["target_entity_id"] == "media_player.kitchen_a"
    assert results[0]["target_entity_id"] == "media_player.kitchen_b"
    assert [call.args[2]["entity_id"] for call in router._hass.services.async_call.await_args_list] == ["media_player.kitchen_a", "media_player.kitchen_b"]


@pytest.mark.asyncio
async def test_unavailable_selected_audio_never_falls_back_to_other_room():
    router, flow, presence = router_for({"voice": {
        "type": "tts", "entity_id": "media_player.bedroom",
        "data": {"audio_targets": {"kitchen": [{"entity_id": "media_player.kitchen"}]}, "room_targets": {"bedroom": "media_player.bedroom"}},
    }}, people_home=["person.alice"], states={"media_player.bedroom": SimpleNamespace(state="idle")})
    install_checker(router)
    ctx = rule_context({"target_room": "kitchen"}, channels=["voice"], device="media_player.bedroom")
    preview = apply_for_preview(router, ctx, presence)
    assert preview["deliveries"][0]["reason"] == "room_audio_unavailable"
    results = await router.async_route(ctx, flow)
    assert results[0]["reason"] == "room_audio_unavailable"
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("notify_mapping", [False, True])
async def test_tv_rule_requires_room_specific_notify_mapping(notify_mapping):
    data = {"room_targets": {"kitchen": "media_player.kitchen_tv", "bedroom": "media_player.bedroom_tv"}}
    if notify_mapping:
        data["notify_services"] = {"kitchen": "notify.kitchen", "bedroom": "notify.bedroom"}
    router, flow, presence = router_for({"tv": {
        "type": "tv", "service": "notify.bedroom", "entity_id": "media_player.bedroom_tv", "data": data,
    }}, people_home=["person.alice"], states={"media_player.kitchen_tv": SimpleNamespace(state="playing")})
    install_checker(router)
    ctx = rule_context({"target_room": "kitchen"}, channels=["tv"], device="notify.bedroom")
    preview = apply_for_preview(router, ctx, presence)
    results = await router.async_route(ctx, flow)
    if notify_mapping:
        assert preview["deliveries"][0]["service"] == "notify.kitchen"
        assert results[0]["service"] == "notify.kitchen"
        assert router._hass.services.async_call.await_args.args[:2] == ("notify", "kitchen")
    else:
        assert preview["deliveries"] == results == []
        router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_selected_audience_excludes_ownerless_personal_channels_and_unselected_users():
    router, flow, presence = router_for({
        "alice": {"type": "mobile_app", "user": "alice", "service": "notify.alice"},
        "bob": {"type": "telegram", "user": "bob", "chat_id": 2},
        "ownerless_mobile": {"type": "mobile_app", "service": "notify.shared_phone"},
        "ownerless_telegram": {"type": "telegram", "chat_id": 3},
        "shared": {"type": "persistent_notification"},
    })
    install_checker(router)
    ctx = rule_context({"users": ["person.alice"]}, channels=list(router._config.channels), users=["person.alice", "person.bob"])
    ctx.metadata["bypass_channel_policy"] = True
    preview = apply_for_preview(router, ctx, presence)
    results = await router.async_route(ctx, flow)
    assert preview["resolved"]["final_channels"] == ["alice", "shared"]
    assert {item["channel"] for item in results} == {"alice", "shared"}
    assert [call.args[:2] for call in router._hass.services.async_call.await_args_list] == [("notify", "alice"), ("persistent_notification", "create")]


@pytest.mark.asyncio
@pytest.mark.parametrize("people_home,silent", [([], False), (["person.alice"], True), (["person.bob"], False)])
async def test_rule_scope_cannot_bypass_local_absence_or_silent_audience(people_home, silent):
    router, flow, presence = router_for({"voice": {"type": "tts", "room": "kitchen", "entity_id": "media_player.kitchen"}}, people_home=people_home)
    install_checker(router)
    ctx = rule_context({"users": ["person.alice"], "target_room": "kitchen"}, channels=["voice"], users=["person.alice"],
                       context_data={"users": [{"slug": "alice", "silent": silent}]})
    ctx.metadata["bypass_channel_policy"] = True
    assert apply_for_preview(router, ctx, presence)["deliveries"] == []
    assert await router.async_route(ctx, flow) == []
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_rule_blocks_before_ai():
    router, flow, _ = router_for({"shared": {"type": "persistent_notification"}})
    install_checker(router)
    ctx = rule_context({"presence": "someone_home"}, channels=["shared"])
    results = await router.async_route(ctx, flow)
    assert results == [{"status": "dropped", "reason": "policy_someone_home", "flow": flow.name}]
    assert ctx.metadata["routing_explanation"]["reason"] == "policy_someone_home"
    router._ai_client.async_rewrite_payload.assert_not_awaited()
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("transition", ["quiet_text", "quiet_mute", "away"])
async def test_presence_transition_during_ai_is_rechecked_before_transport(transition):
    router, flow, presence = router_for({
        "voice": {"type": "tts", "room": "kitchen", "entity_id": "media_player.kitchen"},
        "shared": {"type": "persistent_notification"},
    }, people_home=["person.alice"])
    policy = {"quiet_hours": "text_only" if transition == "quiet_text" else "mute"} if transition != "away" else {"presence": "someone_home"}
    install_checker(router)
    ctx = rule_context(policy, channels=["voice", "shared"], room="kitchen", rewrite=True, force=True, level="critical")
    ctx.metadata["bypass_channel_policy"] = True

    async def rewrite(**kwargs):
        if transition == "away":
            router._presence.async_resolve.return_value = replace(presence, nobody_home=True, people_home=[])
        else:
            router._presence.async_resolve.return_value = replace(presence, quiet_hours=True)
        return {"title": kwargs["title"], "message": kwargs["message"]}

    router._ai_client.async_rewrite_payload.side_effect = rewrite
    results = await router.async_route(ctx, flow)
    assert results[0]["channel"] == "voice"
    assert results[0]["status"] == "dropped"
    expected_reason = {"quiet_text": "policy_text_only", "quiet_mute": "policy_quiet_hours", "away": "policy_someone_home"}[transition]
    assert results[0]["reason"] == expected_reason
    if transition == "quiet_text":
        assert results[1]["channel"] == "shared" and results[1]["status"] == "sent"
        assert router._hass.services.async_call.await_args.args[:2] == ("persistent_notification", "create")
    else:
        assert all(item["status"] == "dropped" for item in results)
        router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_earlier_delivery_then_presence_transition_reports_partial_outcome():
    router, flow, presence = router_for({
        "first": {"type": "persistent_notification"},
        "second": {"type": "persistent_notification"},
    }, people_home=["person.alice"])
    install_checker(router)
    ctx = rule_context({"presence": "someone_home"}, channels=["first", "second"])
    ctx.metadata["bypass_channel_policy"] = True

    async def deliver(*args, **kwargs):
        router._presence.async_resolve.return_value = replace(presence, nobody_home=True, people_home=[])

    router._hass.services.async_call.side_effect = deliver
    results = await router.async_route(ctx, flow)
    assert [item["status"] for item in results] == ["sent", "dropped"]
    assert results[1]["reason"] == "policy_someone_home"
    assert explain_outcome("sent", results=results)["status"] == "partial"
    assert router._hass.services.async_call.await_count == 1


@pytest.mark.asyncio
async def test_default_rule_keeps_legacy_single_presence_resolution_and_device_override():
    router, flow, _ = router_for({"voice": {
        "type": "tts", "entity_id": "media_player.bedroom",
        "data": {"room_targets": {"kitchen": "media_player.kitchen", "bedroom": "media_player.bedroom"}},
    }}, people_home=["person.alice"])
    checker = SimpleNamespace(calls=0)

    def unused_check(ctx, snapshot):
        checker.calls += 1
        return "policy_someone_home"

    router = HeraldRouter(router._hass, router._config, router._ai_client, router._presence, router._controls, rule_checker=unused_check)
    ctx = rule_context({"users": None, "target_room": None, "presence": "any", "quiet_hours": "inherit"}, channels=["voice"], room="kitchen", device="media_player.bedroom")
    results = await router.async_route(ctx, flow)
    assert results[0]["target_entity_id"] == "media_player.bedroom"
    assert checker.calls == 0
    assert router._presence.async_resolve.await_count == 1


@pytest.mark.parametrize("reason", [
    "policy_someone_home", "policy_nobody_home", "policy_quiet_hours", "notification_policy_no_recipients",
    "policy_target_room", "policy_text_only", "policy_unknown_user", "policy_unknown_room", "policy_route_changed",
])
def test_rule_reasons_explain_preview_and_actual_drops(reason):
    preview = {"prechecks": {"blocked_reason": reason}, "policy": {"users": ["person.alice"], "target_room": "kitchen", "presence": "someone_home", "quiet_hours": "text_only"}}
    original = deepcopy(preview)
    planned = explain_route(preview)
    outcome = explain_outcome("dropped", reason=reason)
    assert planned["reason"] == outcome["reason"] == reason
    assert planned["status"] == "blocked"
    assert "причина не уточнена" not in str(planned) + str(outcome)
    assert "Общие каналы" in str(planned["warnings"])
    assert preview == original


@pytest.mark.asyncio
async def test_personal_local_channel_requires_selected_person_to_be_home():
    router, flow, presence = router_for({"voice": {
        "type": "tts", "user": "alice", "room": "kitchen", "entity_id": "media_player.kitchen",
    }}, people_home=["person.bob"])
    install_checker(router)
    ctx = rule_context({"users": ["person.alice"]}, users=["person.alice"], channels=["voice"])
    ctx.metadata["bypass_channel_policy"] = True
    assert apply_for_preview(router, ctx, presence)["deliveries"] == []
    assert await router.async_route(ctx, flow) == []
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_audience_cannot_resurrect_legacy_user_after_ai():
    router, flow, presence = router_for({
        "alice": {"type": "telegram", "user": "alice", "chat_id": 1},
        "bob": {"type": "telegram", "user": "bob", "chat_id": 2},
    })
    install_checker(router)
    ctx = rule_context({"users": ["person.alice", "person.bob"]}, users=["person.alice", "person.bob"], channels=["alice", "bob"])
    ctx.metadata["bypass_channel_policy"] = True

    async def rewrite(**kwargs):
        ctx.users = ["person.bob"]
        ctx.user = "person.alice"
        return {"title": kwargs["title"], "message": kwargs["message"]}

    router._ai_client.async_rewrite_payload.side_effect = rewrite
    results = await router.async_route(ctx, flow)
    assert [(result["channel"], result["status"]) for result in results] == [("alice", "dropped"), ("bob", "sent")]
    assert ctx.user == "person.bob"
    assert router._hass.services.async_call.await_count == 1
    assert router._hass.services.async_call.await_args.args[2]["chat_id"] == [2]


@pytest.mark.asyncio
async def test_quiet_end_after_ai_does_not_expand_initial_text_route():
    router, flow, presence = router_for({
        "voice": {"type": "tts", "room": "kitchen", "entity_id": "media_player.kitchen"},
        "shared": {"type": "persistent_notification"},
    }, people_home=["person.alice"])
    presence.quiet_hours = True
    install_checker(router)
    ctx = rule_context({"quiet_hours": "text_only"}, channels=["voice", "shared"])
    ctx.metadata["bypass_channel_policy"] = True

    async def rewrite(**kwargs):
        router._presence.async_resolve.return_value = replace(presence, quiet_hours=False)
        return {"title": kwargs["title"], "message": kwargs["message"]}

    router._ai_client.async_rewrite_payload.side_effect = rewrite
    results = await router.async_route(ctx, flow)
    assert [(result["channel"], result["status"]) for result in results] == [("shared", "sent")]
    assert "policy_text_only" not in ctx.metadata
    assert router._hass.services.async_call.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["tts_entity", "tts_audio", "tv"])
async def test_rule_room_resolves_localized_mapping_keys(kind):
    data = {"room_targets": {"Гостиная": "media_player.living_room"}}
    if kind == "tts_audio":
        data["audio_targets"] = {"Living Room": [{"kind": "alisa", "entity_id": "media_player.living_room", "service": "tts.say"}]}
    if kind == "tv":
        data["notify_services"] = {"gostinaia": "notify.living_room"}
    router, flow, presence = router_for({"local": {
        "type": "tv" if kind == "tv" else "tts", "entity_id": "media_player.bedroom",
        "service": "notify.bedroom" if kind == "tv" else "tts.say", "data": data,
    }}, people_home=["person.alice"], states={"media_player.living_room": SimpleNamespace(state="playing")})
    install_checker(router)
    ctx = rule_context({"target_room": "living_room"}, channels=["local"], device="media_player.bedroom")
    preview = apply_for_preview(router, ctx, presence)
    results = await router.async_route(ctx, flow)
    assert preview["deliveries"][0]["target_entity_id"] == "media_player.living_room"
    assert results[0]["target_entity_id"] == "media_player.living_room"
    if kind == "tv":
        assert router._hass.services.async_call.await_args.args[:2] == ("notify", "living_room")
    else:
        assert router._hass.services.async_call.await_args.args[2]["entity_id"] == "media_player.living_room"


@pytest.mark.asyncio
@pytest.mark.parametrize("mapping", ["room_targets", "audio_targets", "notify_services"])
async def test_rule_room_rejects_ambiguous_canonical_mapping_keys(mapping):
    data = {"room_targets": {"living_room": "media_player.living_room"}, "notify_services": {"living_room": "notify.living_room"}}
    value = [{"entity_id": "media_player.living_room"}] if mapping == "audio_targets" else "media_player.living_room" if mapping == "room_targets" else "notify.living_room"
    data[mapping] = {"living_room": value, "Гостиная": value}
    router, flow, presence = router_for({"local": {
        "type": "tv" if mapping == "notify_services" else "tts", "room": "living_room", "entity_id": "media_player.living_room", "data": data,
    }}, people_home=["person.alice"], states={"media_player.living_room": SimpleNamespace(state="playing")})
    install_checker(router)
    ctx = rule_context({"target_room": "living_room"}, channels=["local"])
    ctx.metadata["bypass_channel_policy"] = True
    preview = apply_for_preview(router, ctx, presence)
    assert preview["deliveries"] == []
    assert preview["channel_decisions"][0]["reason"] == "policy_target_room"
    assert await router.async_route(ctx, flow) == []
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_canonical_room_keeps_one_local_device_priority():
    router, flow, presence = router_for({
        "voice": {"type": "tts", "data": {"audio_targets": {"Гостиная": [{"kind": "alisa", "entity_id": "media_player.speaker", "service": "tts.say"}]}}},
        "tv": {"type": "tv", "data": {"room_targets": {"Гостиная": "media_player.tv"}, "notify_services": {"Living Room": "notify.tv"}}},
    }, people_home=["person.alice"], states={key: SimpleNamespace(state="playing") for key in ["media_player.speaker", "media_player.tv"]})
    install_checker(router)
    ctx = rule_context({"target_room": "living_room"}, channels=["voice", "tv"])
    preview = apply_for_preview(router, ctx, presence)
    results = await router.async_route(ctx, flow)
    assert preview["resolved"]["final_channels"] == ["voice"]
    assert [(item["channel"], item["status"]) for item in results] == [("voice", "sent")]
    assert router._hass.services.async_call.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", ["synthesize", "store"])
@pytest.mark.parametrize("transition", ["quiet_mute", "quiet_text", "away", "disabled"])
async def test_hume_rechecks_rules_after_synthesis_and_storage_before_play(phase, transition):
    router, flow, presence = router_for({"hume": {
        "type": "tts_hume", "room": "kitchen", "entity_id": "media_player.kitchen", "data": {"api_key": "synthetic"},
    }}, people_home=["person.alice"])
    policy = {"quiet_hours": "text_only" if transition == "quiet_text" else "mute"} if transition != "away" else {"presence": "someone_home"}
    install_checker(router)
    ctx = rule_context(policy, channels=["hume"], room="kitchen")

    def change_snapshot():
        if transition == "disabled":
            router._config.channels["hume"].enabled = False
        elif transition == "away":
            router._presence.async_resolve.return_value = replace(presence, nobody_home=True, people_home=[])
        else:
            router._presence.async_resolve.return_value = replace(presence, quiet_hours=True)

    async def synthesize(**kwargs):
        if phase == "synthesize":
            change_snapshot()
        return b"audio"

    async def store(*args):
        if phase == "store":
            change_snapshot()
        return "/local/herald/hume/synthetic.mp3"

    router._hume_tts._async_synthesize = AsyncMock(side_effect=synthesize)
    router._hume_tts._async_store_audio = AsyncMock(side_effect=store)
    results = await router.async_route(ctx, flow)
    expected_reason = {"quiet_mute": "policy_quiet_hours", "quiet_text": "policy_text_only", "away": "policy_someone_home", "disabled": "policy_route_changed"}[transition]
    assert results == [{"channel": "hume", "status": "dropped", "reason": expected_reason, "flow": flow.name}]
    router._hume_tts._async_synthesize.assert_awaited_once()
    router._hume_tts._async_store_audio.assert_awaited_once()
    router._hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_hume_default_caller_still_plays_without_rule_guard():
    router, flow, _ = router_for({"hume": {
        "type": "tts_hume", "room": "kitchen", "entity_id": "media_player.kitchen", "data": {"api_key": "synthetic"},
    }}, people_home=["person.alice"])
    router._hume_tts._async_synthesize = AsyncMock(return_value=b"audio")
    router._hume_tts._async_store_audio = AsyncMock(return_value="/local/herald/hume/synthetic.mp3")
    ctx = context(channels=["hume"], room="kitchen")
    result = await router._hume_tts.async_deliver(channel=router._config.channels["hume"], text="Message", context=ctx)
    assert result["target_entity_id"] == "media_player.kitchen"
    assert router._hass.services.async_call.await_args.args[:2] == ("media_player", "play_media")
    router._presence.async_resolve.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["tts", "tv"])
@pytest.mark.parametrize("phase", ["turn_on", "volume_set"])
@pytest.mark.parametrize("transition", ["quiet", "away"])
async def test_generic_media_tts_rechecks_after_prep_before_audible_call(kind, phase, transition):
    target = {"entity_id": "media_player.kitchen", "service": "tts.speak", "engine_entity_id": "tts.engine", "turn_on": True, "volume_level": 0.4}
    data = {"room_targets": {"kitchen": "media_player.kitchen"}}
    if kind == "tts":
        data["audio_targets"] = {"kitchen": [target]}
    else:
        data.update({"engine_entity_id": "tts.engine", "turn_on": True, "volume_level": 0.4})
    router, flow, presence = router_for({"local": {
        "type": kind, "room": "kitchen", "entity_id": "media_player.kitchen", "service": "tts.speak", "data": data,
    }}, people_home=["person.alice"], states={"media_player.kitchen": SimpleNamespace(state="playing")})
    install_checker(router)
    policy = {"quiet_hours": "mute"} if transition == "quiet" else {"presence": "someone_home"}
    ctx = rule_context(policy, channels=["local"], room="kitchen")

    async def service(domain, name, data, **kwargs):
        if name == phase:
            router._presence.async_resolve.return_value = replace(presence, quiet_hours=True) if transition == "quiet" else replace(presence, nobody_home=True, people_home=[])

    router._hass.services.async_call.side_effect = service
    results = await router.async_route(ctx, flow)
    assert results[0]["status"] == "dropped"
    assert results[0]["reason"] == ("policy_quiet_hours" if transition == "quiet" else "policy_someone_home")
    assert all(call.args[:2] in [("media_player", "turn_on"), ("media_player", "volume_set")] for call in router._hass.services.async_call.await_args_list)
    assert ("media_player", phase) in [call.args[:2] for call in router._hass.services.async_call.await_args_list]


@pytest.mark.asyncio
@pytest.mark.parametrize("transition", ["quiet_mute", "quiet_text", "away"])
async def test_failed_tts_target_rechecks_rules_before_fallback(transition):
    targets = [{"kind": "alisa", "entity_id": "media_player.first", "service": "tts.say"},
               {"kind": "homepod", "entity_id": "media_player.second", "service": "tts.say"}]
    router, flow, presence = router_for({"voice": {
        "type": "tts", "room": "kitchen", "data": {"audio_targets": {"kitchen": targets}},
    }}, people_home=["person.alice"], states={target["entity_id"]: SimpleNamespace(state="playing") for target in targets})
    install_checker(router)
    policy = {"presence": "someone_home"} if transition == "away" else {"quiet_hours": "mute" if transition == "quiet_mute" else "text_only"}
    ctx = rule_context(policy, channels=["voice"], room="kitchen")

    async def fail_first_target(*args, **kwargs):
        router._presence.async_resolve.return_value = replace(presence, nobody_home=True, people_home=[]) if transition == "away" else replace(presence, quiet_hours=True)
        raise ValueError("Rejected before delivery")

    router._hass.services.async_call.side_effect = fail_first_target
    results = await router.async_route(ctx, flow)
    assert results[0]["status"] == "dropped"
    assert results[0]["reason"] == {"quiet_mute": "policy_quiet_hours", "quiet_text": "policy_text_only", "away": "policy_someone_home"}[transition]
    assert router._hass.services.async_call.await_count == 1
    assert router._hass.services.async_call.await_args.args[2]["entity_id"] == "media_player.first"


@pytest.mark.asyncio
async def test_tv_overlay_final_guard_does_not_call_notify_after_presence_change():
    router, flow, presence = router_for({"tv": {
        "type": "tv", "room": "kitchen", "entity_id": "media_player.kitchen", "service": "notify.kitchen",
    }}, people_home=["person.alice"], states={"media_player.kitchen": SimpleNamespace(state="playing")})
    install_checker(router)
    router._presence.async_resolve.side_effect = [presence, presence, replace(presence, nobody_home=True, people_home=[])]
    results = await router.async_route(rule_context({"presence": "someone_home"}, channels=["tv"], room="kitchen"), flow)
    assert results[0]["status"] == "dropped" and results[0]["reason"] == "policy_someone_home"
    router._hass.services.async_call.assert_not_awaited()
