# Publish Checklist

## Goal

Publish `Herald` as a standalone HACS integration repository from `distrib/herald/`
without any dependency on `browser_mod`.

## Repository checklist

1. Create a new GitHub repository, for example `ha-herald`.
2. Copy the contents of `distrib/herald/` to the repository root.
3. Ensure the repository contains exactly one integration under `custom_components/herald/`.
4. Confirm these files exist:
   - `hacs.json`
   - `README.md`
   - `CHANGELOG.md`
   - `custom_components/herald/manifest.json`
   - `custom_components/herald/services.yaml`
   - `custom_components/herald/strings.json`
   - `custom_components/herald/translations/*.json`
   - `custom_components/herald/brand/icon.png`
   - `custom_components/herald/brand/logo.png`

## Validation checklist

Run in the repository root:

```bash
python3 -m py_compile custom_components/herald/*.py tests/*.py
pytest -q tests
python3 -m json.tool hacs.json >/dev/null
python3 -m json.tool custom_components/herald/manifest.json >/dev/null
npm ci
npm run check
npm run build
```

Expected result:

- Python checks pass
- tests pass
- JSON files are valid
- `custom_components/herald/frontend/herald-card.js` is built

## GitHub Actions checklist

Verify workflows are enabled:

- `.github/workflows/build.yml`
- `.github/workflows/validate.yaml`
- `.github/workflows/release.yml`
- `.github/workflows/release-please.yml`

Repository settings:

1. Enable GitHub Actions.
2. Allow workflows to create pull requests if you want `release-please` to operate normally.
3. Make sure `GITHUB_TOKEN` has `contents`, `issues`, and `pull-requests` write access.

## HACS checklist

1. In Home Assistant HACS, add the GitHub repository as a custom repository of type `Integration`.
2. Install `Herald Notification Center`.
3. Restart Home Assistant.
4. Add Lovelace resource:

```yaml
url: /herald/herald-card.js
type: module
```

5. Add the integration in Settings -> Devices & Services.

## Release checklist

1. Merge conventional-commit changes into `main`.
2. Let `release-please` open/update the release PR.
3. Merge the release PR.
4. Wait for the tag/release workflow to produce the zip artifact.
5. Verify HACS sees the new version.

## Runtime checklist

After install, verify:

- `sensor.herald_status` exists
- `sensor.herald_notifications_today` exists
- `sensor.herald_last_notification` exists
- `sensor.herald_queue_size` exists
- `herald.notify` works
- `herald.generate_dashboard` works
- mobile action feedback clears the originating push notification
- Telegram callback acknowledgement is returned

## Explicit non-goals

The publishable core package does not require or depend on:

- `browser_mod`
- custom popup frameworks
- external UI glue outside the bundled Lovelace card
