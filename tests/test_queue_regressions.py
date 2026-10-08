"""Regression coverage for deadlines, recipients and safe queue draining."""

from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from custom_components.herald.models import NotificationContext
from custom_components.herald.queue import NotificationQueueManager


class _FakeHass:
    def __init__(self) -> None:
        self.tasks: list[asyncio.Task[None]] = []

    def async_create_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.append(task)
        return task


class _EagerHass(_FakeHass):
    def async_create_task(self, coro):
        task = asyncio.create_task(coro, eager_start=True)
        self.tasks.append(task)
        return task


class _Coordinator:
    def __init__(self) -> None:
        self.hass = _FakeHass()
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.release.set()
        self.processed: list[list[NotificationContext]] = []
        self.snapshots: list[list[dict[str, object]]] = []
        self.failure: str | None = None
        self.cancelled = False

    def async_set_queue_state(self, items: list[dict[str, object]]) -> None:
        self.snapshots.append(items)

    async def async_process_notifications(self, notifications: list[NotificationContext]) -> None:
        self.started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise
        if notifications[0].notification_id == self.failure:
            raise RuntimeError("delivery failed")
        self.processed.append(notifications)


def _context(notification_id: str, **kwargs) -> NotificationContext:
    return NotificationContext(
        flow="system_events",
        title=notification_id,
        message=notification_id,
        level="info",
        source="automation.test",
        timestamp="2026-03-08T11:00:00+00:00",
        notification_id=notification_id,
        immediately=False,
        **kwargs,
    )


async def _wait_for_worker(coordinator: _Coordinator) -> None:
    await asyncio.wait_for(coordinator.started.wait(), timeout=1)
    await asyncio.wait_for(asyncio.shield(coordinator.hass.tasks[-1]), timeout=1)


@pytest.mark.asyncio
async def test_urgent_enqueue_reschedules_timer_without_flushing_unrelated_groups() -> None:
    coordinator = _Coordinator()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("later", group="later"), summary_window_seconds=3600)
    await manager.async_enqueue(_context("urgent", group="urgent"), summary_window_seconds=0)

    await _wait_for_worker(coordinator)

    assert [[item.notification_id for item in batch] for batch in coordinator.processed] == [["urgent"]]
    assert manager.size == 1
    assert coordinator.snapshots[-1][0]["notification_id"] == "later"
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_eager_worker_finishing_before_deadline_reschedules_pending_notification() -> None:
    coordinator = _Coordinator()
    coordinator.hass = _EagerHass()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("later"), summary_window_seconds=3600)
    manager._cancel_timer()

    manager._start_flush()

    assert manager.size == 1
    assert manager._flush_task is None
    assert manager._flush_timer is not None
    assert not manager._flush_timer.cancelled()
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_eager_worker_completed_delivery_does_not_block_next_enqueue() -> None:
    coordinator = _Coordinator()
    coordinator.hass = _EagerHass()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("first"), summary_window_seconds=0)
    manager._cancel_timer()

    manager._start_flush()

    assert manager.size == 0
    assert manager._flush_task is None
    await manager.async_enqueue(_context("second"), summary_window_seconds=0)
    async def wait_for_second() -> None:
        while len(coordinator.processed) < 2:
            await asyncio.sleep(0.01)

    await asyncio.wait_for(wait_for_second(), timeout=1)
    assert [[item.notification_id for item in batch] for batch in coordinator.processed] == [["first"], ["second"]]
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_enqueue_during_delivery_is_processed_without_another_enqueue() -> None:
    coordinator = _Coordinator()
    coordinator.release.clear()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("first"), summary_window_seconds=0)
    await asyncio.wait_for(coordinator.started.wait(), timeout=1)
    diagnostics = manager.diagnostic_snapshot()
    assert diagnostics["worker_active"] is True
    assert any("async_process_notifications" in step for step in diagnostics["await_path"])
    await manager.async_enqueue(_context("second"), summary_window_seconds=0)

    coordinator.release.set()
    await _wait_for_worker(coordinator)

    assert [[item.notification_id for item in batch] for batch in coordinator.processed] == [["first"], ["second"]]
    assert manager.size == 0
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_non_due_enqueue_during_delivery_is_scheduled_after_worker_finishes() -> None:
    coordinator = _Coordinator()
    coordinator.release.clear()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("first"), summary_window_seconds=0)
    await asyncio.wait_for(coordinator.started.wait(), timeout=1)
    await manager.async_enqueue(_context("later"), summary_window_seconds=3600)
    coordinator.release.set()
    await _wait_for_worker(coordinator)

    assert manager.size == 1
    assert manager._flush_timer is not None
    assert not manager._flush_timer.cancelled()
    await manager.async_shutdown()
    assert manager.size == 0


@pytest.mark.asyncio
async def test_due_group_keeps_compatible_later_arrivals_in_one_summary_batch() -> None:
    coordinator = _Coordinator()
    manager = NotificationQueueManager(coordinator)
    first = _context("first", group="chores", users=["alice", "bob"], channels=["push", "dashboard"])
    second = replace(first, notification_id="second", users=["bob", "alice"], channels=["dashboard", "push"])
    await manager.async_enqueue(first, summary_window_seconds=0)
    await manager.async_enqueue(second, summary_window_seconds=60)
    await _wait_for_worker(coordinator)

    assert coordinator.processed == [[first, second]]
    assert manager.size == 0
    await manager.async_shutdown()


