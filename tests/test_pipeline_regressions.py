"""Coordinator regression tests using real prechecks and routing decisions."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.herald import coordinator as coordinator_module
from custom_components.herald.context_builder import ResolvedUserProfile, RuntimeContext
from custom_components.herald.coordinator import HeraldCoordinator
from custom_components.herald.models import (
    ChannelConfig,
    FlowConfig,
    HeraldConfig,
    NotificationContext,
    PresenceSnapshot,
    RuntimeState,
)
from custom_components.herald.notification_policies import NotificationPolicyManager
from custom_components.herald.router import HeraldRouter


@pytest.fixture
def coordinator(monkeypatch, tmp_path):
    now = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(coordinator_module.dt_util, "now", lambda: now)
    monkeypatch.setattr(
        coordinator_module.dt_util, "parse_datetime",
        lambda value: datetime.fromisoformat(value) if value else None, raising=False,
    )
    instance = HeraldCoordinator.__new__(HeraldCoordinator)
    flow = FlowConfig(name="system_events", channels=["persistent_default"], dedup_window_seconds=0, cooldown_seconds=0)
    instance.config = HeraldConfig(flows={flow.name: flow}, channels={
        "persistent_default": ChannelConfig(name="persistent_default", channel_type="persistent_notification"),
        "system_log_default": ChannelConfig(name="system_log_default", channel_type="system_log"),
        "voice": ChannelConfig(name="voice", channel_type="tts", entity_id="media_player.kitchen"),
        "alice": ChannelConfig(name="alice", channel_type="mobile_app", user="alice", service="notify.mobile_app_alice"),
        "bob": ChannelConfig(name="bob", channel_type="mobile_app", user="bob", service="notify.mobile_app_bob"),
    })
    instance._state = RuntimeState(current_day=now.date().isoformat())
    instance.entry = SimpleNamespace(entry_id="test_entry")
    instance.hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity: None, async_all=lambda domain=None: []),
        services=SimpleNamespace(async_call=AsyncMock()),
        async_create_task=lambda coro: coro.close(),
    )
    instance.controls = SimpleNamespace(
        maintenance_mode_enabled=lambda: False,
        is_mute_all_enabled=lambda: False,
        is_level_enabled=lambda level: True,
        is_channel_type_enabled=lambda kind: True,
        user_language=lambda user, default="ru": "en",
        user_character=lambda user, default=None: default or "hestia",
        room_audio_target=lambda room, default="auto": default,
        user_silent=lambda user: False,
    )
    instance._notification_policy_overrides = {}
    instance.notification_policies = NotificationPolicyManager(tmp_path)
    instance._async_persist_and_publish = AsyncMock()
    instance._async_refresh_runtime_sources = AsyncMock()
    instance._async_augment_runtime_config = AsyncMock()
    instance._sync_controls = lambda: False
    instance.queue = SimpleNamespace(async_enqueue=AsyncMock())
    instance.context_builder = SimpleNamespace(async_build=AsyncMock(return_value=RuntimeContext()))
    instance.presence = SimpleNamespace(
        async_resolve=AsyncMock(return_value=PresenceSnapshot(nobody_home=True)), away_channels=lambda: [],
        room_sensors=lambda: {},
    )
    instance.ai_client = SimpleNamespace(
        should_use_ai=lambda level: False,
        async_summarize_notifications=AsyncMock(return_value={"title": "Summary", "message": "Two events"}),
        async_rewrite_payload=AsyncMock(side_effect=lambda **kwargs: {"title": kwargs["title"], "message": kwargs["message"]}),
    )
    instance.router = HeraldRouter(instance.hass, instance.config, instance.ai_client, instance.presence, instance.controls)
    return instance


def _context(**kwargs):
    return NotificationContext(
        flow="system_events", event="washer_done", title="Laundry", message="Finished",
        level="info", source="automation.laundry", timestamp="2026-09-30T12:00:00+00:00",
        **kwargs,
    )


@pytest.mark.asyncio
async def test_summary_preserves_routing_audience_options_and_highest_level(coordinator) -> None:
    flow = coordinator.config.flows["system_events"]
    first = _context(
        channels=["bob"], users=["person.bob"], user="person.bob", room="kitchen", device="sensor.washer",
        metadata={"channels_explicit": True, "audience_explicit": True, "audience_resolved": True,
                  "notification_key": "washer_done", "notification_policy": {"delivery_mode": "push_only"},
                  "mobile_options": {"tag": "laundry"}},
        group="chores", suppress_seconds=3600, include_actions=True, entities=["sensor.washer"],
    )
    second = replace(first, event="dryer_done", level="warning", entities=["sensor.dryer"],
                     metadata={**first.metadata, "notification_key": "dryer_done"})

    summary = await coordinator._async_build_summary_context(flow, [first, second])

    assert summary.level == "warning"
    assert summary.channels == ["bob"]
    assert summary.users == ["person.bob"]
    assert (summary.user, summary.room, summary.device, summary.group) == (first.user, first.room, first.device, first.group)
    assert summary.metadata["notification_policy"] == first.metadata["notification_policy"]
    assert summary.metadata["mobile_options"] == {"tag": "laundry"}
    assert summary.metadata["notification_keys"] == ["washer_done", "dryer_done"]
    assert summary.entities == ["sensor.washer", "sensor.dryer"]
    assert summary.include_actions
    assert not summary.summarize and not summary.rewrite
    assert coordinator.ai_client.async_summarize_notifications.call_args.kwargs["language"] == "en"
    preview = coordinator.router.build_route_preview(summary, flow, PresenceSnapshot(nobody_home=True))
    assert preview["resolved"]["final_channels"] == ["bob"]


@pytest.mark.asyncio
async def test_summarize_false_delivers_individually_and_never_calls_summary(coordinator) -> None:
    first = _context(summarize=False, rewrite=False, channels=["persistent_default"])
    second = replace(first, message="Second")
    await coordinator.async_process_notifications([first, second])

    coordinator.ai_client.async_summarize_notifications.assert_not_called()
    assert coordinator.hass.services.async_call.await_count == 2
    assert coordinator._state.notifications_today == 2


@pytest.mark.asyncio
async def test_summary_records_cooldown_for_every_constituent_notification_key(coordinator) -> None:
    first = _context(rewrite=False, channels=["persistent_default"], metadata={"notification_key": "washer_done"})
    second = replace(first, event="dryer_done", metadata={"notification_key": "dryer_done"})
    await coordinator.async_process_notifications([first, second])

    assert set(coordinator._state.last_notification_delivery) == {"washer_done", "dryer_done"}
    assert coordinator._state.notifications_today == 1
    assert coordinator.hass.services.async_call.await_count == 1


@pytest.mark.asyncio
async def test_maintenance_redirect_is_final_after_custom_policy(coordinator) -> None:
    coordinator.controls.maintenance_mode_enabled = lambda: True
    coordinator._notification_policy_overrides["washer_done"] = {"delivery_mode": "custom", "channels": ["voice"]}
    context = _context(channels=["voice"])
    flow = coordinator.config.flows[context.flow]

    checks = await coordinator._async_routing_prechecks(context, flow)
    preview = coordinator.router.build_route_preview(context, flow, PresenceSnapshot(nobody_home=True))

    assert checks["blocked_reason"] is None
    assert checks["maintenance_redirect"]
    assert preview["resolved"]["final_channels"] == ["persistent_default", "system_log_default"]
    assert not context.rewrite and not context.summarize


@pytest.mark.parametrize("override, elapsed, expected", [(60, 30, True), (60, 61, False), (0, 30, False)])
def test_notification_cooldown_override_uses_its_own_history(coordinator, override, elapsed, expected) -> None:
    flow = coordinator.config.flows["system_events"]
    flow.cooldown_seconds = 3600
    now = coordinator_module.dt_util.now()
    coordinator._state.last_flow_delivery[flow.name] = now.isoformat()
    coordinator._state.last_notification_delivery["washer_done"] = (now - timedelta(seconds=elapsed)).isoformat()
    context = _context(metadata={"notification_key": "washer_done", "notification_policy": {"cooldown_override": override}})
    assert coordinator._drop_for_cooldown(flow.name, flow, context) is expected
    other = replace(context, event="dryer_done", metadata={**context.metadata, "notification_key": "dryer_done"})
    assert not coordinator._drop_for_cooldown(flow.name, flow, other)


def test_dedup_includes_recipient_and_keeps_long_per_request_suppression(coordinator, monkeypatch) -> None:
    flow = coordinator.config.flows["system_events"]
    flow.dedup_window_seconds = 5
    now = coordinator_module.dt_util.now()
    alice = _context(users=["person.alice"], suppress_seconds=3600)
    bob = replace(alice, users=["person.bob"])
    assert not coordinator._drop_for_dedup(flow, alice)
    assert not coordinator._drop_for_dedup(flow, bob)
    monkeypatch.setattr(coordinator_module.dt_util, "now", lambda: now + timedelta(minutes=30))
    coordinator._prune_dedup_cache(coordinator_module.dt_util.now())
    assert coordinator._drop_for_dedup(flow, alice)
    assert coordinator._drop_for_dedup(flow, bob)
    monkeypatch.setattr(coordinator_module.dt_util, "now", lambda: now + timedelta(hours=2))
    assert not coordinator._drop_for_dedup(flow, alice)


@pytest.mark.asyncio
async def test_preview_does_not_reserve_dedup_and_real_admission_does(coordinator) -> None:
    flow = coordinator.config.flows["system_events"]
    flow.dedup_window_seconds = 3600
    payload = {"event": "washer_done", "message": "Finished", "channels": ["persistent_default"]}

    preview = await coordinator.async_preview_route(payload)
    assert preview["prechecks"]["will_deliver"]
    assert not coordinator._state.dedup_cache
    coordinator.hass.services.async_call.assert_not_called()
    await coordinator.async_handle_service_notify(payload)
    assert coordinator.queue.async_enqueue.await_count == 1
    assert coordinator._state.dedup_cache
    preview = await coordinator.async_preview_route(payload)
    assert preview["prechecks"]["blocked_reason"] == "deduplicated"
    assert not preview["prechecks"]["will_deliver"]
    await coordinator.async_handle_service_notify(payload)
    assert coordinator.queue.async_enqueue.await_count == 1


@pytest.mark.asyncio
async def test_preview_and_delivery_share_disabled_policy_without_dedup_mutation(coordinator) -> None:
    coordinator.config.flows["system_events"].dedup_window_seconds = 3600
    coordinator._notification_policy_overrides["washer_done"] = {"enabled": False}
    payload = {"event": "washer_done", "message": "Finished", "channels": ["persistent_default"]}
    preview = await coordinator.async_preview_route(payload)
    await coordinator.async_handle_service_notify(payload)

    assert preview["prechecks"]["blocked_reason"] == "notification_policy_disabled"
    assert not preview["prechecks"]["will_deliver"]
    assert coordinator._state.drop_reasons == {"notification_policy_disabled": 1}
    assert not coordinator._state.dedup_cache
    coordinator.queue.async_enqueue.assert_not_called()
    coordinator.hass.services.async_call.assert_not_called()


@pytest.mark.parametrize("users, expected_user", [(["person.bob"], "person.bob"), ([], None)])
@pytest.mark.asyncio
async def test_explicit_audience_does_not_acquire_unrelated_local_user(coordinator, users, expected_user) -> None:
    coordinator.context_builder.async_build.return_value = RuntimeContext(
        people_home=["person.alice"], users=[
            ResolvedUserProfile(person_entity_id="person.alice", slug="alice", name="Alice", home=True),
            ResolvedUserProfile(person_entity_id="person.bob", slug="bob", name="Bob", home=False),
        ],
    )
    *_, context = await coordinator._async_prepare_service_context({"event": "washer_done", "message": "Finished", "users": users})

    assert context.users == users
    assert context.user == expected_user
    assert context.metadata["audience_explicit"]
    assert context.metadata["audience_resolved"]


@pytest.mark.parametrize("status, expected_requests", [("rewritten", 1), ("fallback", 1), ("passthrough", 0), (None, 0)])
@pytest.mark.asyncio
async def test_summary_metrics_count_actual_ai_attempt_once_per_batch(coordinator, status, expected_requests) -> None:
    coordinator.ai_client.async_summarize_notifications.return_value = {
        "title": "Summary", "message": "Two events", "_herald_ai_status": status,
    }
    coordinator.config.flows["system_events"].summary_personality = "hestia"
    first = _context(rewrite=False, channels=["persistent_default", "system_log_default"])
    second = replace(first, event="dryer_done")
    await coordinator.async_process_notifications([first, second])

    assert coordinator._state.ai_requests_today == expected_requests
    assert coordinator._state.ai_character_counts.get("hestia", 0) == expected_requests
    assert coordinator.hass.services.async_call.await_count == 2
