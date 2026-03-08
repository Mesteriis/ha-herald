# Herald AI Notification Center

Herald is a production-ready Home Assistant notification control plane for HACS.
It sits between automations and users and decides how notifications should be enriched,
routed, aggregated, spoken, and delivered.

```text
Automation / Script -> Herald -> User / Device / Voice
```

## What Herald does

- accepts semantic events through `herald.notify`
- resolves presence, room, recipients, language, and character from Home Assistant
- routes through push, voice, Telegram, dashboard, persistent, TV, and system channels
- supports queueing, deduplication, delay, summaries, and runtime diagnostics
- exposes Herald-owned runtime controls directly on the integration page
- speaks its own control-plane actions when someone is home
- selects the best room output device with fallback `Alice -> HomePod -> TV`

## Thin request example

```yaml
service: herald.notify
data:
  event: washing_cycle_finished
  message: Washer cycle completed
  level: info
  ai:
    character: domovoy
    context:
      mode: brief
  context:
    appliance: washer
  entities:
    - sensor.washer_state
  suppress: 120
  group: laundry
  immediately: false
```

## Installation

### HACS

1. Add `https://github.com/Mesteriis/ha-herald` as a custom repository of type `Integration`.
2. Install `Herald AI Notification Center`.
3. Restart Home Assistant.
4. Add the integration in Settings -> Devices & Services.

### Manual

Copy this repository into `config/custom_components/herald/` and restart Home Assistant.

## Runtime controls

Herald creates runtime entities for:

- AI enablement and AI per severity
- severity enablement
- maintenance mode and maintenance minimum level
- mute all
- dashboard sidebar visibility
- channel family toggles
- per-user language, character, and silent mode
- per-room fallback presence and room notification output device
- per-channel enablement, minimum level, and test buttons
- per-flow enablement, summary window, dedup window, cooldown, and test buttons

## Key docs

- [Architecture](docs/architecture.md)
- [System](docs/system.md)
- [Controls](docs/controls.md)
- [API](docs/api.md)
- [Dashboard](docs/dashboard.md)
- [Release](docs/release.md)
- [HACS migration](docs/hacs_migration.md)
- [Changelog](CHANGELOG.md)

## Maintainer

Aleksandr Meshchryakov <avm@sh-inc.ru>
