"""Minimal Home Assistant stubs for standalone Herald unit tests."""

from __future__ import annotations

import enum
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

homeassistant = types.ModuleType("homeassistant")
config_entries = types.ModuleType("homeassistant.config_entries")
config_entries.SOURCE_IMPORT = "import"
config_entries.ConfigEntry = object
core = types.ModuleType("homeassistant.core")
core.HomeAssistant = object
helpers = types.ModuleType("homeassistant.helpers")
helpers_typing = types.ModuleType("homeassistant.helpers.typing")
helpers_typing.ConfigType = dict
const = types.ModuleType("homeassistant.const")

try:
    BaseStrEnum = enum.StrEnum
except AttributeError:
    class BaseStrEnum(str, enum.Enum):
        pass


class Platform(BaseStrEnum):
    SENSOR = "sensor"


const.Platform = Platform

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
sys.modules.setdefault("homeassistant.helpers.typing", helpers_typing)
sys.modules.setdefault("homeassistant.const", const)
