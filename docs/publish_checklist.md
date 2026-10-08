# Publish checklist

1. Run Python, frontend, documentation and metadata checks for the final commit.
2. Confirm the integration manifest version, release metadata and tag agree.
   `hacs.json` declares compatibility/layout and has no package version field.
3. Confirm README/docs describe current behavior and limitations.
4. Verify remote `build`, `validate` and `pages` results for that exact commit.
5. Complete supported-HA installation/reload and selected-channel acceptance.
6. Publish the intended tag/release through the repository release process.
7. Download the published package and check its integration layout and both frontend assets.
