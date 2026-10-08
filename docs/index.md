# Herald AI Notification Center

Herald routes Home Assistant notifications using configurable channels, people,
rooms, policies and runtime controls. It supports in-memory batching, optional
Ollama rewriting/summaries, character templates and a Lit dashboard.

Start with [architecture](architecture.md), [services](api.md), [controls](controls.md)
and [dashboard](dashboard.md). The repository README describes installation.
See [AI characters and rewriting](characters.md) for Domovoy's voice, template updates,
and the controls required to enable paraphrasing.

Local tests exercise synthetic HA interfaces and frontend templates. A successful
local run is not live acceptance on your Home Assistant instance. Verify the
configured transports and dashboard before relying on them for alerts.
