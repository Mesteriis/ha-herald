"""Rule editor, admission, and queued delivery agree on explicit constraints."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from test_pipeline_regressions import coordinator  # noqa: F401
from test_policy_editor_api import editor  # noqa: F401

from custom_components.herald.context_builder import ResolvedUserProfile, RuntimeContext
from custom_components.herald.models import ChannelConfig, HeraldConfig, PresenceSnapshot
from custom_components.herald.router import HeraldRouter
from custom_components.herald.rule_options import rule_options


@pytest.fixture
def rules(editor):  # noqa: F811
    people = [ResolvedUserProfile(person_entity_id=f"person.{name}", slug=name, name=name.title(), home=True)
              for name in ("alice", "bob")]
    editor.context_builder.async_build.return_value = RuntimeContext(users=people, people_home=[p.person_entity_id for p in people])
    editor.hass.states.async_all = lambda domain=None: [
        SimpleNamespace(entity_id=p.person_entity_id, attributes={"friendly_name": p.name}) for p in people
    ] if domain == "person" else []
    editor.presence.async_resolve.return_value = PresenceSnapshot(nobody_home=False, people_home=["person.alice", "person.bob"])
    editor.presence.room_sensors = lambda: {"kitchen": "binary_sensor.kitchen"}
    editor.router = HeraldRouter(editor.hass, editor.config, editor.ai_client, editor.presence, editor.controls,
                                 rule_checker=editor._check_notification_rule)
    editor.async_request_refresh = AsyncMock()
    return editor


@pytest.mark.asyncio
@pytest.mark.parametrize("policy, reason", [
    ({"users": []}, "notification_policy_no_recipients"),
    ({"users": ["person.missing"]}, "policy_unknown_user"),
    ({"target_room": "missing"}, "policy_unknown_room"),
    ({"target_room": ""}, "policy_unknown_room"),
    ({"presence": "nobody_home"}, "policy_nobody_home"),
])
async def test_draft_and_actual_admission_block_identically_without_side_effects(rules, policy, reason):
    before = deepcopy(rules._state.to_dict())
    preview = await rules.async_preview_notification_policy({"notification_key": "washer_done", "policy": policy})
    assert preview["prechecks"]["blocked_reason"] == reason
    assert not preview["prechecks"]["will_deliver"]
    assert rules._state.to_dict() == before
    rules._notification_policies_store.async_save.assert_not_awaited()
    rules._notification_policy_overrides["washer_done"] = policy
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic", "force": True})
    assert rules._state.drop_reasons == {reason: 1}
    rules.queue.async_enqueue.assert_not_awaited()
    rules.hass.services.async_call.assert_not_awaited()
    rules.ai_client.async_rewrite_payload.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario, policy, reason", [
    ("away", {"presence": "someone_home"}, "policy_someone_home"),
    ("quiet_hours", {"quiet_hours": "mute"}, "policy_quiet_hours"),
])
async def test_preview_scenario_applies_new_conditions_without_changing_real_presence(rules, scenario, policy, reason):
    result = await rules.async_preview_notification_policy({"notification_key": "washer_done", "policy": policy, "scenario": scenario})
    assert result["prechecks"]["blocked_reason"] == reason
    current = await rules.async_preview_notification_policy({"notification_key": "washer_done", "policy": policy})
    assert current["prechecks"]["will_deliver"]
    assert not rules.presence.async_resolve.return_value.quiet_hours
    assert not rules.presence.async_resolve.return_value.nobody_home


@pytest.mark.asyncio
async def test_rule_cannot_expand_explicit_request_audience(rules):
    rules._notification_policy_overrides["washer_done"] = {"users": ["person.bob"]}
    result = await rules.async_preview_route({"event": "washer_done", "message": "Synthetic", "users": ["alice"]})
    assert result["prechecks"]["blocked_reason"] == "notification_policy_no_recipients"
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic", "users": ["bob"]})
    queued = rules.queue.async_enqueue.await_args.args[0]
    assert queued.users == ["person.bob"]
    assert queued.user == "person.bob"


@pytest.mark.asyncio
@pytest.mark.parametrize("policy, updated, reason", [
    ({"presence": "someone_home"}, PresenceSnapshot(nobody_home=True), "policy_someone_home"),
    ({"quiet_hours": "mute"}, PresenceSnapshot(nobody_home=False, quiet_hours=True), "policy_quiet_hours"),
])
async def test_queue_rechecks_before_summary_and_records_reason(rules, policy, updated, reason):
    rules._notification_policy_overrides["washer_done"] = policy
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic", "summarize": True, "immediately": False})
    first = rules.queue.async_enqueue.await_args.args[0]
    rules.presence.async_resolve.return_value = updated
    await rules.async_process_notifications([first, replace(first, message="Second")])
    assert rules._state.drop_reasons == {reason: 2}
    assert rules._state.last_decisions["washer_done"]["reason"] == reason
    rules.ai_client.async_summarize_notifications.assert_not_awaited()
    rules.ai_client.async_rewrite_payload.assert_not_awaited()
    rules.hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_rule_rechecked_after_summary_await(rules):
    rules._notification_policy_overrides["washer_done"] = {"quiet_hours": "mute"}
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic", "summarize": True, "immediately": False})
    first = rules.queue.async_enqueue.await_args.args[0]

    async def summarize(*args, **kwargs):
        rules.presence.async_resolve.return_value = PresenceSnapshot(nobody_home=False, quiet_hours=True)
        return {"title": "Synthetic", "message": "Summary"}

    rules.ai_client.async_summarize_notifications.side_effect = summarize
    await rules.async_process_notifications([first, replace(first, message="Second")])
    rules.ai_client.async_summarize_notifications.assert_awaited_once()
    rules.hass.services.async_call.assert_not_awaited()
    assert rules._state.last_decisions["washer_done"]["reason"] == "policy_quiet_hours"


@pytest.mark.asyncio
async def test_queue_honors_new_silent_mode_and_does_not_resurrect_selected_user(rules):
    rules._notification_policy_overrides["washer_done"] = {"users": ["person.alice"]}
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic"})
    context = rules.queue.async_enqueue.await_args.args[0]
    rules.controls.user_silent = lambda user: user == "alice"
    await rules.async_process_notifications([context])
    assert context.users == [] and context.user is None
    assert rules._state.last_decisions["washer_done"]["reason"] == "notification_policy_no_recipients"
    rules.hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_inherited_audience_honors_silence_changed_during_rewrite(rules):
    rules._notification_policy_overrides["washer_done"] = {"quiet_hours": "mute"}
    rules.presence.async_resolve.return_value = PresenceSnapshot(nobody_home=True)
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic", "users": ["alice"],
                                            "channels": ["alice"], "rewrite": True})
    context = rules.queue.async_enqueue.await_args.args[0]

    async def rewrite(**kwargs):
        rules.controls.user_silent = lambda user: user == "alice"
        return {"title": kwargs["title"], "message": kwargs["message"]}

    rules.ai_client.async_rewrite_payload.side_effect = rewrite
    await rules.async_process_notifications([context])
    assert context.users == [] and context.user is None
    rules.hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_save_preserves_new_fields_reset_and_queued_rule_snapshot(rules):
    await rules.async_set_notification_policy({"notification_key": "washer_done", "users": ["alice"],
                                              "target_room": "kitchen", "presence": "someone_home", "quiet_hours": "mute"})
    await rules.async_set_notification_policy({"notification_key": "washer_done", "notes": "A note"})
    stored = rules._notification_policy_overrides["washer_done"]
    assert stored["users"] == ["person.alice"]
    assert stored["target_room"] == "kitchen"
    assert stored["presence"] == "someone_home" and stored["quiet_hours"] == "mute"
    await rules.async_handle_service_notify({"event": "washer_done", "message": "Synthetic"})
    context = rules.queue.async_enqueue.await_args.args[0]
    await rules.async_reset_notification_policy("washer_done")
    assert "washer_done" not in rules._notification_policy_overrides
    assert context.metadata["notification_policy"]["quiet_hours"] == "mute"
    rules.presence.async_resolve.return_value = PresenceSnapshot(nobody_home=False, quiet_hours=True)
    await rules.async_process_notifications([context])
    rules.hass.services.async_call.assert_not_awaited()


def test_catalog_and_snapshot_use_existing_people_and_concrete_rooms(rules):
    rules.config.users = HeraldConfig.from_raw({"users": {"Alice": {"name": "Configured alias"}}}).users
    rules.config.channels["mapped"] = ChannelConfig(name="mapped", channel_type="tts", room=" ", data={"room_targets": {"study": "media_player.study", "auto": "media_player.fallback", "  ": "media_player.unscoped"}})
    options = rule_options(rules.hass, rules.config, rules.presence)
    assert options["user_options"] == [{"value": "person.alice", "label": "Alice"}, {"value": "person.bob", "label": "Bob"}]
    assert {item["value"] for item in options["room_options"]} == {"kitchen", "study"}
    snapshot = rules.notification_registry_snapshot()
    assert snapshot["room_options"] == options["room_options"]
    assert snapshot["items"][0]["available_users"] == options["user_options"]
