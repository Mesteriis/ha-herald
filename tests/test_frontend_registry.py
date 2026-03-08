"""Tests for Herald frontend resource registration."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.herald.const import (
    FRONTEND_BASE_URL,
    FRONTEND_DASHBOARD_TITLE,
    FRONTEND_DASHBOARD_URL_PATH,
    FRONTEND_MODULE_URL,
)
from custom_components.herald.frontend_registry import HeraldFrontendRegistration


class _FakeResources:
    def __init__(self) -> None:
        self.loaded = True
        self._items: list[dict] = []
        self.async_create_item = AsyncMock(side_effect=self._create)

    def async_items(self):
        return list(self._items)

    async def _create(self, item: dict) -> dict:
        payload = {"id": str(len(self._items) + 1), **item}
        self._items.append(payload)
        return payload


class _FakeHttp:
    def __init__(self) -> None:
        self.async_register_static_paths = AsyncMock()


class _FakeConfig:
    def path(self, value: str) -> str:
        return str(Path("/Volumes/config") / value)


class _FakeDashboardStore:
    def __init__(self, hass, config) -> None:
        self.hass = hass
        self.config = config
        self.saved = None

    async def async_save(self, config: dict) -> None:
        self.saved = config


class _FakeStore:
    saved_data: dict[str, dict] = {}

    def __init__(self, hass, version, key) -> None:
        self.key = key

    def __class_getitem__(cls, item):
        return cls

    async def async_load(self):
        return self.saved_data.get(self.key)

    async def async_save(self, value):
        self.saved_data[self.key] = value


class _FakeHass:
    def __init__(self) -> None:
        self.http = _FakeHttp()
        self.config = _FakeConfig()
        self.data = {
            "lovelace": SimpleNamespace(
                resource_mode="storage",
                resources=_FakeResources(),
                dashboards={},
            ),
            "frontend_panels": {},
        }


class _FakeLovelaceKey:
    pass


def test_frontend_registry_supports_hasskey_lovelace_runtime(monkeypatch) -> None:
    hass = _FakeHass()
    lovelace = hass.data.pop("lovelace")
    key = _FakeLovelaceKey()
    hass.data[key] = lovelace

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry._LOVELACE_DATA_KEY",
        key,
    )

    registration = HeraldFrontendRegistration(hass)
    assert registration._resolve_lovelace() is lovelace


def test_frontend_registry_registers_resource_and_static_path(monkeypatch) -> None:
    hass = _FakeHass()
    extra_urls: list[str] = []

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.add_extra_js_url",
        lambda hass, url: extra_urls.append(url),
    )

    import asyncio
    asyncio.run(HeraldFrontendRegistration(hass).async_register())

    registered = hass.http.async_register_static_paths.await_args.args[0][0]
    assert registered.url_path == FRONTEND_BASE_URL
    assert FRONTEND_MODULE_URL in extra_urls
    assert hass.data["lovelace"].resources.async_items()[0]["url"] == FRONTEND_MODULE_URL


def test_frontend_registry_auto_installs_storage_dashboard(monkeypatch) -> None:
    hass = _FakeHass()
    extra_urls: list[str] = []
    panels: list[tuple[str, dict]] = []
    _FakeStore.saved_data = {}

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.add_extra_js_url",
        lambda hass, url: extra_urls.append(url),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.frontend.async_register_built_in_panel",
        lambda hass, component_name, **kwargs: panels.append((component_name, kwargs)),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.lovelace_dashboard.LovelaceStorage",
        _FakeDashboardStore,
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.Store",
        _FakeStore,
    )

    import asyncio

    asyncio.run(
        HeraldFrontendRegistration(
            hass,
            dashboard_factory=lambda: {"title": FRONTEND_DASHBOARD_TITLE, "views": [{"title": "Herald"}]},
        ).async_register()
    )

    assert FRONTEND_MODULE_URL in extra_urls
    assert hass.data["lovelace"].resources.async_items()[0]["url"] == FRONTEND_MODULE_URL
    assert FRONTEND_DASHBOARD_URL_PATH in hass.data["lovelace"].dashboards
    assert (
        _FakeStore.saved_data["lovelace_dashboards"]["items"][0]["url_path"]
        == FRONTEND_DASHBOARD_URL_PATH
    )
    installed = hass.data["lovelace"].dashboards[FRONTEND_DASHBOARD_URL_PATH]
    assert installed.saved == {"title": FRONTEND_DASHBOARD_TITLE, "views": [{"title": "Herald"}]}
    assert panels == [
        (
            "lovelace",
            {
                "frontend_url_path": FRONTEND_DASHBOARD_URL_PATH,
                "require_admin": False,
                "sidebar_title": FRONTEND_DASHBOARD_TITLE,
                "sidebar_icon": "mdi:bell-badge",
                "config": {"mode": "storage"},
            },
        )
    ]


def test_frontend_registry_retries_until_lovelace_is_ready(monkeypatch) -> None:
    hass = _FakeHass()
    lovelace = hass.data.pop("lovelace")
    extra_urls: list[str] = []
    panels: list[tuple[str, dict]] = []
    scheduled: list = []
    _FakeStore.saved_data = {}

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.add_extra_js_url",
        lambda hass, url: extra_urls.append(url),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.frontend.async_register_built_in_panel",
        lambda hass, component_name, **kwargs: panels.append((component_name, kwargs)),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.lovelace_dashboard.LovelaceStorage",
        _FakeDashboardStore,
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.Store",
        _FakeStore,
    )

    def _fake_call_later(hass, delay, callback):
        scheduled.append(callback)
        return lambda: None

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.async_call_later",
        _fake_call_later,
    )

    import asyncio

    asyncio.run(
        HeraldFrontendRegistration(
            hass,
            dashboard_factory=lambda: {"title": FRONTEND_DASHBOARD_TITLE, "views": [{"title": "Herald"}]},
        ).async_register()
    )

    assert FRONTEND_MODULE_URL in extra_urls
    assert scheduled
    assert FRONTEND_DASHBOARD_URL_PATH not in _FakeStore.saved_data.get("lovelace_dashboards", {})

    hass.data["lovelace"] = lovelace
    asyncio.run(scheduled.pop()(None))

    assert hass.data["lovelace"].resources.async_items()[0]["url"] == FRONTEND_MODULE_URL
    assert FRONTEND_DASHBOARD_URL_PATH in hass.data["lovelace"].dashboards
    assert (
        _FakeStore.saved_data["lovelace_dashboards"]["items"][0]["url_path"]
        == FRONTEND_DASHBOARD_URL_PATH
    )
    assert panels == [
        (
            "lovelace",
            {
                "frontend_url_path": FRONTEND_DASHBOARD_URL_PATH,
                "require_admin": False,
                "sidebar_title": FRONTEND_DASHBOARD_TITLE,
                "sidebar_icon": "mdi:bell-badge",
                "config": {"mode": "storage"},
            },
        )
    ]


def test_frontend_registry_updates_existing_dashboard_config(monkeypatch) -> None:
    hass = _FakeHass()
    extra_urls: list[str] = []
    existing = _FakeDashboardStore(hass, {"id": FRONTEND_DASHBOARD_URL_PATH})
    hass.data["lovelace"].dashboards[FRONTEND_DASHBOARD_URL_PATH] = existing
    _FakeStore.saved_data = {}

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.add_extra_js_url",
        lambda hass, url: extra_urls.append(url),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.Store",
        _FakeStore,
    )

    import asyncio

    payload = {"title": FRONTEND_DASHBOARD_TITLE, "views": [{"title": "Обзор"}]}
    asyncio.run(
        HeraldFrontendRegistration(
            hass,
            dashboard_factory=lambda: payload,
        ).async_register()
    )

    assert FRONTEND_MODULE_URL in extra_urls
    assert existing.saved == payload
    assert (
        _FakeStore.saved_data["lovelace_dashboards"]["items"][0]["url_path"]
        == FRONTEND_DASHBOARD_URL_PATH
    )


def test_frontend_registry_uses_sidebar_visibility_getter(monkeypatch) -> None:
    hass = _FakeHass()
    _FakeStore.saved_data = {}

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.Store",
        _FakeStore,
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.lovelace_dashboard.LovelaceStorage",
        _FakeDashboardStore,
    )

    import asyncio

    asyncio.run(
        HeraldFrontendRegistration(
            hass,
            dashboard_factory=lambda: {"title": FRONTEND_DASHBOARD_TITLE, "views": [{"title": "Herald"}]},
            sidebar_visible_getter=lambda: False,
        ).async_register()
    )

    assert _FakeStore.saved_data["lovelace_dashboards"]["items"][0]["show_in_sidebar"] is False


def test_frontend_registry_updates_sidebar_visibility(monkeypatch) -> None:
    hass = _FakeHass()
    _FakeStore.saved_data = {
        "lovelace_dashboards": {
            "items": [
                {
                    "id": FRONTEND_DASHBOARD_URL_PATH,
                    "mode": "storage",
                    "title": FRONTEND_DASHBOARD_TITLE,
                    "url_path": FRONTEND_DASHBOARD_URL_PATH,
                    "icon": "mdi:bell-badge",
                    "show_in_sidebar": True,
                    "require_admin": False,
                }
            ]
        }
    }
    panel = {"show_in_sidebar": True}
    hass.data["frontend_panels"][FRONTEND_DASHBOARD_URL_PATH] = panel

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.Store",
        _FakeStore,
    )

    import asyncio

    registration = HeraldFrontendRegistration(hass)
    asyncio.run(registration.async_set_sidebar_visibility(False))

    assert _FakeStore.saved_data["lovelace_dashboards"]["items"][0]["show_in_sidebar"] is False
    assert panel["show_in_sidebar"] is False


def test_frontend_registry_updates_storage_dashboard_before_runtime_materializes(monkeypatch) -> None:
    hass = _FakeHass()
    extra_urls: list[str] = []
    panels: list[tuple[str, dict]] = []
    _FakeStore.saved_data = {
        "lovelace_dashboards": {
            "items": [
                {
                    "id": FRONTEND_DASHBOARD_URL_PATH,
                    "mode": "storage",
                    "title": FRONTEND_DASHBOARD_TITLE,
                    "url_path": FRONTEND_DASHBOARD_URL_PATH,
                    "icon": "mdi:bell-badge",
                    "show_in_sidebar": True,
                    "require_admin": False,
                }
            ]
        }
    }
    hass.data["frontend_panels"][FRONTEND_DASHBOARD_URL_PATH] = object()

    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.add_extra_js_url",
        lambda hass, url: extra_urls.append(url),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.frontend.async_register_built_in_panel",
        lambda hass, component_name, **kwargs: panels.append((component_name, kwargs)),
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.lovelace_dashboard.LovelaceStorage",
        _FakeDashboardStore,
    )
    monkeypatch.setattr(
        "custom_components.herald.frontend_registry.Store",
        _FakeStore,
    )

    import asyncio

    payload = {"title": FRONTEND_DASHBOARD_TITLE, "views": [{"title": "Обзор"}]}
    asyncio.run(
        HeraldFrontendRegistration(
            hass,
            dashboard_factory=lambda: payload,
        ).async_register()
    )

    assert FRONTEND_MODULE_URL in extra_urls
    assert FRONTEND_DASHBOARD_URL_PATH in hass.data["lovelace"].dashboards
    assert hass.data["lovelace"].dashboards[FRONTEND_DASHBOARD_URL_PATH].saved == payload
    assert panels == []
