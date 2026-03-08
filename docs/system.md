# System Description

## Overview

Herald is an AI-assisted notification control plane for Home Assistant. It receives a
single normalized service call, enriches it with home context, applies flow rules,
optionally rewrites or summarizes the text through Ollama, and then routes the result
to the best delivery channels for the active situation.

## Pipeline

```text
automation/script/service
  -> herald.notify
  -> flow resolution
  -> context + presence snapshot
  -> AI rewrite / AI summary
  -> router
  -> delivery channels
  -> runtime trace + sensors
```

## Core entities

- `sensor.herald_status`
  State: `ready`, `busy`, `quiet_hours`, `away`
  Purpose: compact health and operating-mode signal for dashboards/diagnostics.

- `sensor.herald_notifications_today`
  State: daily delivery count
  Attributes: recent notifications, flow states.

- `sensor.herald_last_notification`
  State: title of the latest delivered notification
  Attributes: message, flow, level, channels, grouped count, results, acknowledgement state.

- `sensor.herald_queue_size`
  State: queued notification count
  Attributes: quiet hours, home mode, people home, flow states, snoozed flows, acknowledgement count.

## Flow model

Built-in flows:

- `security_alerts`
- `system_events`
- `device_alerts`
- `ai_events`
- `energy_events`
- `camera_alerts`
- `timer_notifications`

Each flow supports:

- `enabled`
- `severity`
- `channels`
- `conditions`
- `personality`
- `summary_personality`
- `allow_summary`
- `summary_window_seconds`

## Presence and routing

Routing decisions can use:

- household presence
- quiet hours
- active room sensors
- configured away-only channels
- per-user preferred channels
- per-channel quiet-hours policy overrides

Supported built-in channel types:

- `tts`
- `mobile_app`
- `telegram`
- `persistent_notification`
- `logbook`
- `system_log`

## Action loops

Herald supports acknowledgement and snooze loops across multiple surfaces:

- Mobile app action buttons
- Telegram inline keyboard callbacks
- Direct service calls

Feedback behavior:

- acknowledged or snoozed push notifications clear the original mobile notification tag
- Telegram users receive localized callback confirmation text

## Dashboard presets

The `herald.generate_dashboard` service can render three starter layouts:

- `overview`
- `rooms`
- `roles`

## Distribution

The publishable HACS repository is exported under `distrib/herald/` with a standard
`custom_components/herald` layout, HACS metadata, docs, tests, brand assets, and CI
workflows for release automation.
