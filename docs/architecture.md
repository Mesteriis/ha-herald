# Architecture

Herald is a Home Assistant custom integration. The coordinator composes request
parsing, context, policies, queueing and delivery. Automations can send semantic
requests or specify legacy user/room/channel fields; those explicit boundaries
must survive batching and summaries.

## Implementation map

| Area | Actual files | Dependencies / role |
| --- | --- | --- |
| Lifecycle | `__init__.py`, `config_flow.py` | Config entries, merged options, setup/unload |
| Service contract | `services.py`, `request.py`, `models.py`, `const.py` | HA validation, normalized requests, dataclasses/defaults |
| Orchestration | `coordinator.py` | Pipeline, Store state, trace, counters and generated dashboard |
| Context | `context_builder.py`, `presence.py` | HA state, people, rooms and quiet hours |
| Policy and flow | `notification_policies.py`, `policy_rules.py`, `rule_options.py`, `flows.py`, `controls.py` | Registry, overrides, shared rule checks, target catalogs, flow configuration, runtime controls |
| Queue | `queue.py` | In-memory delay, compatible grouping and deduplication |
| Delivery | `router.py`, `actions.py`, `channel_tts_hume.py` | HA services, notification actions, optional Hume synthesis/cache |
| AI | `ai.py`, `characters.py`, `translations.py` | Ollama requests, character/Jinja templates and text fallback |
| Topology/extensions | `discovery.py`, `plugins.py` | HA/registry discovery and declarative YAML additions |
| Entities | `sensor.py`, `binary_sensor.py`, `switch.py`, `select.py`, `number.py`, `button.py`, `entity.py`, `helpers.py` | Integration-owned entities and compatibility helpers |
| Frontend | `frontend_registry.py`, `frontend/herald-card.js` | Resource/dashboard registration and Lit card source |
| Diagnostics | `diagnostics.py` | Redacted diagnostic export |
| Configuration inspection | `configuration_check.py`, `control_entities.py` | Read-only local checks, bounded safe report, actual control identity after HA entity renames |

[code_architecture.yaml](code_architecture.yaml) records the actual Python modules
and local import edges. It is an import map, not proof that every dependency runs
for every request.

## Configuration layers

Base dictionaries merge recursively in YAML → config-entry data → entry-options
order; later scalar/list values replace earlier ones. Options updates reload the
entry. The merged data becomes `HeraldConfig`. Runtime controls stored
by Herald override applicable fields. Per-notification policies select delivery
mode, channel list, personal recipients, local room, presence/quiet-hours conditions,
severity, cooldown and notes. Final safety constraints such as
maintenance still apply to those routes.

Plugins under `<HA config>/herald/plugins/` contribute declarations for existing
channel types, flows, prompt text and dashboard cards. They do not load arbitrary
Python transport adapters. Implemented transports are dispatched in `router.py`.

## Persistence and limits

HA Store retains runtime controls, counters/selected state and policy data. The
pending notification queue is in memory. A restart can discard pending work;
there is no durable broker, delivery receipt guarantee, or cross-node replication.

Discovery uses HA services/states, registries and configured device links. Automatic
Telegram discovery requires a single allowed chat; ambiguous destinations need an
explicit channel. Explicit channels should be reviewed for each installation.
The policy registry is a static discovery aid, not an interpreter for arbitrary
Jinja or every external automation engine.

There are no separate correlation, learning, webhook, cluster or daily-digest
modules. Earlier design sketches mentioning those modules were aspirational.


## Effective configuration and explainable rules

`effective_config.py` maps shared Options/control fields and constructs sparse,
revisioned edits. `controls.py` owns effective runtime values and their provenance;
legacy values migrate without guessing their origin. The coordinator applies each
Options revision once before reload and restores it idempotently after restart.
`config_flow.py` exposes a native Options menu and captures a separate comparison
snapshot for the selected editor. Static translated field names map to existing
configuration paths; channel discovery runs only for channel selection/editing.
Saving one section ends the flow without copying values from other sections.

`policy_editor.py` builds disposable rule drafts and bounded example requests.
`decisions.py` translates production routing checks and actual delivery outcomes
into structured explanations without side effects. Saved-rule and draft previews
share admission checks and router selection. The frontend consumes the service
response and discards stale asynchronous responses after rule or draft changes.

`policy_rules.py` applies explicit rule constraints to the current request audience
and a presence snapshot. `rule_options.py` derives known targets from configured
users/channels and HA person/room state. The coordinator uses the same checker for
draft admission and real events, then passes it into the router for delivery-time
checks. Queued events retain their captured rule; incompatible rules stay in
separate groups. New constraints cannot be bypassed by legacy routing or force.

`configuration_check.py` inspects only local, allowlisted transport fields and HA
state/service registration. Current delivery restrictions remain separate from
structural checks. Provider credentials and reachability are untested. The normal
snapshot supplies existing effective-setting provenance; the read-only service
reuses that published provenance and marks it unknown if its value has changed.
`control_entities.py` reads an existing entity registry without creating entries
and maps control keys through platform, unique ID and config-entry ownership.
Missing entries never fall back to an unrelated entity with a similar name.
