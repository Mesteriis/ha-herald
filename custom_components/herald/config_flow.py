"""Config flow for Herald."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_END,
    CONF_FLOWS,
    CONF_HOST,
    CONF_MODEL,
    CONF_NAME,
    CONF_OLLAMA,
    CONF_PERSONALITIES,
    CONF_QUIET_HOURS,
    CONF_START,
    CONF_SUMMARY_PERSONALITY,
    DEFAULT_FLOWS,
    DEFAULT_NAME,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_PERSONALITIES,
    DEFAULT_QUIET_HOURS_END,
    DEFAULT_QUIET_HOURS_START,
    DOMAIN,
)


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
        if user_input is not None:
            flow_overrides: dict[str, dict[str, Any]] = {}
            for flow_name in flow_names:
                summary_personality = str(
                    user_input.get(f"summary_personality__{flow_name}", "")
                ).strip()
                if summary_personality:
                    flow_overrides[flow_name] = {
                        CONF_SUMMARY_PERSONALITY: summary_personality,
                    }
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
                    CONF_FLOWS: flow_overrides,
                },
            )

        quiet = dict(self._entry.options.get(CONF_QUIET_HOURS, self._entry.data.get(CONF_QUIET_HOURS, {})))
        ollama = dict(self._entry.options.get(CONF_OLLAMA, self._entry.data.get(CONF_OLLAMA, {})))
        current_flows = dict(self._entry.data.get(CONF_FLOWS, {}))
        current_flows.update(dict(self._entry.options.get(CONF_FLOWS, {})))
        schema_fields: dict[Any, Any] = {
            vol.Required(CONF_HOST, default=ollama.get(CONF_HOST, DEFAULT_OLLAMA_HOST)): str,
            vol.Required(CONF_MODEL, default=ollama.get(CONF_MODEL, DEFAULT_OLLAMA_MODEL)): str,
            vol.Required(CONF_START, default=quiet.get(CONF_START, DEFAULT_QUIET_HOURS_START)): str,
            vol.Required(CONF_END, default=quiet.get(CONF_END, DEFAULT_QUIET_HOURS_END)): str,
        }
        for flow_name in flow_names:
            flow_config = dict(DEFAULT_FLOWS.get(flow_name, {}))
            flow_config.update(dict(current_flows.get(flow_name, {})))
            schema_fields[
                vol.Optional(
                    f"summary_personality__{flow_name}",
                    default=flow_config.get(CONF_SUMMARY_PERSONALITY, ""),
                )
            ] = vol.In(personality_options)
        schema = vol.Schema(schema_fields)
        return self.async_show_form(step_id="init", data_schema=schema)
