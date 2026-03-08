# Herald Notification Center

`herald` is a production-oriented Home Assistant notification framework for HACS.
It centralizes notification routing, AI rewriting, per-user language selection,
queueing, summaries, quiet hours, presence-aware delivery, and actionable flows.

## Features

- `herald.notify` as the central service API
- Presence-aware routing for TTS, push, Telegram, persistent notifications, logbook, and system log
- Flow model with `security_alerts`, `system_events`, `device_alerts`, `ai_events`, `energy_events`, `camera_alerts`, `timer_notifications`
- Quiet hours with critical/security bypass and per-channel override policies
- AI rewrite and summary pipeline via Ollama
- Per-user language routing through helpers such as `input_select.herald_language_alex`
- Queueing and summarization of simultaneous events
- Actionable notifications with acknowledge and snooze actions for mobile and Telegram
- Feedback loops for mobile push clears and localized Telegram callback acknowledgements
- Diagnostics, trace snapshots, status sensor, and auto-generated dashboard YAML presets
- Local bundled Lovelace card served by the integration itself at `/herald/herald-card.js`
- Semantic-release automation via `release-please`

## Installation

### HACS

1. Add `https://github.com/Mesteriis/ha-herald` as a custom repository of type `Integration`.
2. Install `Herald Notification Center`.
3. Restart Home Assistant.
4. Add the Lovelace resource `/herald/herald-card.js` as a module resource.

### Manual

Copy this repository into `config/custom_components/herald/` and restart Home Assistant.

## Minimal configuration

```yaml
herald:
  ollama:
    enabled: true
    host: http://ollama.local:11434
    model: llama3
  quiet_hours:
    start: "23:00"
    end: "08:00"
  channels:
    kitchen_tts:
      type: tts
      service: tts.yandex_station_say
      entity_id: media_player.kitchen_homepod
      room: kitchen
      quiet_hours_policy: block
    alex_phone:
      type: mobile_app
      service: notify.mobile_app_alex_phone
      user: alex
      quiet_hours_policy: allow
    family_telegram:
      type: telegram
      chat_id: -1001234567890
    persistent_default:
      type: persistent_notification
    system_log_default:
      type: system_log
  users:
    alex:
      name: Alex
      language_helper: input_select.herald_language_alex
      preferred_channels:
        - alex_phone
    wife:
      name: Wife
      language_helper: input_select.herald_language_wife
      preferred_channels:
        - family_telegram
  flows:
    security_alerts:
      enabled: true
      severity: security
      channels:
        - family_telegram
        - kitchen_tts
      summary_personality: Jarvis
    energy_events:
      enabled: true
      severity: warning
      channels:
        - alex_phone
```

## Service API

### `herald.notify`

```yaml
service: herald.notify
data:
  flow: timer_notifications
  level: warning
  title: Таймер
  message: До выключения осталось 15 минут
  source: automation.timer
  automation_id: timer_kitchen_shutdown
  room: kitchen
  include_actions: true
```

### `herald.acknowledge`

```yaml
service: herald.acknowledge
data:
  notification_id: timer_notifications_20260308120000_1234abcd
  actor: alex
```

### `herald.snooze_flow`

```yaml
service: herald.snooze_flow
data:
  flow: timer_notifications
  notification_id: timer_notifications_20260308120000_1234abcd
  minutes: 30
  actor: alex
```

## Migration from scripts

Current YAML automations that call `script.voice_notify_router` or `script.system_notify`
should be migrated to `herald.notify`.

Example:

```yaml
service: herald.notify
data:
  flow: device_alerts
  level: info
  title: Стиральная машина
  message: Стирка закончилась
  source: automation.washer_cycle_finished_notify
  device: washer
  room: bathroom
  include_actions: true
```

## Dashboard

Use `herald.generate_dashboard` to create a starter dashboard YAML file.

```yaml
service: herald.generate_dashboard
data:
  path: dashboards/herald_dashboard.yaml
  title: Herald Dashboard
  preset: rooms
```

## Development

- Python: 3.11
- Frontend: TypeScript + Lit + esbuild
- Tests: `pytest`
- Build frontend: `npm install && npm run build`
- Run tests: `pytest -q`

## Documentation

- [Architecture](docs/architecture.md)
- [System Description](docs/system.md)
- [Publish Checklist](docs/publish_checklist.md)
- [HACS Migration](docs/hacs_migration.md)
- [Flows](docs/flows.md)
- [API](docs/api.md)
- [Dashboard](docs/dashboard.md)
- [Contributing](CONTRIBUTING.md)
