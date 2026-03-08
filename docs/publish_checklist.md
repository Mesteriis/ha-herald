# Publish Checklist

1. Validate Python, tests, frontend checks, and JSON metadata.
2. Confirm `custom_components/herald/manifest.json` and `hacs.json` versions are aligned.
3. Confirm `README.md`, `CHANGELOG.md`, and `docs/` describe the current runtime behavior.
4. Push to `main` and verify GitHub Actions `build`, `validate`, and `pages` succeed.
5. Merge or create the release through `release-please`.
6. Verify the tagged release contains the HACS-ready repository layout.
