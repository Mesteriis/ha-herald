# Architecture

## Boundaries

Automations do not choose users, devices, channels, or languages.
They publish the meaning of an event. Herald resolves delivery from Home Assistant state.

## Runtime layers

- `request.py`: thin request parsing and legacy compatibility
- `context_builder.py`: people, rooms, entities, and semantic enrichment
- `characters.py`: character loading and prompt templates
- `ai.py`: Ollama rewrite, summary, translation, and character styling
- `router.py`: routing strategies, room device selection, and delivery orchestration
- `queue.py`: deduplication, grouping, delay, summary windows, and queue state
- `controls.py`: integration-owned runtime controls
- `coordinator.py`: orchestration, analytics, dashboard feed, and diagnostics
- `frontend_registry.py`: frontend resource and dashboard registration

## Room audio routing

Voice delivery discovers room-local output devices and orders them by default priority:

1. `Alice`
2. `HomePod`
3. `TV`

If a room has multiple device families, Herald creates `select.herald_room_<room>_audio_target`.
The selected target is preferred first and the router then falls back to the next available target.

## Self-actions

Herald speaks its own control-plane changes when someone is home.
These self-actions are voice-only and bypass normal mute and maintenance gating.
