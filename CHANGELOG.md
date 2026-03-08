# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

## [0.2.0] - 2026-03-08

### Added
- Actionable notifications with acknowledge and snooze support for mobile app and Telegram.
- Local Lovelace resource serving at `/herald/herald-card.js`.
- Nested repository layout for standalone HACS development.
- Repo-local CI workflows, issue templates, documentation, and tests.
- TypeScript/Lit source for `herald-card` with local bundled output.

### Changed
- Sensor setup now resolves the coordinator from `hass.data[DOMAIN][DATA_COORDINATORS]`.
- Dashboard generation now references the local frontend resource.
- Runtime trace snapshots now include acknowledged notifications and snoozed flows.
