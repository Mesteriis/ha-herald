# Herald AI Notification Center

Herald is a custom Home Assistant integration for notification routing, policies,
queueing, optional AI rewriting, and dashboard controls. Automations call
`herald.notify`; Herald resolves delivery using configured channels, presence,
room information, and runtime controls.

```text
Automation / Script -> Context and policies -> Queue -> Router -> HA services
                                                  -> optional AI
```

## Supported behavior

- Semantic requests and legacy explicit user, room, and channel fields.
- Per-notification delivery policies, severity and channel controls, mute and maintenance modes.
- In-memory delay, compatible batching, deduplication, and optional summaries.
- Existing HA services for mobile notifications, Telegram, TTS, TV, persistent notifications,
  logbook and system log; a dashboard feed and optional Hume TTS adapter.
- Ollama or OpenAI-compatible rewriting/summaries and file-backed character templates.
- Integration-owned switches, selects, numbers, buttons and sensors.
- A bundled Lit frontend with policy editing, queue, flow, user and room cards.

This is a local integration, not a durable message broker. Pending queue entries
are not persisted across restart. Delivery receipts and exactly-once delivery are
not guaranteed. Device discovery uses HA services, registries and device links; review discovered
channels and configure explicit targets when ownership or room mapping is ambiguous.
AI, Hume and external transports require their own working services/configuration.

## Example

```yaml
service: herald.notify
data:
  event: washing_cycle_finished
  message: Washer cycle completed
  level: info
  entities:
    - sensor.washer_state
  suppress: 120
  group: laundry
  immediately: false
```

## Full dashboard

Herald includes a full-page `custom:ha-herald-dashboard` with six tabs, live event
details, rule editing, delivery controls and diagnostics. Its artwork ships with
the integration. See [dashboard setup](docs/dashboard.md#full-herald-dashboard).

## Installation

The repository declares Home Assistant 2026.3.0 as its minimum in `hacs.json`;
compatibility with your HA version and configured transports still requires a
local acceptance check.

### HACS custom repository

1. Add `https://github.com/Mesteriis/ha-herald` as a custom repository of type `Integration`.
2. Install Herald and restart Home Assistant.
3. Add Herald from Settings → Devices & Services and review its settings.
4. Verify the generated entities/dashboard and test only the channels you intend to use.

These steps describe a custom-repository installation; listing in the default
HACS catalog is not implied.

### Manual

Copy the **`custom_components/herald/` directory**, including its bundled `frontend/`
assets, into `<HA config>/custom_components/herald/`. Do not copy the repository
root into that directory. Restart Home Assistant and add the integration.

Released/check-in frontend assets need no Node.js on the HA host. Developers edit
`frontend/herald-card.js`, run `npm ci && npm run build`, and commit both generated
assets. See [Contributing](CONTRIBUTING.md) for validation.

## Documentation

- [Architecture and boundaries](docs/architecture.md)
- [Runtime pipeline](docs/system.md)
- [Guided integration settings](docs/options.md)
- [Controls](docs/controls.md) and [flows](docs/flows.md)
- [AI characters and rewriting](docs/characters.md)
- [Настройка правил и проверка без отправки](docs/rule_editor.md)
- [Общая доставка и настройка каналов](docs/channel_setup.md)
- [Services](docs/api.md) and [dashboard](docs/dashboard.md)
- [Release validation](docs/release.md) and [known follow-up work](TODO.md)
- [Changelog](CHANGELOG.md)
