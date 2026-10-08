# Runtime system

## Pipeline

```text
HA automation / script / service
  -> herald.notify
  -> parse request and resolve flow
  -> context and presence snapshot
  -> policy overrides and admission controls
  -> queue: deduplication, delay, compatible grouping
  -> optional summary
  -> router: recipients, channels, device availability
  -> optional AI rewrite/translation
  -> HA delivery services or Hume TTS
  -> trace, dashboard feed and counters
```

`ai_decision` in the trace records eligibility for AI. It is not a separate LLM
that classifies severity. AI generation is optional; configured static text is the
fallback when rewriting is disabled or generation fails.

The queue is in memory. Delay and summary windows do not imply persistence or
transport retries. The router records delivery outcomes from HA service calls;
those outcomes do not prove that a person read or heard a message.

## Runtime entities

Default entity names include:

- `sensor.herald_notification_center_status`
- `sensor.herald_notification_center_notifications_today`
- `sensor.herald_notification_center_deliveries_today`
- `sensor.herald_notification_center_dropped_today`
- `sensor.herald_notification_center_errors_today`
- `sensor.herald_notification_center_ai_requests_today`
- `sensor.herald_notification_center_last_notification`
- `sensor.herald_notification_center_queue_size`

Entity registry customizations may change entity IDs. Use the actual IDs shown in
Home Assistant when constructing a custom dashboard.

Herald exposes maintenance, mute, sidebar, AI/severity, channel-family, user,
room, channel and flow controls as integration-owned entities. Some explicit
control-plane actions have their own audible feedback behavior; assess those
separately from ordinary notification routing during acceptance tests.
