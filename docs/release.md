# Release validation

Run from an isolated repository checkout, using Python 3.11+ and Node.js 20+:

```bash
python3 -m pip install pytest pytest-asyncio ruff voluptuous aiohttp PyYAML Jinja2
python3 -m py_compile custom_components/herald/*.py tests/*.py
ruff check custom_components/herald tests
pytest -q tests
npm ci
npm run check
npm run build:check
npm run test:frontend
```

If frontend source changes, run `npm run build` first and commit both generated
assets. The parity check is read-only and fails on stale/missing JavaScript or gzip.
Build documentation separately with `mkdocs build --strict` after installing
`mkdocs<2` and `mkdocs-material`.

`build.yml` runs Python and frontend checks. `validate.yaml` checks JSON/HACS
metadata. `pages.yml` builds documentation. `release-please.yml` manages release
metadata; `release.yml` verifies frontend assets and packages tagged code. The tag
workflow alone is not proof that all Python checks or live acceptance passed.

Before publishing, verify remote CI for the exact commit, install/reload behavior
on a supported HA version, the built dashboard, and intended transport success and
failure paths. Download and inspect the published artifact before claiming a
release is usable. No real device/service is called by the local test suite.

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
