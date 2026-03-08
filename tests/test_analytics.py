"""Tests for Herald analytics counters."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.herald.coordinator import HeraldCoordinator
from custom_components.herald.models import NotificationContext, RuntimeState


def test_record_delivery_updates_analytics_counters() -> None:
    traces: list[dict[str, object]] = []
    state = RuntimeState(current_day="2026-03-08")

    async def _async_persist_and_publish() -> None:
        return None

    fake = SimpleNamespace(
        _state=state,
        _reset_daily_counters_if_needed=lambda: None,
        ai_client=SimpleNamespace(should_use_ai=lambda level: True),
        _history_limit=lambda: 20,
        _append_trace=lambda item: traces.append(item),
        _async_persist_and_publish=_async_persist_and_publish,
        hass=SimpleNamespace(async_create_task=lambda coro: coro.close()),
    )
    fake._record_result_metrics = lambda context, results: HeraldCoordinator._record_result_metrics(
        fake,
        context,
        results,
    )
    context = NotificationContext(
        flow="camera_alerts",
        event="motion",
        title="Camera",
        message="Motion detected",
        level="warning",
        source="automation.camera",
        timestamp="2026-03-08T12:00:00+00:00",
        notification_id="notif_analytics_1",
        character="domovoy",
        rewrite=True,
    )
    results = [
        {"channel": "dashboard_default", "status": "sent"},
        {"channel": "mobile_macbook", "status": "error"},
        {"channel": "tv_auto", "status": "dropped", "reason": "tv_inactive"},
    ]

    HeraldCoordinator._record_delivery(fake, context, results, grouped_count=1)

    assert state.notifications_today == 1
    assert state.deliveries_today == 1
    assert state.errors_today == 1
    assert state.dropped_today == 1
    assert state.ai_requests_today == 1
    assert state.channel_delivery_counts["dashboard_default"] == 1
    assert state.channel_error_counts["mobile_macbook"] == 1
    assert state.drop_reasons["tv_inactive"] == 1
    assert state.ai_character_counts["domovoy"] == 1
    assert traces[-1]["stage"] == "delivered"


def test_record_drop_metric_tracks_pre_route_drops() -> None:
    traces: list[dict[str, object]] = []
    state = RuntimeState(current_day="2026-03-08")
    fake = SimpleNamespace(
        _state=state,
        _reset_daily_counters_if_needed=lambda: None,
        _append_trace=lambda item: traces.append(item),
    )

    HeraldCoordinator._record_drop_metric(
        fake,
        reason="flow_disabled",
        flow="system_events",
        level="warning",
    )

    assert state.dropped_today == 1
    assert state.drop_reasons["flow_disabled"] == 1
    assert traces[0]["stage"] == "analytics_drop"
