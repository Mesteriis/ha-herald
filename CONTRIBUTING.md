# Contributing

Work in a standalone checkout; local unit tests use synthetic Home Assistant
stubs and must not access the running home. Use a Python 3.11+ environment and Node.js 20+.

```bash
python3 -m pip install pytest pytest-asyncio ruff voluptuous aiohttp PyYAML Jinja2
npm ci
```

## Checks

Run from the repository root:

```bash
python3 -m py_compile custom_components/herald/*.py tests/*.py
ruff check custom_components/herald tests
pytest -q tests
npm run check
npm run build
npm run build:check
npm run test:frontend
```

The ordinary `pytest` entry point and `python -m pytest` both load the repository
root through `tests/conftest.py`. These tests model selected HA interfaces; they do
not prove compatibility with every HA release or successful delivery on real devices.

## Frontend source of truth

Edit `frontend/herald-card.js`, which imports Lit normally. `scripts/build-frontend.mjs`
bundles it with the locked esbuild/Lit dependencies and produces:

- `custom_components/herald/frontend/herald-card.js`
- `custom_components/herald/frontend/herald-card.js.gz`

Commit both assets with source changes. Never edit generated assets directly.
`npm run build:check` rebuilds in memory and compares both assets byte for byte,
without rewriting them. CI and release packaging fail when either asset is stale.
`npm run test:frontend` executes the distributed browser bundle in an isolated VM,
checks all 14 registrations and Lit template branches, and tests policy/control
service payloads using a synthetic `hass` object. It does not measure CSS layout,
browser accessibility, or real HA service behavior; those require separate UI acceptance.

## Scope and review

Keep runtime code in `custom_components/herald/`, frontend code in `frontend/`,
and tests alongside the behavior they cover. Update service/configuration and
operational documentation with public behavior changes. Preserve unrelated changes
and keep secrets and machine-specific runtime snapshots out of the repository.
Use Conventional Commits when practical.

## Home Assistant API compatibility check

Use a **separate Python 3.14 environment** for the pinned real-HA smoke suite:

```bash
python -m pip install homeassistant==2026.9.3
python -m unittest discover -s tests_ha -v
```

The separate `home-assistant-api` CI job runs this command without loading the
synthetic `tests/conftest.py` stubs. It checks real HA setup/shutdown, service
schemas and admin rejection, config-entry lifecycle and diagnostics redaction.
The fixtures do not call external services or devices. This establishes selected
API compatibility with HA 2026.9.3, not full installation or end-device acceptance.
