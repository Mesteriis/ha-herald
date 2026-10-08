"""Real HA Options, update-listener and Store contracts without external services."""

from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from types import MappingProxyType, SimpleNamespace
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.data_entry_flow import FlowManagerIndexView
from homeassistant.helpers.storage import Store

from custom_components.herald import _async_update_options, _merge_config
from custom_components.herald.config_flow import HeraldConfigFlow
from custom_components.herald.const import DATA_COORDINATORS, DOMAIN, STORAGE_KEY, STORAGE_VERSION
from custom_components.herald.controls import HeraldControlManager
from custom_components.herald.effective_config import OPTIONS_CONTROL_UPDATES
from custom_components.herald.models import HeraldConfig, RuntimeState


class EffectiveOptionsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.temporary.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.entry = ConfigEntry(
            version=1, minor_version=1, domain=DOMAIN, title="Herald", source="user",
            unique_id="synthetic", discovery_keys=MappingProxyType({}), subentries_data=None,
            state=ConfigEntryState.NOT_LOADED,
            data={"channels": {"phone": {"type": "mobile_app", "service": "notify.mobile_app_synthetic"}}, "ollama": {"enabled": False}},
            options={"router": {"recent_limit": 17}},
        )
        with patch.object(self.hass.config_entries, "async_setup", new=AsyncMock(return_value=True)):
            await self.hass.config_entries.async_add(self.entry)
        self.state = RuntimeState(current_day="2026-09-30")
        self.config = HeraldConfig.from_raw(_merge_config(self.entry.data, self.entry.options))
        self.controls = self.make_controls(self.state, self.config)
        self.controls.ensure_defaults()
        self.store = Store(self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.entry.entry_id}")

        async def apply_options(options):
            if self.controls.apply_option_updates(options):
                self.controls.sync_runtime_config()
                await self.store.async_save(self.state.to_dict())

        self.hass.data[DOMAIN] = {DATA_COORDINATORS: {self.entry.entry_id: SimpleNamespace(config=self.config, controls=self.controls, async_apply_option_control_updates=apply_options)}}
        self.entry.add_update_listener(_async_update_options)

    def make_controls(self, state, config):
        presence = SimpleNamespace(room_sensors=lambda: {})
        characters = SimpleNamespace(list_character_keys=lambda: ["hestia"], get=lambda name: SimpleNamespace(key="hestia"))
        return HeraldControlManager(self.hass, config, presence, characters, lambda: state, config_layers_getter=lambda: {"entry": self.entry.data, "options": self.entry.options})

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        self.temporary.cleanup()

    async def test_real_form_edit_listener_store_and_later_runtime_change(self):
        self.controls.set_value("channel_min_level:phone", "warning")
        manager = self.hass.config_entries.options
        with patch("custom_components.herald.config_flow.async_discover_runtime_channels", new=AsyncMock(return_value={})):
            menu = await self.start_options()
            flow_id = menu["flow_id"]
            selection = await manager.async_configure(flow_id, {"next_step_id": "channel_select"})
            self.assertEqual(selection["step_id"], "channel_select")
            form = await manager.async_configure(flow_id, {"channel": "phone"})
            self.assertEqual(form["description_placeholders"], {"channel_name": "phone"})
            values = {marker.schema: marker.default() for marker in form["data_schema"].schema}
            self.assertEqual(values, {"enabled": True, "min_level": "warning"})
            values["min_level"] = "security"
            with patch.object(self.hass.config_entries, "async_reload", new=AsyncMock(return_value=True)) as reload_entry:
                result = await manager.async_configure(flow_id, values)
                await self.hass.async_block_till_done()
                reload_entry.assert_awaited_once_with(self.entry.entry_id)
        self.assertEqual(result["data"]["channels"], {"phone": {"min_level": "security"}})
        self.assertEqual(result["data"]["router"], {"recent_limit": 17})
        self.assertIn(OPTIONS_CONTROL_UPDATES, result["data"])
        self.assertEqual(dict(self.entry.options), result["data"])
        self.assertEqual(self.controls.value("channel_min_level:phone"), "security")
        saved = await Store(self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.entry.entry_id}").async_load()
        self.assertEqual(saved["control_metadata"]["channel_min_level:phone"]["source"], "options")

        self.controls.set_value("channel_min_level:phone", "notice")
        await self.store.async_save(self.state.to_dict())
        restored = RuntimeState.from_dict(await Store(self.hass, STORAGE_VERSION, f"{STORAGE_KEY}.{self.entry.entry_id}").async_load())
        config = HeraldConfig.from_raw(_merge_config(self.entry.data, self.entry.options))
        controls = self.make_controls(restored, config)
        self.assertFalse(controls.apply_option_updates(self.entry.options))
        controls.ensure_defaults()
        self.assertEqual(config.channels["phone"].min_level, "notice")
        self.assertEqual(controls.effective_settings()["channel_min_level:phone"]["source"], "runtime")

    async def start_options(self):
        with patch("homeassistant.config_entries._async_get_flow_handler", new=AsyncMock(return_value=HeraldConfigFlow)):
            return await self.hass.config_entries.options.async_init(self.entry.entry_id)

    async def test_native_menu_serializes_and_cancel_does_not_load_or_save_settings(self):
        before = deepcopy(dict(self.entry.options))
        with (
            patch("custom_components.herald.config_flow.async_options_config", new=AsyncMock(side_effect=AssertionError("menu must not read settings"))),
            patch("custom_components.herald.config_flow.async_discover_runtime_channels", new=AsyncMock(side_effect=AssertionError("menu must not discover"))),
            patch.object(self.store, "async_save", new=AsyncMock()) as save,
        ):
            menu = await self.start_options()
            self.assertEqual(menu["type"], "menu")
            self.assertEqual(menu["menu_options"], ["quiet_hours", "ai", "channel_select", "flow_select", "maintenance"])
            serialized = FlowManagerIndexView(self.hass.config_entries.options)._prepare_result_json(menu)
            self.assertEqual(serialized["data_schema"][0]["name"], "next_step_id")
            self.hass.config_entries.options.async_abort(menu["flow_id"])
            save.assert_not_awaited()
        self.assertEqual(dict(self.entry.options), before)

    async def test_native_quiet_hours_invalid_retry_preserves_other_settings(self):
        manager = self.hass.config_entries.options
        menu = await self.start_options()
        flow_id = menu["flow_id"]
        with patch("custom_components.herald.config_flow.async_discover_runtime_channels", new=AsyncMock(side_effect=AssertionError("not a channel form"))):
            form = await manager.async_configure(flow_id, {"next_step_id": "quiet_hours"})
            self.assertEqual({field.schema for field in form["data_schema"].schema}, {"start", "end"})
            retry = await manager.async_configure(flow_id, {"start": "25:00", "end": "07:15"})
            self.assertEqual(retry["errors"], {"start": "invalid_time"})
            self.assertNotIn("quiet_hours", self.entry.options)
            defaults = {field.schema: field.default() for field in retry["data_schema"].schema}
            self.assertEqual(defaults, {"start": "25:00", "end": "07:15"})
            with patch.object(self.hass.config_entries, "async_reload", new=AsyncMock(return_value=True)):
                result = await manager.async_configure(flow_id, {"start": "23:30", "end": "07:15"})
                await self.hass.async_block_till_done()
            self.assertEqual(result["data"], {"router": {"recent_limit": 17}, "quiet_hours": {"start": "23:30", "end": "07:15"}})

    async def test_native_ai_section_preserves_parallel_runtime_and_option_edits(self):
        manager = self.hass.config_entries.options
        menu = await self.start_options()
        flow_id = menu["flow_id"]
        with patch("custom_components.herald.config_flow.async_discover_runtime_channels", new=AsyncMock(side_effect=AssertionError("not a channel form"))):
            form = await manager.async_configure(flow_id, {"next_step_id": "ai"})
            values = {field.schema: field.default() for field in form["data_schema"].schema}
            self.assertEqual(set(values), {"provider", "host", "model", "api_key"})
            values["model"] = "synthetic-model"
            self.controls.set_value("channel_min_level:phone", "critical")
            with patch.object(self.hass.config_entries, "async_reload", new=AsyncMock(return_value=True)):
                self.hass.config_entries.async_update_entry(self.entry, options={"router": {"recent_limit": 31}})
                await self.hass.async_block_till_done()
                result = await manager.async_configure(flow_id, values)
                await self.hass.async_block_till_done()
            self.assertEqual(result["data"], {"router": {"recent_limit": 31}, "ollama": {"model": "synthetic-model"}})
            self.assertEqual(self.controls.value("channel_min_level:phone"), "critical")
            self.assertFalse(_merge_config(self.entry.data, result["data"])["ollama"]["enabled"])

    async def test_native_sections_serialize_compact_static_fields(self):
        manager = self.hass.config_entries.options
        view = FlowManagerIndexView(manager)
        cases = {
            "quiet_hours": (None, {"start", "end"}),
            "ai": (None, {"provider", "host", "model", "api_key"}),
            "maintenance": (None, {"maintenance_mode_entity"}),
            "channel_select": ({"channel": "phone"}, {"enabled", "min_level"}),
            "flow_select": ({"flow": "system_events"}, {"summary_personality", "cooldown_seconds", "dedup_window_seconds"}),
        }
        with patch("custom_components.herald.config_flow.async_discover_runtime_channels", new=AsyncMock(return_value={})):
            for section, (selection, expected_fields) in cases.items():
                with self.subTest(section=section):
                    menu = await self.start_options()
                    flow_id = menu["flow_id"]
                    form = await manager.async_configure(flow_id, {"next_step_id": section})
                    if selection is not None:
                        form = await manager.async_configure(flow_id, selection)
                    fields = view._prepare_result_json(form)["data_schema"]
                    self.assertEqual({field["name"] for field in fields}, expected_fields)
                    self.assertLessEqual(len(fields), 4)
                    self.hass.config_entries.options.async_abort(flow_id)
        self.assertEqual(dict(self.entry.options), {"router": {"recent_limit": 17}})

    async def test_native_optional_fields_can_be_cleared_by_frontend_omission(self):
        self.config.router["maintenance_mode_entity"] = "input_boolean.synthetic_maintenance"
        self.config.flows["system_events"].summary_personality = "synthetic_persona"
        manager = self.hass.config_entries.options
        view = FlowManagerIndexView(manager)
        cases = [
            ("maintenance", None, "maintenance_mode_entity", "input_boolean.synthetic_maintenance"),
            ("flow_select", {"flow": "system_events"}, "summary_personality", "synthetic_persona"),
        ]
        for section, selection, clear_field, current_value in cases:
            with self.subTest(section=section):
                menu = await self.start_options()
                flow_id = menu["flow_id"]
                form = await manager.async_configure(flow_id, {"next_step_id": section})
                if selection is not None:
                    form = await manager.async_configure(flow_id, selection)
                serialized = view._prepare_result_json(form)["data_schema"]
                field = next(item for item in serialized if item["name"] == clear_field)
                self.assertFalse(field["required"])
                self.assertEqual(field["default"], "")
                self.assertEqual(field["description"]["suggested_value"], current_value)
                submitted = {marker.schema: (marker.description or {}).get("suggested_value", marker.default()) for marker in form["data_schema"].schema}
                # Native HA initializes suggested values, then omits cleared strings on POST.
                submitted.pop(clear_field)
                with patch.object(self.hass.config_entries, "async_reload", new=AsyncMock(return_value=True)):
                    result = await manager.async_configure(flow_id, submitted)
                    await self.hass.async_block_till_done()
                if clear_field == "maintenance_mode_entity":
                    self.assertEqual(result["data"]["router"][clear_field], "")
                else:
                    self.assertIsNone(result["data"]["flows"]["system_events"][clear_field])
