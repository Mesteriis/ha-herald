# Dashboard and frontend

Herald serves its bundled card module at `/herald/herald-card.js` and attempts to
register a `herald-control-center` dashboard in storage-mode Lovelace. Resource
registration retries while Lovelace is starting. A detected dedicated YAML dashboard
takes precedence over creation of a generated storage dashboard.

Herald creates a starter storage dashboard only when there is no existing runtime
dashboard, persisted registry entry or occupied panel path. Existing layouts are
preserved on registration/reload, including when a YAML Herald dashboard exists.
With global YAML Lovelace mode the extra JS loader exposes the cards; automatic
storage dashboard/resource creation is skipped. Startup retries are cancelled on unload.

## Full Herald dashboard

`custom:ha-herald-dashboard` provides a full-page dashboard with Overview, Rules,
Delivery, Analytics, Controls and Diagnostics tabs. Its artwork and frontend are
included in the Herald integration package; no external card repository is needed.
The overview shows the latest event, a recent-event list, daily counters, queue
size and quick controls. Events open in a keyboard-accessible dialog; a rule link
appears only when the recorded event identifies one unique rule.

Use the card in a Lovelace **panel** view:

```yaml
views:
  - title: Herald
    path: herald
    type: panel
    cards:
      - type: custom:ha-herald-dashboard
        home_path: /lovelace-main/home
```

`home_path` is optional and defaults to `/`; only a local absolute path is accepted.
Set `fullscreen: true` when the surrounding HA header is hidden (for example by
kiosk mode). This uses the full viewport height instead of reserving the normal
HA header space; it does not change the user's HA navigation preferences.
The inherited `status_entity`, `today_entity`, `queue_entity` and `entry_id` options
can scope the dashboard to a particular Herald entry or renamed sensor. Controls
use exact IDs resolved from the entity registry and stay disabled until HA reports
available state. Pending edits wait for HA acknowledgement; rejected calls and
invalid numeric values remain visible. Existing rule editors retain drafts across
ordinary HA state updates.

`herald.generate_dashboard` now defaults to `preset: dashboard`, producing this
panel view with its Herald entry ID. The `overview`, `rooms` and `roles` presets
remain supported. Back up a YAML dashboard before generating over its path;
registration and HACS updates do not overwrite an existing layout automatically.

Analytics uses Herald's actual daily counters and channel distributions. There is
no fabricated hourly chart. An accepted transport call is not proof of receipt or
reading. Queue state is in memory and does not claim restart durability. Diagnostics
can open native test entities; pressing those entities sends real notifications.

## Supported card types

`herald-card` is the full card. The same implementation registers these views:

- `ha-herald-general`, `ha-herald-policies`, `ha-herald-policy-guide`
- `ha-herald-flows`, `ha-herald-languages`, `ha-herald-characters`, `ha-herald-mute`
- `ha-herald-rooms`, `ha-herald-queue`, `ha-herald-controls`
- `ha-herald-feed`, `ha-herald-recent`, `ha-herald-overview`

Use a `custom:` prefix in Lovelace YAML. `view_mode` can explicitly select a view.
Policy cards allow search, family/scope filtering, pagination and editing of policy
fields through Herald services. The editor separates saved values from drafts,
shows save failures, previews unsaved rules without delivery, and explains recent
real outcomes. Preview assumptions and effective setting provenance are visible.
See [the rule-editor guide](rule_editor.md). Missing sensors show an unavailable-data message.
General and overview cards show active delivery restrictions; controls and full
cards expose channel settings, source values and local configuration checks.
The check button only reads local HA configuration/state and never sends a test
notification. Channel switches and severity selectors use the actual entities
resolved through HA's entity registry, including renamed controls. Unknown or
unavailable values are distinct from off/free states. See [channel setup](channel_setup.md).
The card currently contains Russian UI text; backend translation files do not
localize every frontend string.

## Compact home event feed

`ha-herald-recent` supports `compact: true` for a short home event feed.
`max_items` controls the initially visible record count (1–8, default 8);
older records remain available under “Ещё события”. Each entry shows its title,
local time and a short description. Opening an entry reveals the full event
description and date. Channel names, delivery outcomes and AI processing metadata
are omitted from the event feed. The description comes from the original event
record; it is not the final rewritten message sent by a channel.

The card uses the current Home Assistant theme and native disclosure controls.
Use a full-width card with automatic height in a Sections view:

```yaml
type: custom:ha-herald-recent
title: События дома
compact: true
max_items: 4
grid_options:
  columns: 12
  rows: auto
```

## Compact policy panel

`ha-herald-policies` accepts `compact: true` to use Home Assistant card header,
radius and border tokens. Its table keeps the notification, state, delivery,
channels and action columns visible; secondary family, last-event and source
columns are omitted from this compact table. Search, family/scope filters,
pagination, the rule editor and service contracts are unchanged. The existing
mobile row layout remains available. Leave `compact` unset for the original
table presentation.

```yaml
type: custom:ha-herald-policies
compact: true
grid_options:
  columns: 12
  rows: auto
```

For a Sections container with `column_span: 2`, use `grid_options.columns: 24`
on the policy card so it fills both section columns. Keeping `columns: 12`
inside that container leaves the card at half its available width.

## Development

`frontend/index.js` bundles the existing `herald-card.js`, dashboard and shared
model helpers. These files are the frontend source of truth. `npm run build` bundles Lit and
writes JavaScript plus gzip under `custom_components/herald/frontend/`.
`npm run build:check` checks exact source/artifact parity; `npm run test:frontend`
checks bundle registration, templates and service contracts without real services.
See the repository [contributor guide](https://github.com/Mesteriis/ha-herald/blob/main/CONTRIBUTING.md).
