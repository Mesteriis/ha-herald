"""Config flow for Herald."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AI_API_KEY,
    CONF_AI_PROVIDER,
    CONF_CHANNELS,
    CONF_END,
    CONF_FLOWS,
    CONF_HOST,
    CONF_MAINTENANCE_MODE_ENTITY,
    CONF_MODEL,
    CONF_NAME,
    CONF_OLLAMA,
    CONF_PERSONALITIES,
    CONF_QUIET_HOURS,
    CONF_START,
    DEFAULT_CHANNEL_MIN_LEVEL,
    DEFAULT_NAME,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_PERSONALITIES,
    DEFAULT_QUIET_HOURS_END,
    DEFAULT_QUIET_HOURS_START,
    DOMAIN,
)
from .discovery import async_discover_runtime_channels
from .effective_config import (
    async_options_config,
    edited_options,
    options_field_bindings,
    options_form_values,
    set_path,
)

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
_CLEARABLE_OPTION_FIELDS = {CONF_MAINTENANCE_MODE_ENTITY, "summary_personality"}


def _quiet_hours_errors(user_input: dict[str, Any] | None) -> dict[str, str]:
    """Require the HH:MM representation used by the presence policy."""
    if user_input is None:
        return {}
    return {
        key: "invalid_time"
        for key in (CONF_START, CONF_END)
        if not isinstance(user_input.get(key), str)
        or re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", user_input[key]) is None
    }


def _options_schema(values: dict[str, Any], validators: dict[str, Any]) -> vol.Schema:
    """Show optional current values while treating omitted blank inputs as clears.

    HA initializes fields from suggested_value, then omits empty strings on submit.
    A nonempty schema default would silently restore the value the user cleared.
    """
    return vol.Schema({
        (vol.Optional(key, default="", description={"suggested_value": value})
         if key in _CLEARABLE_OPTION_FIELDS
         else vol.Required(key, default=value)): validators[key]
        for key, value in values.items()
    })


def _ai_errors(values: dict[str, Any]) -> dict[str, str]:
    if values.get(CONF_AI_PROVIDER) != "openai":
        return {}
    try:
        url = urlsplit(values[CONF_HOST].strip())
        valid = (url.scheme == "https" and bool(url.hostname) and not url.username
                 and not url.password and not url.query and not url.fragment
                 and url.path.rstrip("/") in ("", "/v1"))
    except ValueError:
        valid = False
    return {} if valid else {CONF_HOST: "invalid_host"}


class HeraldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Herald."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle UI setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = _quiet_hours_errors(user_input)
        if user_input is not None and not errors:
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

        values = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
                vol.Required(CONF_HOST, default=values.get(CONF_HOST, DEFAULT_OLLAMA_HOST)): str,
                vol.Required(CONF_MODEL, default=values.get(CONF_MODEL, DEFAULT_OLLAMA_MODEL)): str,
                vol.Required(CONF_START, default=values.get(CONF_START, DEFAULT_QUIET_HOURS_START)): str,
                vol.Required(CONF_END, default=values.get(CONF_END, DEFAULT_QUIET_HOURS_END)): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, import_config: dict[str, Any]):
        """Handle YAML import."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        quiet = import_config.get(CONF_QUIET_HOURS, {})
        if not isinstance(quiet, dict) or _quiet_hours_errors({
            CONF_START: quiet.get(CONF_START, DEFAULT_QUIET_HOURS_START),
            CONF_END: quiet.get(CONF_END, DEFAULT_QUIET_HOURS_END),
        }):
            return self.async_abort(reason="invalid_quiet_hours")
        return self.async_create_entry(
            title=import_config.get(CONF_NAME, DEFAULT_NAME),
            data=import_config,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HeraldOptionsFlow(config_entry)


class HeraldOptionsFlow(config_entries.OptionsFlow):
    """Edit one small section while preserving all unrelated settings."""

    def __init__(self, entry) -> None:
        self._entry = entry
        self._form_key: str | None = None
        self._displayed_values: dict[str, Any] = {}
        self._displayed_bindings: dict[str, Any] = {}
        self._selected_channel: str | None = None
        self._selected_flow: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Show navigation without loading settings or discovering devices."""
        self._form_key = None
        self._selected_channel = None
        self._selected_flow = None
        return self.async_show_menu(
            step_id="init",
            menu_options=["quiet_hours", "ai", "channel_select", "flow_select", "maintenance"],
        )

    async def _async_current_config(self, *, discover_channels: bool = False) -> dict[str, Any]:
        current = await async_options_config(self.hass, self._entry)
        if discover_channels and self.hass is not None:
            discovered = await async_discover_runtime_channels(self.hass)
            channels = dict(current.get(CONF_CHANNELS, {}))
            for name, payload in discovered.items():
                channels.setdefault(name, payload)
            current[CONF_CHANNELS] = channels
        return current

    async def async_step_quiet_hours(self, user_input: dict[str, Any] | None = None):
        return await self._async_section(
            "quiet_hours", {CONF_START: CONF_START, CONF_END: CONF_END},
            {CONF_START: str, CONF_END: str}, user_input,
        )

    async def async_step_ai(self, user_input: dict[str, Any] | None = None):
        return await self._async_section(
            "ai", {CONF_AI_PROVIDER: CONF_AI_PROVIDER, CONF_HOST: CONF_HOST, CONF_MODEL: CONF_MODEL},
            {CONF_AI_PROVIDER: vol.In(("ollama", "openai")), CONF_HOST: str, CONF_MODEL: str},
            user_input, secret_field=CONF_AI_API_KEY,
        )

    async def async_step_maintenance(self, user_input: dict[str, Any] | None = None):
        return await self._async_section(
            "maintenance",
            {CONF_MAINTENANCE_MODE_ENTITY: CONF_MAINTENANCE_MODE_ENTITY},
            {CONF_MAINTENANCE_MODE_ENTITY: str},
            user_input,
        )

    async def async_step_channel_select(self, user_input: dict[str, Any] | None = None):
        current = await self._async_current_config(discover_channels=True)
        names = sorted(current.get(CONF_CHANNELS, {}))
        if not names:
            return self.async_abort(reason="no_channels")
        if user_input is not None and set(user_input) == {"channel"} and user_input["channel"] in names:
            self._selected_channel = user_input["channel"]
            return await self.async_step_channel()
        return self.async_show_form(
            step_id="channel_select",
            data_schema=vol.Schema({vol.Required("channel"): vol.In(names)}),
            errors={"base": "invalid_selection"} if user_input is not None else {},
        )

    async def async_step_channel(self, user_input: dict[str, Any] | None = None):
        current = await self._async_current_config(discover_channels=True)
        name = self._selected_channel
        if name is None or name not in current.get(CONF_CHANNELS, {}):
            return self.async_abort(reason="channel_unavailable")
        return await self._async_section(
            "channel", {"enabled": f"channel_enabled__{name}", "min_level": f"channel_min_level__{name}"},
            {"enabled": bool, "min_level": vol.In(LEVEL_OPTIONS)}, user_input,
            current=current, target=name, placeholders={"channel_name": name},
        )

    async def async_step_flow_select(self, user_input: dict[str, Any] | None = None):
        current = await self._async_current_config()
        names = sorted(current.get(CONF_FLOWS, {}))
        if not names:
            return self.async_abort(reason="no_flows")
        if user_input is not None and set(user_input) == {"flow"} and user_input["flow"] in names:
            self._selected_flow = user_input["flow"]
            return await self.async_step_flow()
        return self.async_show_form(
            step_id="flow_select",
            data_schema=vol.Schema({vol.Required("flow"): vol.In(names)}),
            errors={"base": "invalid_selection"} if user_input is not None else {},
        )

    async def async_step_flow(self, user_input: dict[str, Any] | None = None):
        current = await self._async_current_config()
        name = self._selected_flow
        if name is None or name not in current.get(CONF_FLOWS, {}):
            return self.async_abort(reason="flow_unavailable")
        personality_key = f"summary_personality__{name}"
        # Keep an existing custom persona selectable even if its definition is offline.
        personalities = {"", *DEFAULT_PERSONALITIES, *current.get(CONF_PERSONALITIES, {})}
        for value in (current[CONF_FLOWS][name].get("summary_personality"), self._displayed_values.get(personality_key)):
            if isinstance(value, str):
                personalities.add(value)
        fields = {key: f"{key}__{name}" for key in ("summary_personality", "cooldown_seconds", "dedup_window_seconds")}
        validators = {
            "summary_personality": vol.In(sorted(personalities)),
            "cooldown_seconds": vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
            "dedup_window_seconds": vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
        }
        return await self._async_section(
            "flow", fields, validators, user_input, current=current,
            target=name, placeholders={"flow_name": name},
        )

    async def _async_section(
        self, step_id: str, fields: dict[str, str], validators: dict[str, Any],
        user_input: dict[str, Any] | None, *, current: dict[str, Any] | None = None,
        target: str = "", placeholders: dict[str, str] | None = None,
        secret_field: str | None = None,
    ):
        """Translate a small form into the existing sparse, revisioned option patch."""
        if current is None:
            current = await self._async_current_config()
        form_key = f"{step_id}:{target}"
        if user_input is None or self._form_key != form_key:
            values = options_form_values(current)
            bindings = options_field_bindings(current)
            self._displayed_values = {field: values[field] for field in fields.values()}
            for alias, fallback in (("enabled", True), ("min_level", DEFAULT_CHANNEL_MIN_LEVEL)):
                if alias in fields and self._displayed_values[fields[alias]] is None:
                    self._displayed_values[fields[alias]] = fallback
            self._displayed_bindings = {field: bindings[field] for field in fields.values()}
            self._form_key = form_key
        defaults = {}
        for alias, field in fields.items():
            value = self._displayed_values[field]
            if value is None and alias == "enabled":
                value = True
            elif value is None and alias == "min_level":
                value = DEFAULT_CHANNEL_MIN_LEVEL
            elif value is None:
                value = ""
            defaults[alias] = value
        schema = _options_schema(defaults, validators)
        if secret_field:
            schema = schema.extend({vol.Optional(secret_field, default=""): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            )})
        errors = {}
        if user_input is not None:
            try:
                submitted = schema(user_input)
            except vol.Invalid as error:
                field = str(error.path[0]) if error.path and error.path[0] in (*fields, secret_field) else "base"
                errors[field] = "invalid_value"
            else:
                errors = _quiet_hours_errors(submitted) if step_id == "quiet_hours" else _ai_errors(submitted) if step_id == "ai" else {}
                if not errors:
                    updated = edited_options(
                        self._entry.options, self._displayed_values,
                        {fields[key]: value for key, value in submitted.items() if key in fields},
                        self._displayed_bindings,
                    )
                    if secret_field and (new_secret := submitted.get(secret_field, "").strip()):
                        set_path(updated, (CONF_OLLAMA, secret_field), new_secret)
                    return self.async_create_entry(
                        title="", data=updated,
                    )
            # Retry shows the submitted values, while comparison keeps the original snapshot.
            defaults.update({key: value for key, value in user_input.items() if key in fields})
            for key in _CLEARABLE_OPTION_FIELDS & fields.keys():
                if key not in user_input:
                    defaults[key] = ""
            schema = _options_schema(defaults, validators)
            if secret_field:
                schema = schema.extend({vol.Optional(secret_field, default=""): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                )})
        return self.async_show_form(
            step_id=step_id, data_schema=schema, errors=errors, description_placeholders=placeholders,
        )
