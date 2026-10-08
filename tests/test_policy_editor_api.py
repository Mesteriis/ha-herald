"""Rule editor previews use production routing and never save or deliver drafts."""

from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from test_pipeline_regressions import coordinator  # noqa: F401

from custom_components.herald import coordinator as coordinator_module
from custom_components.herald.models import PresenceSnapshot, RuntimeState
from custom_components.herald.notification_policies import literal_preview_request
from custom_components.herald.policy_editor import build_preview_request
from custom_components.herald.services import PREVIEW_NOTIFICATION_POLICY_SCHEMA


@pytest.fixture
def editor(coordinator):  # noqa: F811
    coordinator._notification_registry = {"washer_done": {
        "notification_key": "washer_done", "title": "Laundry finished",
        "preview_request": {"channels": ["persistent_default"], "level": "info"},
    }}
    coordinator._notification_registry_refreshed_at = None
    coordinator._notification_policies_store = type("Storage", (), {"async_save": AsyncMock()})()
    return coordinator


@pytest.mark.asyncio
async def test_draft_isolated_from_saved_policy_delivery_ai_and_runtime_state(editor):
    editor._notification_policy_overrides["washer_done"] = {"enabled": True}
    before_state = deepcopy(editor._state.to_dict())
    before_rules = deepcopy(editor._notification_policy_overrides)
    result = await editor.async_preview_notification_policy({
        "notification_key": "washer_done", "policy": {"enabled": False},
    })
    assert result["explanation"]["status"] == "blocked"
    assert result["prechecks"]["blocked_reason"] == "notification_policy_disabled"
    assert editor._state.to_dict() == before_state
    assert editor._notification_policy_overrides == before_rules
    editor._notification_policies_store.async_save.assert_not_awaited()
    editor._async_persist_and_publish.assert_not_awaited()
    editor.hass.services.async_call.assert_not_awaited()
    editor.queue.async_enqueue.assert_not_awaited()
    editor.ai_client.async_rewrite_payload.assert_not_awaited()
    editor.ai_client.async_summarize_notifications.assert_not_awaited()


@pytest.mark.asyncio
async def test_draft_empty_custom_channels_do_not_fall_back(editor):
    result = await editor.async_preview_notification_policy({
        "notification_key": "washer_done", "policy": {"delivery_mode": "custom", "channels": []},
    })
    assert result["explanation"]["status"] == "no_targets"
    assert result["resolved"]["final_channels"] == []


@pytest.mark.asyncio
async def test_preview_draft_cooldown_and_real_checks_agree(editor):
    editor._state.last_notification_delivery["washer_done"] = coordinator_module.dt_util.now().isoformat()
    result = await editor.async_preview_notification_policy({
        "notification_key": "washer_done", "policy": {"cooldown_override": 60},
    })
    assert result["prechecks"]["blocked_reason"] == "flow_cooldown"
    assert "washer_done" not in editor._notification_policy_overrides


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", ["away", "quiet_hours"])
async def test_scenarios_are_disposable_and_explain_limits(editor, scenario):
    actual = PresenceSnapshot(people_home=["person.alice"], nobody_home=False, occupied_rooms=["kitchen"], primary_room="kitchen")
    editor.presence.async_resolve.return_value = actual
    result = await editor.async_preview_notification_policy({"notification_key": "washer_done", "scenario": scenario})
    assert result["scenario"] == scenario
    assert result["warnings"]
    if scenario == "away":
        assert result["presence"]["nobody_home"]
        assert result["runtime_context"]["people_home"] == []
    else:
        assert result["presence"]["quiet_hours"]
    assert actual.people_home == ["person.alice"]
    assert not actual.quiet_hours
    editor.hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_preview_does_not_prune_expired_snoozes(editor):
    editor._state.snoozed_flows["system_events"] = (coordinator_module.dt_util.now() - timedelta(minutes=1)).isoformat()
    before = deepcopy(editor._state.to_dict())
    await editor.async_preview_notification_policy({"notification_key": "washer_done"})
    assert editor._state.to_dict() == before


