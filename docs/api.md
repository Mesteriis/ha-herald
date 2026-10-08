# Services

## `herald.notify`

The primary semantic fields are `event`, `message`, `level`, `ai`, `context`,
`entities`, `suppress`, `group` and `immediately`. `message` is required. Legacy
explicit fields such as `flow`, `users`, `room`, `channels`, `rewrite`, `summarize`,
`metadata`, and notification action options remain supported; consult
`custom_components/herald/services.yaml` and `services.py` for the complete schema.

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

`immediately` bypasses the configured queue window for that item. Compatible queued
items may be summarized; different audiences/routes must remain separate. Explicit
`summarize: false` and `rewrite: false` retain their meaning through the pipeline.
Omitting `rewrite` requests AI rewriting by default, subject to the global and
severity AI controls. Legacy `already_humanized: true` preserves the original
text when `rewrite` is omitted; an explicit `rewrite` value takes precedence.
If AI is unavailable, the notification keeps its original text.
The queue is not durable across HA restarts.

## Registry and policies

- `herald.refresh_notification_registry`: refresh static discovery.
- `herald.get_notification_registry`: return discovered notification entries.
- `herald.get_notification_policy`: inspect one `notification_key`.
- `herald.set_notification_policy`: update enablement, delivery mode, channels,
  personal recipients, local room, presence/quiet-hours conditions, severity
  override, cooldown (0–86400 seconds), or notes. Omitted fields retain saved values.
- `herald.reset_notification_policy`: remove the override for one key.

Delivery modes are `inherit`, `disabled`, `text_only`, `voice_only`, `push_only`
and `custom`. An explicitly selected mode with no eligible channels produces no
delivery; it does not restore the default route. Maintenance constraints take
priority over delivery mode selection.

Additional fields apply after mode selection and also constrain forced/legacy routes:

| Field | Values and behavior |
| --- | --- |
| `users` | `null` inherits; a list of person IDs intersects the request audience; `[]` blocks the entire event. Slugs normalize to `person.slug`. Silent users are removed. |
| `target_room` | `null` inherits; a known room strictly limits voice/TV targets without fallback to another room. Text channels keep their normal audience rules. |
| `presence` | `any` (default), `someone_home`, `nobody_home`. Evaluated from Herald's presence snapshot. |
| `quiet_hours` | `inherit` (default), `text_only` (remove voice/TV from eligible channels), `mute` (drop the event). No deferred delivery or extra channels. |

Unknown saved people/rooms remain visible and block delivery until corrected. A
selected personal audience does not make dashboard, log, persistent notifications
or room audio private; unowned mobile/Telegram channels are excluded. Registry
responses expose `user_options`/`room_options`; entries and single-policy responses
also expose `available_users`/`available_rooms` as `{value, label}` lists.

Each event captures its rule on admission. Rule edits affect subsequent events.
Captured constraints are checked again before processing a queued group and after
AI processing before transport calls, with fresh presence, quiet hours and user
silence. A changed condition drops the event with an explanation; it does not
reschedule it. Delivery calls already started cannot be recalled.

The registry reads static `service: herald.notify` and `action: herald.notify`
calls in the main configuration, conventional automation/script/package/template
files and supported structural YAML includes. It also recognizes selected-event
routing patterns. Dynamic event keys and arbitrary Jinja cannot be fully enumerated;
scan issues describe skipped/ambiguous inputs. Secret tags are not resolved and
includes outside the configuration root, hidden paths, and secret files are rejected.
This registry is a discovery aid, not an execution trace of every possible automation.

## Preview an unsaved rule

`herald.preview_notification_policy` is a response-only service. It accepts
`notification_key`, an optional partial `policy` with the same fields as
`set_notification_policy`, `scenario` (`current`, `quiet_hours`, `away`), and an
optional example `message`. Omit `policy` to inspect the saved rule. An empty
policy object previews the saved values as a draft; use explicit inherit/empty
values to preview resetting overrides.

```yaml
action: herald.preview_notification_policy
data:
  notification_key: washing_cycle_finished
  policy:
    delivery_mode: text_only
    cooldown_override: 300
  scenario: quiet_hours
response_variable: route
```

The response contains the normal route-preview fields plus `policy`, `scenario`,
`draft`, `warnings`, relevant `effective_settings`, and `explanation` (status,
reason code, summary, steps, channels, warnings). It never saves the draft, queues
or sends a message, invokes AI, or changes duplicate/cooldown state. Scenarios
alter routing presence/quiet hours only; flow conditions still read real entities
and current time. Unknown templates and ambiguous source defaults are disclosed.

Registry entries expose `last_decision` for new real events, including admission
drops. The newest outcomes for up to 256 event keys survive restart. Successful
service calls do not prove physical receipt or reading. Existing `route_preview`
continues to retain its diagnostic snapshot; draft previews do not replace it.

## Other services

- `herald.configuration_check`: response-only local inspection with optional
  `entry_id`. Returns `schema_version`, `checked_at`, active `restrictions`, channel
  `checks`, actual control entity IDs, allowlisted setting provenance, `summary`,
  `limitations` and `truncated`. It does not refresh discovery, mutate Store/runtime
  history, call AI, send messages, or validate provider credentials/connectivity.
  The status sensor also exports this report as `configuration_check`. A configured
  channel is not proof of delivery. Use `route_preview` to evaluate a specific event.
- `herald.route_preview`: inspect routing without sending a notification or running AI.
- `herald.trace_snapshot`: return runtime trace data for local debugging.
- `herald.generate_dashboard`: administrator-only YAML export. `path` must name a
  `.yaml` or `.yml` file beneath `dashboards/` relative to the HA configuration
  root. Absolute paths, traversal, and symlink escapes are rejected. The default
  is `dashboards/herald_dashboard.yaml`; exporting can replace an existing file there.
  `preset` defaults to `dashboard`; `overview`, `rooms` and `roles` remain available.
- `herald.set_flow_state`: change runtime flow enablement.
- `herald.acknowledge`: record an acknowledgement.
- `herald.snooze_flow`: temporarily mute a flow.

Service response traces may contain notification text and device/user context.
Use the dedicated redacted diagnostics export when sharing a diagnostic report.
