"""Config flow for Herald."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_CHANNELS,
    CONF_COOLDOWN,
    CONF_DEDUP_WINDOW,
    CONF_ENABLED,
    CONF_END,
    CONF_FLOWS,
    CONF_HOST,
    CONF_MAINTENANCE_MIN_LEVEL,
    CONF_MAINTENANCE_MODE_ENTITY,
    CONF_MIN_LEVEL,
    CONF_MODEL,
    CONF_NAME,
    CONF_OLLAMA,
    CONF_PERSONALITIES,
    CONF_QUIET_HOURS,
    CONF_ROUTER,
    CONF_START,
    CONF_SUMMARY_PERSONALITY,
    DEFAULT_CHANNEL_MIN_LEVEL,
    DEFAULT_FLOW_COOLDOWN_SECONDS,
    DEFAULT_FLOW_DEDUP_WINDOW_SECONDS,
    DEFAULT_FLOWS,
    DEFAULT_MAINTENANCE_MIN_LEVEL,
    DEFAULT_MAINTENANCE_MODE_ENTITY,
    DEFAULT_NAME,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_PERSONALITIES,
    DEFAULT_QUIET_HOURS_END,
    DEFAULT_QUIET_HOURS_START,
    DOMAIN,
)
from .discovery import discover_runtime_channels

LEVEL_OPTIONS = [
    "debug",
    "info",
    "notice",
    "ai",
    "warning",
    "system",
    "critical",
    "security",
]


class HeraldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Herald."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle UI setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_OLLAMA: {
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_MODEL: user_input[CONF_MODEL],
                    },
                    CONF_QUIET_HOURS: {
                        CONF_START: user_input[CONF_START],
                        CONF_END: user_input[CONF_END],
                    },
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST, default=DEFAULT_OLLAMA_HOST): str,
                vol.Required(CONF_MODEL, default=DEFAULT_OLLAMA_MODEL): str,
                vol.Required(CONF_START, default=DEFAULT_QUIET_HOURS_START): str,
                vol.Required(CONF_END, default=DEFAULT_QUIET_HOURS_END): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, import_config: dict[str, Any]):
        """Handle YAML import."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(
            title=import_config.get(CONF_NAME, DEFAULT_NAME),
            data=import_config,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HeraldOptionsFlow(config_entry)


