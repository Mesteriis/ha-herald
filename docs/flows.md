# Flows

Herald separates notification traffic into named flows.

## Built-in flows

- `security_alerts`
- `system_events`
- `device_alerts`
- `ai_events`
- `energy_events`
- `camera_alerts`
- `timer_notifications`

## Flow fields

- `enabled`
- `severity`
- `channels`
- `conditions`
- `personality`
- `summary_personality`
- `allow_summary`
- `summary_window_seconds`

## Example

```yaml
herald:
  flows:
    security_alerts:
      enabled: true
      severity: security
      channels:
        - family_telegram
        - hallway_tts
      conditions:
        presence: someone_home
```

## Runtime control

Use `herald.set_flow_state` for hard enable/disable and `herald.snooze_flow` for temporary muting.

## Summary personality override

Each flow can override the AI personality used for queue summaries without changing the
personality used for single-notification rewrites:

```yaml
herald:
  flows:
    system_events:
      personality: HESTIA
      summary_personality: Jarvis
```
