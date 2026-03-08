# API

## Services

### `herald.notify`

Fields:

- `flow`
- `level`
- `title`
- `message`
- `source`
- `automation_id`
- `device`
- `room`
- `user`
- `users`
- `channels`
- `personality`
- `metadata`
- `notification_id`
- `include_actions`
- `rewrite`
- `summarize`
- `force`

### `herald.acknowledge`

Acknowledge a notification by `notification_id`.

### `herald.snooze_flow`

Temporarily mute a flow for `minutes`.

Fields:

- `flow`
- `minutes`
- `notification_id`
- `actor`
- `source`

### `herald.generate_dashboard`

Generate a YAML dashboard definition.

Fields:

- `path`
- `title`
- `preset` (`overview`, `rooms`, `roles`)

### `herald.trace_snapshot`

Return runtime traces, recent notifications, acknowledged notifications, and snoozed flows.

## Events handled

- `mobile_app_notification_action`
- `mobile_app_notification_cleared`
- `telegram_callback`

## Entities

- `sensor.herald_status`
- `sensor.herald_notifications_today`
- `sensor.herald_last_notification`
- `sensor.herald_queue_size`
