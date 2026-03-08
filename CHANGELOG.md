# Changelog

## 0.4.0 - 2026-03-08

- upgraded Herald to the AI Notification Center architecture with the thin `herald.notify` contract
- added context enrichment from `person.*`, `device_tracker.*`, room sensors, and per-user runtime controls
- added Herald-owned `switch`, `select`, `number`, `button`, and `binary_sensor` control entities
- added maintenance mode, mute-all, sidebar visibility, per-channel tests, and per-level tests
- added self-action voice announcements for Herald control-plane changes when someone is home
- added AI characters from `/config/herald/<character>/` with Ollama rewrite, summary, and translation support
- added HumeAI-backed TTS delivery and preserved TV delivery through the existing Home Assistant stack
- added room-local notification output selection with fallback order `Alice -> HomePod -> TV`
- added routing strategies for presence, room, severity, quiet hours, and activity
- added queue deduplication, grouping, delay, summaries, dashboard feed, traces, and analytics sensors
- added plugin loading for custom channels, flows, prompts, and dashboard cards
- added storage-mode Lovelace resource registration and auto-install of `Herald Control Center`
- added standalone unit coverage and Home Assistant runtime smoke tests for the current pipeline

## 0.3.0

- introduced the first normalized Herald runtime with AI rewrite, flow routing, and queue handling

## 0.2.0

- initial Herald notification center runtime
