# Dashboard

Herald serves its card locally at `/herald/herald-card.js`.

## Lovelace resource

Add a module resource:

```yaml
url: /herald/herald-card.js
type: module
```

## Card example

```yaml
type: custom:herald-card
title: Herald Notification Center
today_entity: sensor.herald_notifications_today
last_entity: sensor.herald_last_notification
queue_entity: sensor.herald_queue_size
language_entities:
  - input_select.herald_language_alex
  - input_select.herald_language_wife
```

## Auto dashboard

The service `herald.generate_dashboard` writes a starter dashboard YAML file. The resulting dashboard shows:

- statistics
- queue size
- recent notifications
- per-flow toggles
- language selectors

## Presets

Use the `preset` field to generate different starter layouts:

- `overview`: single-pane operational summary
- `rooms`: adds room occupancy tiles from configured room sensors
- `roles`: adds per-user sections with language helpers and core Herald entities
