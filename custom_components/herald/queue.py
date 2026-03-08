"""Notification queue and batching logic for Herald."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from .const import DEFAULT_SUMMARY_WINDOW_SECONDS
from .models import NotificationContext

if TYPE_CHECKING:
    from .coordinator import HeraldCoordinator


@dataclass(slots=True)
class QueuedNotification:
    """A queued notification awaiting dispatch."""

    context: NotificationContext
    enqueued_at: datetime
    summary_window_seconds: int = DEFAULT_SUMMARY_WINDOW_SECONDS


class NotificationQueueManager:
    """Queue manager that batches events and triggers summary dispatches."""

    def __init__(self, coordinator: "HeraldCoordinator") -> None:
        self._coordinator = coordinator
        self._items: list[QueuedNotification] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None

    @property
    def size(self) -> int:
        """Return the current queue size."""
        return len(self._items)

    async def async_enqueue(self, item: NotificationContext, *, summary_window_seconds: int) -> None:
        """Append a notification and schedule a flush if needed."""
        async with self._lock:
            self._items.append(
                QueuedNotification(
                    context=item,
                    enqueued_at=datetime.now(),
                    summary_window_seconds=max(0, summary_window_seconds),
                )
            )
            self._coordinator.async_set_queue_size(len(self._items))
            if self._flush_task is None or self._flush_task.done():
                delay = max(
                    0,
                    min(
                        queued.summary_window_seconds
                        for queued in self._items
                    ),
                )
                self._flush_task = self._coordinator.hass.async_create_task(
                    self._async_delayed_flush(delay)
                )

    async def async_flush_now(self) -> None:
        """Flush the queue immediately."""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
        await self._async_flush()

    async def _async_delayed_flush(self, delay: int) -> None:
        """Flush the queue after the debounce window."""
        if delay:
            await asyncio.sleep(delay)
        await self._async_flush()

    async def _async_flush(self) -> None:
        """Flush queued items to the coordinator grouped by flow and channel set."""
        async with self._lock:
            items = list(self._items)
            self._items.clear()
            self._coordinator.async_set_queue_size(0)

        groups: dict[tuple[str, tuple[str, ...]], list[NotificationContext]] = defaultdict(list)
        for item in items:
            group_key = (item.context.flow, tuple(sorted(item.context.channels)))
            groups[group_key].append(item.context)

        for notifications in groups.values():
            await self._coordinator.async_process_notifications(notifications)
