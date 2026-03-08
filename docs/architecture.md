# Architecture

## Pipeline

```text
automation -> herald.notify -> context builder -> AI rewrite -> router -> queue -> channels
```

## Core modules

- `__init__.py`: YAML import, config entry setup, frontend static path registration
- `config_flow.py`: UI configuration and options
- `coordinator.py`: runtime state, queue orchestration, traces, actionable callback handling
- `router.py`: channel selection, presence-aware delivery, quiet-hours policies, mobile/Telegram action feedback
- `ai.py`: Ollama rewrite and summary client
- `presence.py`: people-home, room, mode, quiet-hours snapshot
- `flows.py`: flow condition evaluation and severity logic
- `sensor.py`: status, metrics, and diagnostic sensors
- `diagnostics.py`: redacted runtime diagnostics
- `frontend/herald-card.ts`: Lovelace UI

## Runtime state

Persistent state is stored with Home Assistant `Store` and tracks:

- notifications today
- last notification
- recent notifications
- flow overrides
- snoozed flows
- acknowledged notifications
- mobile push clears
- trace history

## Entities

- `sensor.herald_status`: compact runtime status (`ready`, `busy`, `quiet_hours`, `away`)
- `sensor.herald_notifications_today`: daily delivery counter with recent notification attributes
- `sensor.herald_last_notification`: latest delivery title plus full payload attributes
- `sensor.herald_queue_size`: live queue depth and routing diagnostics

## Action feedback loops

- Mobile push actions acknowledge/snooze notifications and clear the originating push tag.
- Telegram callbacks return localized confirmation text through `answer_callback_query`.
