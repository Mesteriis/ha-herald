"""Filesystem-backed plugin loading for Herald extensions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from homeassistant.core import HomeAssistant

PLUGIN_FILES: tuple[str, ...] = ("plugin.yaml", "plugin.yml")
CHANNEL_FILES: tuple[str, ...] = ("channels.yaml", "channels.yml")
FLOW_FILES: tuple[str, ...] = ("flows.yaml", "flows.yml")
PROMPT_FILES: tuple[str, ...] = (
    "prompts.yaml",
    "prompts.yml",
    "ai_prompts.yaml",
    "ai_prompts.yml",
)
DASHBOARD_CARD_FILES: tuple[str, ...] = ("dashboard_cards.yaml", "dashboard_cards.yml")


@dataclass(slots=True)
class HeraldPlugin:
    """One plugin loaded from /config/herald/plugins/<plugin>/."""

    key: str
    path: Path
    enabled: bool = True
    override_existing: bool = False
    channels: dict[str, dict[str, Any]] = field(default_factory=dict)
    flows: dict[str, dict[str, Any]] = field(default_factory=dict)
    ai_prompts: dict[str, str] = field(default_factory=dict)
    dashboard_cards: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a compact diagnostics snapshot."""
        return {
            "enabled": self.enabled,
            "override_existing": self.override_existing,
            "channels": sorted(self.channels),
            "flows": sorted(self.flows),
            "ai_prompts": sorted(self.ai_prompts),
            "dashboard_cards": len(self.dashboard_cards),
        }


class HeraldPluginManager:
    """Load extension plugins from the Herald config directory."""

    def __init__(self, hass: HomeAssistant, root: Path | None = None) -> None:
        self._hass = hass
        self._root = root or Path(hass.config.path("herald", "plugins"))
        self._plugins: dict[str, HeraldPlugin] = {}

    @property
    def root(self) -> Path:
        """Return the plugin root path."""
        return self._root

    @property
    def plugins(self) -> dict[str, HeraldPlugin]:
        """Return all loaded plugins."""
        return dict(self._plugins)

    async def async_initialize(self) -> None:
        """Ensure the plugin root exists and refresh loaded plugins."""
        await self._hass.async_add_executor_job(self._ensure_root)
        self._plugins = await self._hass.async_add_executor_job(self._load_plugins)

    def active_plugins(self) -> list[HeraldPlugin]:
        """Return only enabled plugins in stable order."""
        return [plugin for _, plugin in sorted(self._plugins.items()) if plugin.enabled]

    def list_plugin_keys(self, *, include_disabled: bool = False) -> list[str]:
        """Return plugin keys, optionally including disabled entries."""
        if include_disabled:
            return sorted(self._plugins)
        return sorted(plugin.key for plugin in self.active_plugins())

    def diagnostic_summary(self) -> dict[str, dict[str, Any]]:
        """Return loaded plugin metadata for diagnostics."""
        return {
            key: plugin.to_dict()
            for key, plugin in sorted(self._plugins.items())
        }

    def dashboard_cards(self) -> list[dict[str, Any]]:
        """Return plugin-provided dashboard cards."""
        cards: list[dict[str, Any]] = []
        for plugin in self.active_plugins():
            cards.extend(deepcopy(plugin.dashboard_cards))
        return cards

    def _ensure_root(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)

    def _load_plugins(self) -> dict[str, HeraldPlugin]:
        plugins: dict[str, HeraldPlugin] = {}
        if not self._root.exists():
            return plugins
        for item in sorted(self._root.iterdir()):
            if not item.is_dir():
                continue
            plugins[item.name] = self._load_plugin(item)
        return plugins

    def _load_plugin(self, directory: Path) -> HeraldPlugin:
        payload = _load_mapping_candidates(directory, PLUGIN_FILES)
        channels = _normalize_mapping(payload.get("channels"))
        channels.update(_load_mapping_candidates(directory, CHANNEL_FILES))

        flows = _normalize_mapping(payload.get("flows"))
        flows.update(_load_mapping_candidates(directory, FLOW_FILES))

        ai_prompts = _normalize_string_mapping(payload.get("ai_prompts", payload.get("prompts", {})))
        ai_prompts.update(_normalize_string_mapping(_load_mapping_candidates(directory, PROMPT_FILES)))

        dashboard_cards = _normalize_dashboard_cards(
            payload.get("dashboard_cards", payload.get("cards", []))
        )
        dashboard_cards.extend(_load_dashboard_cards(directory))

        return HeraldPlugin(
            key=directory.name,
            path=directory,
            enabled=bool(payload.get("enabled", True)),
            override_existing=bool(payload.get("override_existing", False)),
            channels=channels,
            flows=flows,
            ai_prompts=ai_prompts,
            dashboard_cards=dashboard_cards,
        )


def _load_mapping_candidates(directory: Path, candidates: tuple[str, ...]) -> dict[str, Any]:
    for candidate in candidates:
        loaded = _load_yaml_file(directory / candidate)
        if isinstance(loaded, dict):
            return {str(key): value for key, value in loaded.items()}
    return {}


def _load_dashboard_cards(directory: Path) -> list[dict[str, Any]]:
    for candidate in DASHBOARD_CARD_FILES:
        loaded = _load_yaml_file(directory / candidate)
        cards = _normalize_dashboard_cards(loaded)
        if cards:
            return cards
    return []


def _normalize_mapping(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for key, payload in value.items():
        if isinstance(payload, dict):
            normalized[str(key)] = dict(payload)
    return normalized


def _normalize_string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, payload in value.items():
        if payload is None:
            continue
        normalized[str(key)] = str(payload)
    return normalized


def _normalize_dashboard_cards(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        value = value.get("cards", [])
    if not isinstance(value, list):
        return []
    cards: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            cards.append(dict(item))
    return cards


def _load_yaml_file(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None
