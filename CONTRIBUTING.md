# Contributing

## Local setup

1. Clone the repository into your Home Assistant config or a standalone workspace.
2. Create a Python 3.11 environment.
3. Install the development tools you need.

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
```

## Commit style

Use Conventional Commits when practical.

Examples:

- `feat: add room audio target fallback routing`
- `fix: recover dashboard resource registration on cold start`
- `docs: update release and controls documentation`

## Scope

Keep changes modular:

- runtime pipeline changes in `custom_components/herald/`
- repo docs in `docs/`
- frontend source in `frontend/`
- tests updated alongside behavior changes

## Maintainer

Aleksandr Meshchryakov <avm@sh-inc.ru>