@pytest.mark.parametrize(
    "changed",
    [
        {"flow": "another_flow"},
        {"users": ["bob"]},
        {"user": "bob"},
        {"room": "kitchen"},
        {"device": "speaker"},
        {"channels": ["voice"]},
        {"summarize": False},
        {"rewrite": False},
        {"immediately": True},
        {"force": True},
        {"include_actions": True},
        {"personality": "brief"},
        {"character": "another"},
        {"metadata": {"notification_policy": {"delivery_mode": "push_only"}}},
        {"metadata": {"notification_policy": {"users": ["person.alice"]}}},
        {"metadata": {"notification_policy": {"target_room": "kitchen"}}},
        {"metadata": {"notification_policy": {"presence": "someone_home"}}},
        {"metadata": {"notification_policy": {"quiet_hours": "text_only"}}},
        {"metadata": {"bypass_channel_policy": True}},
        {"metadata": {"channels_explicit": True}},
        {"metadata": {"audience_explicit": True}},
        {"metadata": {"audience_resolved": True}},
        {"metadata": {"mobile_options": {"target": "alice"}}},
        {"metadata": {"tts_options": {"voice": "different"}}},
    ],
)
@pytest.mark.asyncio
async def test_batches_preserve_recipient_routing_and_ai_boundaries(changed) -> None:
    coordinator = _Coordinator()
    manager = NotificationQueueManager(coordinator)
    first = _context("first", group="shared", users=["alice"], channels=["push"])
    second = replace(first, notification_id="second", **changed)
    await manager.async_enqueue(first, summary_window_seconds=60)
    await manager.async_enqueue(second, summary_window_seconds=60)
    await manager.async_flush_now()

    assert coordinator.processed == [[first], [second]]
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_equivalent_policies_can_summarize_different_registry_events() -> None:
    coordinator = _Coordinator()
    manager = NotificationQueueManager(coordinator)
    first = _context(
        "first",
        metadata={"notification_policy": {"notification_key": "washer", "delivery_mode": "push_only", "notes": "one"}},
    )
    second = replace(first, notification_id="second", metadata={
        "notification_policy": {"notification_key": "dryer", "delivery_mode": "push_only", "notes": "two"}
    })
    await manager.async_enqueue(first, summary_window_seconds=60)
    await manager.async_enqueue(second, summary_window_seconds=60)
    await manager.async_flush_now()

    assert coordinator.processed == [[first, second]]
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_concurrent_manual_flush_and_shutdown_do_not_cancel_active_delivery() -> None:
    coordinator = _Coordinator()
    coordinator.release.clear()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("first"), summary_window_seconds=0)
    await asyncio.wait_for(coordinator.started.wait(), timeout=1)
    await manager.async_enqueue(_context("second"), summary_window_seconds=3600)
    flush = asyncio.create_task(manager.async_flush_now())
    shutdown = asyncio.create_task(manager.async_shutdown())
    coordinator.release.set()
    await asyncio.wait_for(asyncio.gather(flush, shutdown), timeout=1)

    assert not coordinator.cancelled
    assert [[item.notification_id for item in batch] for batch in coordinator.processed] == [["first"], ["second"]]
    assert manager.size == 0
    assert manager._flush_timer is None
    with pytest.raises(RuntimeError, match="shut down"):
        await manager.async_enqueue(_context("late"), summary_window_seconds=0)


@pytest.mark.asyncio
async def test_cancelled_flush_caller_does_not_cancel_or_lose_delivery() -> None:
    coordinator = _Coordinator()
    coordinator.release.clear()
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("first"), summary_window_seconds=3600)
    flush = asyncio.create_task(manager.async_flush_now())
    await asyncio.wait_for(coordinator.started.wait(), timeout=1)
    flush.cancel()
    with pytest.raises(asyncio.CancelledError):
        await flush

    assert not coordinator.cancelled
    assert manager.size == 1
    coordinator.release.set()
    await _wait_for_worker(coordinator)
    assert manager.size == 0
    assert len(coordinator.processed) == 1
    await manager.async_shutdown()


@pytest.mark.asyncio
async def test_failed_batch_remains_pending_and_other_groups_still_deliver() -> None:
    coordinator = _Coordinator()
    coordinator.failure = "failed"
    manager = NotificationQueueManager(coordinator)
    await manager.async_enqueue(_context("failed", group="first"), summary_window_seconds=3600)
    await manager.async_enqueue(_context("good", group="second"), summary_window_seconds=3600)

    with pytest.raises(RuntimeError, match="delivery failed"):
        await manager.async_flush_now()

    assert [[item.notification_id for item in batch] for batch in coordinator.processed] == [["good"]]
    assert manager.size == 1
    assert coordinator.snapshots[-1][0]["notification_id"] == "failed"
    assert manager._flush_timer is not None
    assert manager._flush_timer.when() > asyncio.get_running_loop().time()
    coordinator.failure = None
    await manager.async_shutdown()
    assert [[item.notification_id for item in batch] for batch in coordinator.processed] == [["good"], ["failed"]]
    assert manager.size == 0
