# Release

## Validation

Run from the repository root:

```bash
python3 -m pip install pytest pytest-asyncio ruff voluptuous aiohttp PyYAML Jinja2
python3 -m py_compile custom_components/herald/*.py tests/*.py
ruff check custom_components/herald tests
pytest -q tests
npm ci
npm run check
npm run build
```

## GitHub workflows

- `build.yml`
- `validate.yaml`
- `release-please.yml`
- `release.yml`
- `pages.yml`

## Suggested commit messages

- `feat: prepare Herald 0.4.0 release snapshot`
- `docs: publish Herald GitHub Pages documentation`
- `fix: remove stale release metadata and authorship traces`
