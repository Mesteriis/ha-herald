"""Tests for Herald queue diagnostics."""

from __future__ import annotations

import asyncio

from custom_components.herald.models import NotificationContext
from custom_components.herald.queue import NotificationQueueManager


class _FakeHass:
    def async_create_task(self, coro):
        return asyncio.create_task(coro)


class _FakeCoordinator:
    def __init__(self) -> None:
        self.hass = _FakeHass()
        self.queue_snapshots: list[list[dict[str, object]]] = []
        self.processed: list[list[NotificationContext]] = []

    def async_set_queue_state(self, items: list[dict[str, object]]) -> None:
        self.queue_snapshots.append(items)

    async def async_process_notifications(self, notifications: list[NotificationContext]) -> None:
        self.processed.append(notifications)


def test_queue_manager_exposes_serialized_queue_items() -> None:
    async def _exercise() -> None:
        coordinator = _FakeCoordinator()
        manager = NotificationQueueManager(coordinator)
        context = NotificationContext(
            flow="system_events",
            event="washer_done",
            title="Laundry",
            message="Cycle finished",
            level="info",
            source="automation.laundry",
            timestamp="2026-03-08T11:00:00+00:00",
            notification_id="queue_1",
            channels=["dashboard_default", "persistent_default"],
            users=["person.aleksandr_meshcheriakov"],
            room="bathroom",
            group="chores",
        )

        await manager.async_enqueue(context, summary_window_seconds=60)

        assert coordinator.queue_snapshots
        assert coordinator.queue_snapshots[-1][0]["event"] == "washer_done"
        assert coordinator.queue_snapshots[-1][0]["channels"] == [
            "dashboard_default",
            "persistent_default",
        ]
        assert coordinator.queue_snapshots[-1][0]["group"] == "chores"
        assert coordinator.queue_snapshots[-1][0]["summary_window_seconds"] == 60

        await manager.async_flush_now()

        assert coordinator.queue_snapshots[-1] == []
        assert len(coordinator.processed) == 1
        assert coordinator.processed[0][0].notification_id == "queue_1"

    asyncio.run(_exercise())
