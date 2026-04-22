# Dashboard

Herald registers two frontend surfaces in storage-mode Lovelace:

- `/herald/herald-card.js`
- `/herald-control-center`

The generated dashboard is a starter operational layout. It is safe to replace or
rebuild it with a custom YAML design after installation.

Useful entities for custom dashboards:

- `sensor.herald_notification_center_status`
- `sensor.herald_notification_center_queue_size`
- `sensor.herald_notification_center_last_notification`
- `sensor.herald_notification_center_deliveries_today`
- `switch.herald_maintenance_mode`
- `switch.herald_mute_all`
- `switch.herald_dashboard_sidebar`
- `select.herald_room_<room>_audio_target`
