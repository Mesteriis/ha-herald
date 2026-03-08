# HACS Migration

## Goal

Move from local development usage in `config/custom_components/herald/` to a standalone
HACS-managed repository published from `distrib/herald/`.

## Recommended migration path

### Stage 1: Publish repository

1. Publish `distrib/herald/` as its own GitHub repository.
2. Install it in HACS as a custom repository.
3. Keep the local dev copy temporarily while validating the packaged build.

### Stage 2: Freeze local config

Before switching runtime ownership:

1. Export a snapshot of your Herald YAML config.
2. Note current entities and services in use.
3. Confirm that automations call:
   - `herald.notify`
   - `herald.acknowledge`
   - `herald.snooze_flow`
   - `herald.generate_dashboard`

No migration step should rely on `browser_mod`.

### Stage 3: Install HACS package

1. Install the HACS version.
2. Restart Home Assistant.
3. Verify the integration loads and entities appear.
4. Rebuild the frontend resource if needed:

```yaml
url: /herald/herald-card.js
type: module
```

### Stage 4: Remove local override

Once HACS version is confirmed working:

1. Stop Home Assistant.
2. Move the local dev directory out of the active custom components path:

```bash
mv custom_components/herald _tmp_/herald-dev-backup
```

3. Start Home Assistant again.
4. Confirm the loaded integration now comes from HACS-managed files.

This is safer than deleting the local source immediately.

### Stage 5: Validate runtime

Check:

- `sensor.herald_status`
- `sensor.herald_notifications_today`
- `sensor.herald_last_notification`
- `sensor.herald_queue_size`
- config entry loads without repair issues
- mobile push acknowledge/snooze works
- Telegram callback acknowledgement works
- generated dashboards still render

## Rollback plan

If the HACS package fails:

1. Stop Home Assistant.
2. Remove the HACS-installed `custom_components/herald`.
3. Restore the dev backup:

```bash
mv _tmp_/herald-dev-backup custom_components/herald
```

4. Start Home Assistant.

## Long-term structure

Recommended ongoing layout:

- `custom_components/herald/`: local development source only while actively building
- `distrib/herald/`: clean export used for the GitHub/HACS repository

If you stop active local development, keep only:

- HACS-managed runtime package
- `distrib/herald/` as the release source snapshot

## Optional hardening

After migration, consider:

1. adding a CI rule that fails if `distrib/herald/` is stale versus source
2. cutting releases only from `distrib/herald/`
3. eventually moving source-of-truth to the standalone repository and treating this HA config repo as consumer-only
