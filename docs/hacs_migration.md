# HACS Migration

1. Publish `distrib/herald/` as its own repository.
2. Install it in HACS as a custom repository.
3. Restart Home Assistant and confirm the config entry loads.
4. Confirm the runtime entities and controls appear.
5. Remove any local `custom_components/herald` override only after the HACS package is verified.
