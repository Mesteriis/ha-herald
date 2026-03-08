"""Tests for Herald plugin loading and runtime extension merge."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from custom_components.herald.coordinator import HeraldCoordinator
from custom_components.herald.models import HeraldConfig
from custom_components.herald.plugins import HeraldPlugin, HeraldPluginManager


class _FakeConfig:
    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, *parts: str) -> str:
        return str(self._root.joinpath(*parts))


class _FakeHass:
    def __init__(self, root: Path) -> None:
        self.config = _FakeConfig(root)

    async def async_add_executor_job(self, func, *args):
        return func(*args)


@pytest.mark.asyncio
async def test_plugin_manager_loads_inline_and_sidecar_extensions(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "herald" / "plugins" / "ops"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(
        "\n".join(
            (
                "enabled: true",
                "override_existing: true",
                "channels:",
                "  ops_push:",
                "    type: mobile_app",
                "    service: notify.ops",
                "ai_prompts:",
                "  nightwatch: Stay terse and operational.",
            )
        ),
        encoding="utf-8",
    )
    (plugin_dir / "flows.yaml").write_text(
        "\n".join(
            (
                "ops_alerts:",
                "  severity: critical",
                "  channels:",
                "    - ops_push",
            )
        ),
        encoding="utf-8",
    )
    (plugin_dir / "dashboard_cards.yaml").write_text(
        "\n".join(
            (
                "- type: markdown",
                "  title: Ops Plugin",
                "  content: Plugin card loaded",
            )
        ),
        encoding="utf-8",
    )

    manager = HeraldPluginManager(_FakeHass(tmp_path))

    await manager.async_initialize()

    assert manager.list_plugin_keys() == ["ops"]
    assert manager.diagnostic_summary()["ops"]["channels"] == ["ops_push"]
    assert manager.diagnostic_summary()["ops"]["flows"] == ["ops_alerts"]
    assert manager.diagnostic_summary()["ops"]["ai_prompts"] == ["nightwatch"]
    assert manager.dashboard_cards()[0]["title"] == "Ops Plugin"


def test_plugin_extensions_respect_override_existing(tmp_path: Path) -> None:
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "persistent_default": {"type": "persistent_notification"},
            },
            "flows": {
                "system_events": {"severity": "system", "channels": ["persistent_default"]},
            },
            "personalities": {
                "Jarvis": "Base prompt",
            },
        }
    )
    fake = SimpleNamespace(
        config=config,
        plugins=SimpleNamespace(
            active_plugins=lambda: [
                HeraldPlugin(
                    key="no_override",
                    path=tmp_path / "no_override",
                    channels={
                        "persistent_default": {
                            "type": "telegram",
                            "service": "telegram_bot.send_message",
                        }
                    },
                    flows={
                        "system_events": {
                            "severity": "critical",
                            "channels": ["persistent_default"],
                        }
                    },
                    ai_prompts={"Jarvis": "Plugin prompt"},
                ),
                HeraldPlugin(
                    key="override",
                    path=tmp_path / "override",
                    override_existing=True,
                    channels={
                        "persistent_default": {
                            "type": "telegram",
                            "service": "telegram_bot.send_message",
                        },
                        "ops_push": {
                            "type": "mobile_app",
                            "service": "notify.ops",
                        },
                    },
                    flows={
                        "system_events": {
                            "severity": "critical",
                            "channels": ["ops_push"],
                        },
                        "ops_alerts": {
                            "severity": "warning",
                            "channels": ["ops_push"],
                        },
                    },
                    ai_prompts={
                        "Jarvis": "Override prompt",
                        "Nightwatch": "Operational voice",
                    },
                ),
            ]
        ),
    )

    HeraldCoordinator._apply_plugin_extensions(fake)

    assert fake.config.channels["persistent_default"].channel_type == "telegram"
    assert fake.config.channels["ops_push"].service == "notify.ops"
    assert fake.config.flows["system_events"].severity == "critical"
    assert fake.config.flows["ops_alerts"].channels == ["ops_push"]
    assert fake.config.personalities["Jarvis"] == "Override prompt"
    assert fake.config.personalities["Nightwatch"] == "Operational voice"


def test_default_tv_rules_extend_selected_flows() -> None:
    config = HeraldConfig.from_raw(
        {
            "channels": {
                "tv_auto": {"type": "tv", "entity_id": "media_player.tv"},
            },
            "flows": {
                "security_alerts": {"channels": ["persistent_default"]},
                "camera_alerts": {"channels": ["persistent_default"]},
                "timer_notifications": {"channels": ["persistent_default"]},
                "system_events": {"channels": ["persistent_default"]},
            },
        }
    )
    fake = SimpleNamespace(config=config)

    HeraldCoordinator._apply_default_tv_routing_rules(fake)

    assert "tv_auto" in fake.config.flows["security_alerts"].channels
    assert "tv_auto" in fake.config.flows["camera_alerts"].channels
    assert "tv_auto" in fake.config.flows["timer_notifications"].channels
    assert "tv_auto" not in fake.config.flows["system_events"].channels