@pytest.mark.asyncio
async def test_real_dropped_and_sent_events_expose_last_decision(editor):
    editor._notification_policy_overrides["washer_done"] = {"enabled": False}
    await editor.async_handle_service_notify({"event": "washer_done", "message": "Finished"})
    item = editor.notification_registry_snapshot()["items"][0]
    assert item["last_decision"]["status"] == "dropped"
    assert item["last_decision"]["reason"] == "notification_policy_disabled"
    editor._notification_policy_overrides.clear()
    _, _, _, flow, context = await editor._async_prepare_service_context({"event": "washer_done", "message": "Finished"})
    await editor.async_process_notifications([context])
    item = editor.notification_registry_snapshot()["items"][0]
    assert item["last_decision"]["status"] == "sent"
    assert editor._state.recent_notifications[0]["explanation"]["steps"]
    restored = RuntimeState.from_dict(editor._state.to_dict())
    assert restored.last_decisions == editor._state.last_decisions


def test_literals_preserve_empty_allowlist_and_audience_and_mark_dynamic_fields():
    literal, unknown = literal_preview_request({"channels": [], "users": ["person.alice"], "flow": "{{ dynamic }}", "message": "private"})
    assert literal == {"channels": [], "users": ["person.alice"]}
    assert unknown == ["flow"]
    values, warnings = build_preview_request({"notification_key": "test", "preview_request": literal, "preview_unknown_fields": unknown}, None)
    assert values["channels"] == []
    assert values["users"] == ["person.alice"]
    assert any("шаблонами" in item for item in warnings)


def test_preview_schema_rejects_unbounded_cooldowns_and_unknown_modes():
    import voluptuous as vol
    for draft in ({"cooldown_override": -1}, {"cooldown_override": 86401}, {"delivery_mode": "unknown"}, {"level_override": "unknown"}):
        with pytest.raises(vol.Invalid):
            PREVIEW_NOTIFICATION_POLICY_SCHEMA({"notification_key": "test", "policy": draft})


@pytest.mark.asyncio
async def test_sparse_discovered_channel_preferences_preserve_transport_and_disappearance(editor, monkeypatch):
    from types import SimpleNamespace

    from custom_components.herald.models import HeraldConfig
    raw = {"channels": {"phone": {"enabled": False, "min_level": "warning"}}}
    editor._raw_config = raw
    editor.config = HeraldConfig.from_raw(raw)
    editor.entry = SimpleNamespace(entry_id="test", data={})
    editor._apply_plugin_extensions = lambda: None
    editor._apply_default_tv_routing_rules = lambda: None
    discovery = AsyncMock(return_value={"phone": {"type": "mobile_app", "service": "notify.mobile_app_phone", "user": "alice"}})
    monkeypatch.setattr(coordinator_module, "async_discover_runtime_channels", discovery)
    await type(editor)._async_augment_runtime_config(editor)
    assert editor.config.channels["phone"].channel_type == "mobile_app"
    assert editor.config.channels["phone"].service == "notify.mobile_app_phone"
    assert not editor.config.channels["phone"].enabled
    discovery.return_value = {}
    await type(editor)._async_augment_runtime_config(editor)
    assert "phone" not in editor.config.channels
    discovery.return_value = {"phone": {"type": "mobile_app", "service": "notify.mobile_app_phone"}}
    await type(editor)._async_augment_runtime_config(editor)
    assert not editor.config.channels["phone"].enabled


def test_preview_preserves_event_distinct_from_policy_key():
    values, _ = build_preview_request({"notification_key": "washer_done", "preview_request": {"event": "Laundry"}}, "Finished")
    assert values["event"] == "Laundry"
    assert values["metadata"]["notification_key"] == "washer_done"
