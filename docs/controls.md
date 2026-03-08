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
