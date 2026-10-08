# Controls

## Global controls

- `switch.herald_ai_enabled`
- `switch.herald_maintenance_mode`
- `switch.herald_mute_all`
- `switch.herald_dashboard_sidebar`
- `select.herald_maintenance_min_level`

## Channel families

- `switch.herald_channel_voice`
- `switch.herald_channel_push`
- `switch.herald_channel_tv`

## Per-room controls

- `binary_sensor.herald_room_<room>_presence`
- `switch.herald_room_<room>_presence`
- `select.herald_room_<room>_audio_target` when more than one output family exists

## Per-user controls

- `select.herald_user_<user>_language`
- `select.herald_user_<user>_character`
- `switch.herald_user_<user>_silent`

## Test controls

- `button.herald_test_level_info`
- `button.herald_test_level_warning`
- `button.herald_test_level_critical`
- `button.herald_test_channel_<channel>`

## State and configuration

Channel switches and importance thresholds are available in the Herald controls
card alongside a local configuration report. The card resolves controls through
their registry identity, displays unavailable/missing states, and reports failed
updates. See [the channel setup guide](channel_setup.md).

Controls are integration-owned entities, not automatically created input helpers.
The integration Options menu separates quiet hours, Ollama, maintenance, channels
and notification flows. Channel and flow sections edit one selected item at a time.
Each form reads effective runtime values and submits only edited fields; saving
closes the dialog and preserves other settings. See the [settings guide](options.md).
Each edited control value is applied once and persisted before entry reload; later
entity edits are not overwritten by stale Options snapshots. Existing runtime values
are preserved with source `restored` when their origin cannot be recovered.
`effective_settings` exposes value, source, inherited value and inherited source.
Dormant discovered-channel preferences survive a temporary topology disappearance.
AI enablement is one effective setting shared by its switch and client configuration.
Saving the Ollama server/model form does not enable AI or test the connection.
Entity IDs may differ when users rename them in the HA entity registry.
