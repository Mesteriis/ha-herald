"""Minimal Home Assistant stubs for standalone Herald unit tests."""

from __future__ import annotations

import enum
import re
import sys
import types
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import voluptuous as vol

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class _FlowHandler:
    hass = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_show_menu(self, **kwargs):
        return {"type": "menu", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}

    def _async_current_entries(self):
        return list(getattr(self, "_current_entries", []))


def _redact_data(value, keys):
    if isinstance(value, dict):
        return {key: "**REDACTED**" if key in keys else _redact_data(item, keys) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_data(item, keys) for item in value]
    return value


homeassistant = types.ModuleType("homeassistant")
config_entries = types.ModuleType("homeassistant.config_entries")
config_entries.SOURCE_IMPORT = "import"
config_entries.ConfigEntry = object
config_entries.ConfigFlow = _FlowHandler
config_entries.OptionsFlow = _FlowHandler
core = types.ModuleType("homeassistant.core")
core.HomeAssistant = object
core.Event = object
core.callback = lambda func: func
helpers = types.ModuleType("homeassistant.helpers")
helpers_config_validation = types.ModuleType("homeassistant.helpers.config_validation")
helpers_config_validation.string = vol.Coerce(str)
helpers_config_validation.boolean = vol.Boolean()
helpers_service = types.ModuleType("homeassistant.helpers.service")
helpers_service.async_register_admin_service = lambda hass, domain, service, handler, **kwargs: hass.services.async_register(
    domain, service, handler, **kwargs
)
helpers_typing = types.ModuleType("homeassistant.helpers.typing")
helpers_typing.ConfigType = dict
helpers_typing.StateType = object
helpers_aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
helpers_dispatcher = types.ModuleType("homeassistant.helpers.dispatcher")
helpers_entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
helpers_event = types.ModuleType("homeassistant.helpers.event")
helpers_storage = types.ModuleType("homeassistant.helpers.storage")
helpers_selector = types.ModuleType("homeassistant.helpers.selector")
helpers.selector = helpers_selector


class TextSelectorType:
    PASSWORD = "password"


class TextSelectorConfig(dict):
    def __init__(self, *, type):
        super().__init__(type=type)


class TextSelector:
    def __init__(self, config):
        self.config = config

    def __call__(self, value):
        if not isinstance(value, str):
            raise vol.Invalid("expected string")
        return value


helpers_selector.TextSelector = TextSelector
helpers_selector.TextSelectorConfig = TextSelectorConfig
helpers_selector.TextSelectorType = TextSelectorType
helpers_update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")
components = types.ModuleType("homeassistant.components")
components_diagnostics = types.ModuleType("homeassistant.components.diagnostics")
components_diagnostics.async_redact_data = _redact_data
components_button = types.ModuleType("homeassistant.components.button")
components_binary_sensor = types.ModuleType("homeassistant.components.binary_sensor")
components_frontend = types.ModuleType("homeassistant.components.frontend")
components_http = types.ModuleType("homeassistant.components.http")
components_lovelace = types.ModuleType("homeassistant.components.lovelace")
components_lovelace_dashboard = types.ModuleType("homeassistant.components.lovelace.dashboard")
components_lovelace_resources = types.ModuleType("homeassistant.components.lovelace.resources")
components_number = types.ModuleType("homeassistant.components.number")
components_select = types.ModuleType("homeassistant.components.select")
components_sensor = types.ModuleType("homeassistant.components.sensor")
components_switch = types.ModuleType("homeassistant.components.switch")
const = types.ModuleType("homeassistant.const")
util = types.ModuleType("homeassistant.util")
util_dt = types.ModuleType("homeassistant.util.dt")
helpers_entity = types.ModuleType("homeassistant.helpers.entity")
helpers_entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")
helpers_device_registry = types.ModuleType("homeassistant.helpers.device_registry")
helpers_area_registry = types.ModuleType("homeassistant.helpers.area_registry")

try:
    BaseStrEnum = enum.StrEnum
except AttributeError:
    class BaseStrEnum(str, enum.Enum):
        pass


class Platform(BaseStrEnum):
    SENSOR = "sensor"


const.Platform = Platform
helpers_aiohttp_client.async_get_clientsession = lambda hass: None
helpers_dispatcher.async_dispatcher_connect = lambda hass, signal, callback: (lambda: None)
helpers_dispatcher.async_dispatcher_send = lambda hass, signal, *args: None
helpers_entity_platform.AddEntitiesCallback = object
helpers_event.async_call_later = lambda hass, delay, action: None
helpers_event.async_track_state_change_event = lambda hass, entities, callback: (lambda: None)
components_frontend.add_extra_js_url = lambda hass, url: None
components_frontend.async_register_built_in_panel = lambda hass, component_name, **kwargs: None
components_frontend.DATA_PANELS = "frontend_panels"