class HeraldOptionsFlow(config_entries.OptionsFlow):
    """Basic options flow for Herald."""

    def __init__(self, entry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage Herald options."""
        discovered_channels = discover_runtime_channels(self.hass) if self.hass else {}
        current_channels = dict(self._entry.data.get(CONF_CHANNELS, {}))
        current_channels.update(dict(self._entry.options.get(CONF_CHANNELS, {})))
        for channel_name, channel_payload in discovered_channels.items():
            current_channels.setdefault(channel_name, channel_payload)
        channel_names = sorted(current_channels)
        flow_names = sorted(
            {
                *DEFAULT_FLOWS,
                *dict(self._entry.data.get(CONF_FLOWS, {})).keys(),
                *dict(self._entry.options.get(CONF_FLOWS, {})).keys(),
            }
        )
        personality_options = [""] + sorted(
            {
                *DEFAULT_PERSONALITIES.keys(),
                *dict(self._entry.data.get(CONF_PERSONALITIES, {})).keys(),
                *dict(self._entry.options.get(CONF_PERSONALITIES, {})).keys(),
            }
        )
        current_router = dict(self._entry.data.get(CONF_ROUTER, {}))
        current_router.update(dict(self._entry.options.get(CONF_ROUTER, {})))
        current_flows = dict(self._entry.data.get(CONF_FLOWS, {}))
        current_flows.update(dict(self._entry.options.get(CONF_FLOWS, {})))
        if user_input is not None:
            flow_overrides: dict[str, dict[str, Any]] = {}
            for flow_name in flow_names:
                flow_config = dict(DEFAULT_FLOWS.get(flow_name, {}))
                flow_config.update(dict(current_flows.get(flow_name, {})))
                summary_personality = str(
                    user_input.get(f"summary_personality__{flow_name}", "")
                ).strip()
                flow_config[CONF_SUMMARY_PERSONALITY] = summary_personality or None
                flow_config[CONF_COOLDOWN] = int(
                    user_input.get(
                        f"cooldown_seconds__{flow_name}",
                        flow_config.get(CONF_COOLDOWN, DEFAULT_FLOW_COOLDOWN_SECONDS),
                    )
                )
                flow_config[CONF_DEDUP_WINDOW] = int(
                    user_input.get(
                        f"dedup_window_seconds__{flow_name}",
                        flow_config.get(CONF_DEDUP_WINDOW, DEFAULT_FLOW_DEDUP_WINDOW_SECONDS),
                    )
                )
                flow_overrides[flow_name] = flow_config
            channel_overrides: dict[str, dict[str, Any]] = {}
            for channel_name in channel_names:
                channel_config = dict(current_channels.get(channel_name, {}))
                if not channel_config:
                    continue
                channel_config[CONF_ENABLED] = bool(
                    user_input.get(
                        f"channel_enabled__{channel_name}",
                        channel_config.get(CONF_ENABLED, True),
                    )
                )
                channel_config[CONF_MIN_LEVEL] = str(
                    user_input.get(
                        f"channel_min_level__{channel_name}",
                        channel_config.get(CONF_MIN_LEVEL, DEFAULT_CHANNEL_MIN_LEVEL),
                    )
                )
                channel_overrides[channel_name] = channel_config
            return self.async_create_entry(
                title="",
                data={
                    CONF_OLLAMA: {
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_MODEL: user_input[CONF_MODEL],
                    },
                    CONF_QUIET_HOURS: {
                        CONF_START: user_input[CONF_START],
                        CONF_END: user_input[CONF_END],
                    },
                    CONF_ROUTER: {
                        CONF_MAINTENANCE_MODE_ENTITY: str(
                            user_input.get(
                                CONF_MAINTENANCE_MODE_ENTITY,
                                current_router.get(
                                    CONF_MAINTENANCE_MODE_ENTITY,
                                    DEFAULT_MAINTENANCE_MODE_ENTITY,
                                ),
                            )
                        ).strip(),
                        CONF_MAINTENANCE_MIN_LEVEL: str(
                            user_input.get(
                                CONF_MAINTENANCE_MIN_LEVEL,
                                current_router.get(
                                    CONF_MAINTENANCE_MIN_LEVEL,
                                    DEFAULT_MAINTENANCE_MIN_LEVEL,
                                ),
                            )
                        ),
                    },
                    CONF_CHANNELS: channel_overrides,
                    CONF_FLOWS: flow_overrides,
                },
            )

        quiet = dict(self._entry.options.get(CONF_QUIET_HOURS, self._entry.data.get(CONF_QUIET_HOURS, {})))
        ollama = dict(self._entry.options.get(CONF_OLLAMA, self._entry.data.get(CONF_OLLAMA, {})))
        schema_fields: dict[Any, Any] = {
            vol.Required(CONF_HOST, default=ollama.get(CONF_HOST, DEFAULT_OLLAMA_HOST)): str,
            vol.Required(CONF_MODEL, default=ollama.get(CONF_MODEL, DEFAULT_OLLAMA_MODEL)): str,
            vol.Required(CONF_START, default=quiet.get(CONF_START, DEFAULT_QUIET_HOURS_START)): str,
            vol.Required(CONF_END, default=quiet.get(CONF_END, DEFAULT_QUIET_HOURS_END)): str,
            vol.Required(
                CONF_MAINTENANCE_MODE_ENTITY,
                default=current_router.get(
                    CONF_MAINTENANCE_MODE_ENTITY,
                    DEFAULT_MAINTENANCE_MODE_ENTITY,
                ),
            ): str,
            vol.Required(
                CONF_MAINTENANCE_MIN_LEVEL,
                default=current_router.get(
                    CONF_MAINTENANCE_MIN_LEVEL,
                    DEFAULT_MAINTENANCE_MIN_LEVEL,
                ),
            ): vol.In(LEVEL_OPTIONS),
        }
        for channel_name in channel_names:
            channel_config = dict(current_channels.get(channel_name, {}))
            schema_fields[
                vol.Optional(
                    f"channel_enabled__{channel_name}",
                    default=channel_config.get(CONF_ENABLED, True),
                )
            ] = bool
            schema_fields[
                vol.Optional(
                    f"channel_min_level__{channel_name}",
                    default=channel_config.get(CONF_MIN_LEVEL, DEFAULT_CHANNEL_MIN_LEVEL),
                )
            ] = vol.In(LEVEL_OPTIONS)
        for flow_name in flow_names:
            flow_config = dict(DEFAULT_FLOWS.get(flow_name, {}))
            flow_config.update(dict(current_flows.get(flow_name, {})))
            schema_fields[
                vol.Optional(
                    f"summary_personality__{flow_name}",
                    default=flow_config.get(CONF_SUMMARY_PERSONALITY, ""),
                )
            ] = vol.In(personality_options)
            schema_fields[
                vol.Optional(
                    f"cooldown_seconds__{flow_name}",
                    default=flow_config.get(CONF_COOLDOWN, DEFAULT_FLOW_COOLDOWN_SECONDS),
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=0, max=24 * 60 * 60))
            schema_fields[
                vol.Optional(
                    f"dedup_window_seconds__{flow_name}",
                    default=flow_config.get(
                        CONF_DEDUP_WINDOW,
                        DEFAULT_FLOW_DEDUP_WINDOW_SECONDS,
                    ),
                )
            ] = vol.All(vol.Coerce(int), vol.Range(min=0, max=24 * 60 * 60))
        schema = vol.Schema(schema_fields)
        return self.async_show_form(step_id="init", data_schema=schema)
