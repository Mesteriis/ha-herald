# API

## Primary service

### `herald.notify`

Thin request fields:

- `event`
- `message`
- `level`
- `ai`
- `context`
- `entities`
- `suppress`
- `group`
- `immediately`

Example:

```yaml
service: herald.notify
data:
  event: door_left_open
  message: Balcony door has been open for 10 minutes
  level: warning
  entities:
    - binary_sensor.balcony_door
  context:
    area: balcony
```

## Other services

- `herald.generate_dashboard`
- `herald.set_flow_state`
- `herald.trace_snapshot`
- `herald.acknowledge`
- `herald.snooze_flow`
