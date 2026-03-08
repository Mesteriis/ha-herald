"""Frontend resource registration for Herald Lovelace card."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from homeassistant.components import frontend
from homeassistant.components.frontend import DATA_PANELS, add_extra_js_url
from homeassistant.components.lovelace import dashboard as lovelace_dashboard
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store

from .const import (
    FRONTEND_BASE_URL,
    FRONTEND_DASHBOARD_ICON,
    FRONTEND_DASHBOARD_TITLE,
    FRONTEND_DASHBOARD_URL_PATH,
    FRONTEND_DIR,
    FRONTEND_MODULE_URL,
)

_LOGGER = logging.getLogger(__name__)
_LOVELACE_DASHBOARDS_STORAGE_KEY = "lovelace_dashboards"
_LOVELACE_DASHBOARDS_STORAGE_VERSION = 1

try:
    from homeassistant.components.lovelace.const import LOVELACE_DATA as _LOVELACE_DATA_KEY
except ImportError:
    _LOVELACE_DATA_KEY = None


class HeraldFrontendRegistration:
    """Register Herald frontend resources for the Lovelace editor and dashboards."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        dashboard_factory: Callable[[], dict[str, Any]] | None = None,
        sidebar_visible_getter: Callable[[], bool] | None = None,
    ) -> None:
        self.hass = hass
        self._dashboard_factory = dashboard_factory
        self._sidebar_visible_getter = sidebar_visible_getter
        self._lovelace = None
        self._retry_unsub: Callable[[], None] | None = None

    async def async_register(self) -> None:
        """Expose the JS bundle and load it into the frontend."""
        await self._async_register_static_path()
        add_extra_js_url(self.hass, FRONTEND_MODULE_URL)
        await self._async_register_lovelace_artifacts()

    async def _async_register_lovelace_artifacts(self) -> None:
        """Register Lovelace resource and dashboard when Lovelace runtime is available."""
        if self._resolve_lovelace() is None:
            self._async_schedule_retry()
            return

        resource_ready = await self._async_register_lovelace_resource()
        dashboard_ready = await self._async_register_storage_dashboard()
        if resource_ready and dashboard_ready and self._retry_unsub is not None:
            self._retry_unsub()
            self._retry_unsub = None
            return
        if not resource_ready or not dashboard_ready:
            self._async_schedule_retry()

    async def _async_register_static_path(self) -> None:
        """Serve the bundled frontend assets under a stable URL."""
        frontend_dir = Path(__file__).resolve().parent / FRONTEND_DIR
        if not frontend_dir.exists():
            _LOGGER.debug("Herald frontend directory does not exist: %s", frontend_dir)
            return
        try:
            register_many = getattr(self.hass.http, "async_register_static_paths", None)
            if callable(register_many):
                from homeassistant.components.http import StaticPathConfig

                await register_many(
                    [StaticPathConfig(FRONTEND_BASE_URL, str(frontend_dir), cache_headers=False)]
                )
            else:
                self.hass.http.register_static_path(
                    FRONTEND_BASE_URL,
                    str(frontend_dir),
                    cache_headers=False,
                )
        except RuntimeError:
            _LOGGER.debug("Herald static path already registered: %s", FRONTEND_BASE_URL)

    async def _async_register_lovelace_resource(self) -> bool:
        """Create a Lovelace module resource entry when dashboards are storage-backed."""
        if not self._lovelace or self._lovelace_mode() != "storage":
            return False

        @callback
        async def _check_resources_loaded(_: Any) -> None:
            self._resolve_lovelace()
            resources = self._lovelace_value("resources")
            if resources is None:
                self._async_schedule_retry()
                return
            if await self._async_ensure_resource(resources):
                return
            loaded = getattr(resources, "loaded", None)
            if loaded is False:
                self._async_schedule_retry()
            return

        await _check_resources_loaded(None)
        resources = self._lovelace_value("resources")
        if resources is None:
            return False
        try:
            return any(
                FRONTEND_MODULE_URL in str(resource.get("url", ""))
                for resource in resources.async_items()
            )
        except Exception:  # noqa: BLE001
            return False

    async def _async_ensure_resource(self, resources: Any) -> bool:
        """Ensure the Herald card module exists in Lovelace resources."""
        if getattr(resources, "loaded", None) is False and hasattr(resources, "async_get_info"):
            try:
                await resources.async_get_info()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Failed to load Lovelace resources before registration: %s", err)
        try:
            existing = resources.async_items()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to enumerate Lovelace resources: %s", err)
            return False

        for resource in existing:
            if FRONTEND_MODULE_URL in str(resource.get("url", "")):
                return True

        try:
            await resources.async_create_item({"res_type": "module", "url": FRONTEND_MODULE_URL})
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Could not auto-register Herald Lovelace resource %s: %s",
                FRONTEND_MODULE_URL,
                err,
            )
            return False
        return True

    async def _async_register_storage_dashboard(self) -> bool:
        """Create a storage-backed Herald Control Center when Lovelace uses storage mode."""
        if (
            self._dashboard_factory is None
            or not self._lovelace
            or self._lovelace_mode() != "storage"
        ):
            return False

        dashboards = self._lovelace_value("dashboards")
        if not isinstance(dashboards, dict):
            return False

        dashboard_item = {
            "id": FRONTEND_DASHBOARD_URL_PATH,
            "mode": "storage",
            "title": FRONTEND_DASHBOARD_TITLE,
            "url_path": FRONTEND_DASHBOARD_URL_PATH,
            "icon": FRONTEND_DASHBOARD_ICON,
            "show_in_sidebar": self._sidebar_visible(),
            "require_admin": False,
        }
        dashboard_config = self._dashboard_factory()
        existing = dashboards.get(FRONTEND_DASHBOARD_URL_PATH)
        if existing is not None:
            await self._async_upsert_dashboard_registry(dashboard_item)
            await existing.async_save(dashboard_config)
            return True

        if await self._async_dashboard_exists_in_registry(FRONTEND_DASHBOARD_URL_PATH):
            await self._async_upsert_dashboard_registry(dashboard_item)
            dashboard_store = lovelace_dashboard.LovelaceStorage(self.hass, dashboard_item)
            await dashboard_store.async_save(dashboard_config)
            dashboards[FRONTEND_DASHBOARD_URL_PATH] = dashboard_store
            return True

        panels = self.hass.data.get(DATA_PANELS, {})
        if FRONTEND_DASHBOARD_URL_PATH in panels:
            _LOGGER.warning(
                "Cannot auto-register Herald dashboard at %s because the URL path is already in use",
                FRONTEND_DASHBOARD_URL_PATH,
            )
            return False

        await self._async_upsert_dashboard_registry(dashboard_item)
        dashboard_store = lovelace_dashboard.LovelaceStorage(self.hass, dashboard_item)
        await dashboard_store.async_save(dashboard_config)
        dashboards[FRONTEND_DASHBOARD_URL_PATH] = dashboard_store
        panel_kwargs: dict[str, Any] = {
            "frontend_url_path": FRONTEND_DASHBOARD_URL_PATH,
            "require_admin": False,
            "sidebar_title": FRONTEND_DASHBOARD_TITLE,
            "sidebar_icon": FRONTEND_DASHBOARD_ICON,
            "config": {"mode": "storage"},
        }
        if "show_in_sidebar" in inspect.signature(frontend.async_register_built_in_panel).parameters:
            panel_kwargs["show_in_sidebar"] = self._sidebar_visible()
        frontend.async_register_built_in_panel(
            self.hass,
            "lovelace",
            **panel_kwargs,
        )
        return True

    async def async_set_sidebar_visibility(self, visible: bool) -> None:
        """Update the Herald dashboard sidebar visibility in Lovelace storage/runtime."""
        self._resolve_lovelace()
        await self._async_update_dashboard_registry_visibility(visible)
        panels = self.hass.data.get(DATA_PANELS, {})
        panel = panels.get(FRONTEND_DASHBOARD_URL_PATH)
        if panel is None:
            return
        if isinstance(panel, dict):
            panel["show_in_sidebar"] = visible
            return
        if hasattr(panel, "show_in_sidebar"):
            try:
                setattr(panel, "show_in_sidebar", visible)
            except Exception:  # noqa: BLE001
                return

    async def _async_upsert_dashboard_registry(self, item: dict[str, Any]) -> None:
        """Persist one storage dashboard entry into the Lovelace dashboards registry."""
        store: Store[dict[str, Any]] = Store(
            self.hass,
            _LOVELACE_DASHBOARDS_STORAGE_VERSION,
            _LOVELACE_DASHBOARDS_STORAGE_KEY,
        )
        data = await store.async_load() or {"items": []}
        items = [entry for entry in data.get("items", []) if entry.get("id") != item["id"]]
        items.append(item)
        await store.async_save({"items": items})

    async def _async_update_dashboard_registry_visibility(self, visible: bool) -> None:
        """Update only the show_in_sidebar flag in the Lovelace dashboards registry."""
        store: Store[dict[str, Any]] = Store(
            self.hass,
            _LOVELACE_DASHBOARDS_STORAGE_VERSION,
            _LOVELACE_DASHBOARDS_STORAGE_KEY,
        )
        data = await store.async_load() or {"items": []}
        changed = False
        items: list[dict[str, Any]] = []
        for entry in data.get("items", []):
            payload = dict(entry)
            if payload.get("id") == FRONTEND_DASHBOARD_URL_PATH:
                payload["show_in_sidebar"] = visible
                changed = True
            items.append(payload)
        if changed:
            await store.async_save({"items": items})

    async def _async_dashboard_exists_in_registry(self, dashboard_id: str) -> bool:
        """Return True when the dashboard already exists in Lovelace storage registry."""
        store: Store[dict[str, Any]] = Store(
            self.hass,
            _LOVELACE_DASHBOARDS_STORAGE_VERSION,
            _LOVELACE_DASHBOARDS_STORAGE_KEY,
        )
        data = await store.async_load() or {"items": []}
        return any(entry.get("id") == dashboard_id for entry in data.get("items", []))

    def _lovelace_mode(self) -> str | None:
        """Return the Lovelace storage mode across old and new HA APIs."""
        return self._lovelace_value("resource_mode") or self._lovelace_value("mode")

    def _lovelace_value(self, key: str) -> Any:
        """Read a Lovelace runtime field from either a dict or a dataclass-like object."""
        if self._lovelace is None:
            return None
        if isinstance(self._lovelace, dict):
            return self._lovelace.get(key)
        return getattr(self._lovelace, key, None)

    def _resolve_lovelace(self) -> Any:
        """Resolve Lovelace runtime from old or new HA storage."""
        self._lovelace = self.hass.data.get("lovelace")
        if self._lovelace is None and _LOVELACE_DATA_KEY is not None:
            self._lovelace = self.hass.data.get(_LOVELACE_DATA_KEY)
        return self._lovelace

    def _sidebar_visible(self) -> bool:
        """Return the desired sidebar visibility for the Herald dashboard."""
        if self._sidebar_visible_getter is None:
            return True
        try:
            return bool(self._sidebar_visible_getter())
        except Exception:  # noqa: BLE001
            return True

    @callback
    def _async_schedule_retry(self) -> None:
        """Retry Lovelace registration on cold start until runtime is ready."""
        if self._retry_unsub is not None:
            return

        @callback
        async def _retry(_: Any) -> None:
            self._retry_unsub = None
            await self._async_register_lovelace_artifacts()

        self._retry_unsub = async_call_later(self.hass, 5, _retry)
