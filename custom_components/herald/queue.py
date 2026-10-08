"""Notification queue and batching logic for Herald."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from traceback import extract_tb
from typing import TYPE_CHECKING

from .const import DEFAULT_SUMMARY_WINDOW_SECONDS
from .models import NotificationContext

if TYPE_CHECKING:
    from .coordinator import HeraldCoordinator

_RETRY_DELAY_SECONDS = 30


def _group_key(context: NotificationContext) -> tuple[object, ...]:
    """Keep batching inside the same recipient, routing and AI boundaries."""
    metadata = {
        key: context.metadata.get(key)
        for key in (
            "bypass_channel_policy",
            "control_test_channel",
            "maintenance_tray_debug",
            "legacy_target_group",
            "mobile_options",
            "tts_options",
            "channels_explicit",
            "audience_explicit",
            "audience_resolved",
        )
    }
    policy = context.metadata.get("notification_policy") or {}
    # Registry identity and UI notes do not change delivery and must not prevent
    # summaries of different events governed by the same effective policy.
    metadata["notification_policy"] = {
        key: value
        for key, value in policy.items()
        if key not in {"notification_key", "notes", "updated_at"}
    }
    return (
        context.flow,
        context.group or context.flow or context.event,
        context.user,
        tuple(sorted(set(context.users))),
        context.room,
        context.device,
        tuple(sorted(set(context.channels))),
        context.summarize,
        context.rewrite,
        context.immediately,
        context.force,
        context.include_actions,
        context.character,
        context.personality,
        json.dumps(metadata, sort_keys=True, default=str),
    )


@dataclass(slots=True)
class QueuedNotification:
    """A queued notification awaiting dispatch."""

    context: NotificationContext
    enqueued_at: datetime
    summary_window_seconds: int = DEFAULT_SUMMARY_WINDOW_SECONDS
    due_at: float = 0.0

    def as_dict(self) -> dict[str, object]:
        """Serialize the queued notification for diagnostics and UI."""
        return {
            "flow": self.context.flow,
            "event": self.context.event,
            "title": self.context.title,
            "message": self.context.message,
            "level": self.context.level,
            "notification_id": self.context.notification_id,
            "group": self.context.group,
            "channels": list(self.context.channels),
            "room": self.context.room,
            "users": list(self.context.users),
            "timestamp": self.context.timestamp,
            "enqueued_at": self.enqueued_at.isoformat(),
            "summary_window_seconds": self.summary_window_seconds,
        }


class NotificationQueueManager:
    """Queue manager that batches events and triggers summary dispatches."""

    def __init__(self, coordinator: "HeraldCoordinator") -> None:
        self._coordinator = coordinator
        self._items: list[QueuedNotification] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task[None] | None = None
        self._flush_timer: asyncio.TimerHandle | None = None
        self._closed = False
        self._last_failure: dict[str, object] | None = None

    @property
    def size(self) -> int:
        """Return the current queue size."""
        return len(self._items)

    def diagnostic_snapshot(self) -> dict[str, object]:
        """Expose the active await path without message bodies or task locals."""
        task = self._flush_task
        timer_due_in = (
            max(0, round(self._flush_timer.when() - asyncio.get_running_loop().time(), 1))
            if self._flush_timer is not None else None
        )
        if task is None:
            return {"worker_active": False, "await_path": [], "timer_due_in": timer_due_in,
                    "last_failure": self._last_failure}
        await_path: list[str] = []
        current: object | None = task.get_coro()
        for _ in range(12):
            if current is None:
                break
            frame = getattr(current, "cr_frame", None) or getattr(current, "gi_frame", None)
            if frame is not None:
                await_path.append(f"{frame.f_code.co_name}:{frame.f_lineno}")
            current = getattr(current, "cr_await", None) or getattr(current, "gi_yieldfrom", None)
        return {"worker_active": not task.done(), "await_path": await_path,
                "timer_due_in": timer_due_in, "last_failure": self._last_failure}

    def _snapshot(self) -> list[dict[str, object]]:
        """Return a serializable snapshot of the current queue."""
        return [item.as_dict() for item in self._items]

    async def async_enqueue(self, item: NotificationContext, *, summary_window_seconds: int) -> None:
        """Append a notification and schedule a flush if needed."""
        async with self._lock:
            if self._closed:
                raise RuntimeError("The Herald notification queue is shut down")
            window = max(0, summary_window_seconds)
            self._items.append(
                QueuedNotification(
                    context=item,
                    enqueued_at=datetime.now(),
                    summary_window_seconds=window,
                    due_at=asyncio.get_running_loop().time() + window,
                )
            )
            self._coordinator.async_set_queue_state(self._snapshot())
            self._schedule_flush()

    async def async_flush_now(self) -> None:
        """Make pending groups due and wait without cancelling any delivery."""
        async with self._lock:
            now = asyncio.get_running_loop().time()
            for item in self._items:
                item.due_at = now
            self._cancel_timer()
            task = self._start_flush()
        if task is not None:
            # Cancelling a service caller must not cancel an in-flight send.
            await asyncio.shield(task)

    async def async_shutdown(self) -> None:
        """Stop accepting notifications and finish all pending deliveries."""
        async with self._lock:
            self._closed = True
            self._cancel_timer()
        await self.async_flush_now()

    def _cancel_timer(self) -> None:
        """Cancel only the waiting timer, never the delivery task."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()
            self._flush_timer = None

    def _start_flush(self) -> asyncio.Task[None] | None:
        """Start a single delivery worker on the event-loop thread."""
        self._flush_timer = None
        if self._flush_task is None and self._items:
            task = self._coordinator.hass.async_create_task(self._async_flush())
            if task.done():
                # Home Assistant may start tasks eagerly. A timer callback can
                # also run just before the deadline, leaving no due group yet.
                # Never retain a completed worker or strand its pending items.
                self._flush_task = None
                self._schedule_flush()
            else:
                self._flush_task = task
        return self._flush_task

    def _schedule_flush(self) -> None:
        """Always schedule from the earliest remaining monotonic deadline."""
        self._cancel_timer()
        if self._closed or not self._items or self._flush_task is not None:
            return
        self._flush_timer = asyncio.get_running_loop().call_at(
            min(item.due_at for item in self._items), self._start_flush
        )

    def _next_due_group(self) -> list[QueuedNotification]:
        """Close only a due group, including its later compatible arrivals."""
        groups: dict[tuple[object, ...], list[QueuedNotification]] = defaultdict(list)
        for item in self._items:
            groups[_group_key(item.context)].append(item)
        now = asyncio.get_running_loop().time()
        for group in groups.values():
            if min(item.due_at for item in group) <= now:
                return group
        return []

    async def _async_flush(self) -> None:
        """Deliver due groups, retaining each batch until processing succeeds."""
        first_error: Exception | None = None
        try:
            while True:
                async with self._lock:
                    items = self._next_due_group()
                if not items:
                    break
                try:
                    await self._coordinator.async_process_notifications([item.context for item in items])
                except Exception as err:  # noqa: BLE001
                    # Keep the failed batch visible and retry later. Other due
                    # groups still run, and explicit flush callers see the error.
                    first_error = first_error or err
                    last_frame = extract_tb(err.__traceback__)[-1]
                    self._last_failure = {
                        "type": type(err).__name__,
                        "location": f"{Path(last_frame.filename).name}:{last_frame.lineno}",
                    }
                    async with self._lock:
                        retry_at = asyncio.get_running_loop().time() + _RETRY_DELAY_SECONDS
                        for item in items:
                            item.due_at = retry_at
                else:
                    async with self._lock:
                        completed = {id(item) for item in items}
                        self._items = [item for item in self._items if id(item) not in completed]
                        self._coordinator.async_set_queue_state(self._snapshot())
            if first_error is not None:
                raise first_error
        finally:
            async with self._lock:
                self._flush_task = None
                self._schedule_flush()