class StaticPathConfig:
    def __init__(self, url_path, path, cache_headers=False) -> None:
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers


components_http.StaticPathConfig = StaticPathConfig
components_lovelace_resources.ResourceStorageCollection = object
components_lovelace_dashboard.LovelaceStorage = object


class Store:
    def __init__(self, *args, **kwargs) -> None:
        self.data = None

    def __class_getitem__(cls, item):
        return cls

    async def async_load(self):
        return self.data

    async def async_save(self, value):
        self.data = value


class DataUpdateCoordinator:
    def __init__(self, hass, logger, name="", config_entry=None) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.config_entry = config_entry
        self.data = {}

    def __class_getitem__(cls, item):
        return cls

    async def async_request_refresh(self):
        return None

    async def async_shutdown(self):
        return None

    def async_set_updated_data(self, data):
        self.data = data


class CoordinatorEntity:
    def __init__(self, coordinator, context=None) -> None:
        self.coordinator = coordinator
        self.hass = getattr(coordinator, "hass", None)

    async def async_added_to_hass(self):
        return None

    def async_on_remove(self, func) -> None:
        return None

    def async_write_ha_state(self) -> None:
        return None

    def _handle_coordinator_update(self) -> None:
        return None


class _Entity:
    pass


class NumberMode:
    BOX = "box"


@dataclass(kw_only=True)
class SensorEntityDescription:
    key: str | None = None
    icon: str | None = None
    entity_category: str | None = None


class EntityCategory:
    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


helpers_storage.Store = Store
helpers_update_coordinator.CoordinatorEntity = CoordinatorEntity
helpers_update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
components_binary_sensor.BinarySensorEntity = _Entity
components_button.ButtonEntity = _Entity
components_number.NumberEntity = _Entity
components_number.NumberMode = NumberMode
components_select.SelectEntity = _Entity
components_sensor.SensorEntity = _Entity
components_sensor.SensorEntityDescription = SensorEntityDescription
components_switch.SwitchEntity = _Entity
helpers_entity.EntityCategory = EntityCategory
helpers_entity_registry.async_get = lambda hass: None
helpers_device_registry.async_get = lambda hass: None
helpers_area_registry.async_get = lambda hass: None
util.slugify = lambda value: re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")
util_dt.now = lambda: datetime.now(timezone.utc)
util.dt = util_dt

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.helpers.selector", helpers_selector)
sys.modules.setdefault("homeassistant.components", components)
sys.modules.setdefault("homeassistant.components.diagnostics", components_diagnostics)
sys.modules.setdefault("homeassistant.components.button", components_button)
sys.modules.setdefault("homeassistant.components.binary_sensor", components_binary_sensor)
sys.modules.setdefault("homeassistant.components.frontend", components_frontend)
sys.modules.setdefault("homeassistant.components.http", components_http)
sys.modules.setdefault("homeassistant.components.lovelace", components_lovelace)
sys.modules.setdefault("homeassistant.components.lovelace.dashboard", components_lovelace_dashboard)
sys.modules.setdefault("homeassistant.components.lovelace.resources", components_lovelace_resources)
sys.modules.setdefault("homeassistant.components.number", components_number)
sys.modules.setdefault("homeassistant.components.select", components_select)
sys.modules.setdefault("homeassistant.components.sensor", components_sensor)
sys.modules.setdefault("homeassistant.components.switch", components_switch)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
sys.modules.setdefault("homeassistant.helpers.config_validation", helpers_config_validation)
sys.modules.setdefault("homeassistant.helpers.service", helpers_service)
sys.modules.setdefault("homeassistant.helpers.aiohttp_client", helpers_aiohttp_client)
sys.modules.setdefault("homeassistant.helpers.dispatcher", helpers_dispatcher)
sys.modules.setdefault("homeassistant.helpers.entity", helpers_entity)
sys.modules.setdefault("homeassistant.helpers.entity_registry", helpers_entity_registry)
sys.modules.setdefault("homeassistant.helpers.device_registry", helpers_device_registry)
sys.modules.setdefault("homeassistant.helpers.area_registry", helpers_area_registry)
sys.modules.setdefault("homeassistant.helpers.entity_platform", helpers_entity_platform)
sys.modules.setdefault("homeassistant.helpers.event", helpers_event)
sys.modules.setdefault("homeassistant.helpers.storage", helpers_storage)
sys.modules.setdefault("homeassistant.helpers.typing", helpers_typing)
sys.modules.setdefault("homeassistant.helpers.update_coordinator", helpers_update_coordinator)
sys.modules.setdefault("homeassistant.const", const)
sys.modules.setdefault("homeassistant.util", util)
sys.modules.setdefault("homeassistant.util.dt", util_dt)
