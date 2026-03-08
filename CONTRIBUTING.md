# Contributing

## Local setup

1. Clone the repository into `config/custom_components/herald`.
2. Create a Python 3.11 environment.
3. Install development tools:

```bash
python3 -m pip install pytest pytest-asyncio ruff voluptuous aiohttp
npm install
```

4. Run checks:

```bash
python3 -m py_compile *.py tests/*.py
ruff check .
pytest -q
npm run build
```

## Commit style

Use Conventional Commits whenever practical, for example:

- `feat: add telegram inline keyboard actions`
- `fix: restore coordinator lookup for sensors`
- `docs: expand migration notes`

## Scope

Please keep changes modular:

- Core runtime changes in Python
- Frontend changes in `frontend/`
- Documentation updates in `docs/`
- Tests updated alongside behavior changes
