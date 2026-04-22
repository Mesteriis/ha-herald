# System

## Pipeline

```text
automation/script/service
  -> herald.notify
  -> flow resolution
  -> context + presence snapshot
  -> AI decision
  -> AI rewrite
  -> router
  -> queue
  -> delivery
  -> diagnostics + analytics
```

## Core runtime entities

- `sensor.herald_notification_center_status`
- `sensor.herald_notification_center_notifications_today`
- `sensor.herald_notification_center_deliveries_today`
- `sensor.herald_notification_center_dropped_today`
- `sensor.herald_notification_center_errors_today`
- `sensor.herald_notification_center_ai_requests_today`
- `sensor.herald_notification_center_last_notification`
- `sensor.herald_notification_center_queue_size`

## Control plane

Herald creates integration-owned runtime entities for:

- maintenance mode
- mute all
- sidebar visibility
- AI and severity toggles
- channel family toggles
- per-user language, character, and silence
- per-room fallback presence
- per-room notification device selection
- per-channel and per-flow controls
