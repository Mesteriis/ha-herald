"""Real Home Assistant API checks; run separately from the unit-test stubs.

python -m unittest discover -s tests_ha -v
"""
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from types import MappingProxyType, SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
from homeassistant.auth import auth_manager_from_config
from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import area_registry, device_registry, entity_registry, floor_registry, label_registry

from custom_components.herald import async_setup_entry, async_unload_entry
from custom_components.herald.const import DATA_COORDINATORS, DATA_YAML_CONFIG, DOMAIN
from custom_components.herald.diagnostics import async_get_config_entry_diagnostics
from custom_components.herald.models import HeraldConfig
from custom_components.herald.services import async_setup_services, async_unload_services


class RuntimeAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.temporary.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        device_registry.async_setup(self.hass)
        for registry in (floor_registry, label_registry, area_registry, device_registry, entity_registry):
            await registry.async_load(self.hass)
        self.hass.auth = await auth_manager_from_config(self.hass, [], [])
        self.entry = ConfigEntry(
            version=1, minor_version=1, domain=DOMAIN, title="Herald", source="user",
            unique_id="test-herald", discovery_keys=MappingProxyType({}), subentries_data=None,
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            data={"ollama": {"enabled": False, "model": "base"}},
            options={"ollama": {"model": "override"}},
        )
        self.coordinator = SimpleNamespace(
            async_handle_service_notify=AsyncMock(), async_generate_dashboard=AsyncMock(),
        )
        self.hass.data[DOMAIN] = {DATA_COORDINATORS: {self.entry.entry_id: self.coordinator}}

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        self.temporary.cleanup()

    async def test_dashboard_service_rejects_non_admin_and_allows_system_call(self):
        await async_setup_services(self.hass)
        await self.hass.auth.async_create_user("Owner")
        user = await self.hass.auth.async_create_user("Non-admin", group_ids=[])
        with self.assertRaises(Unauthorized):
            await self.hass.services.async_call(
                DOMAIN, "generate_dashboard", {}, blocking=True, context=Context(user_id=user.id),
            )
        self.coordinator.async_generate_dashboard.assert_not_awaited()
        await self.hass.services.async_call(DOMAIN, "generate_dashboard", {}, blocking=True)
        self.coordinator.async_generate_dashboard.assert_awaited_once_with(
            path="dashboards/herald_dashboard.yaml", title="Herald Control Center", preset="dashboard",
        )
        self.hass.data[DOMAIN][DATA_COORDINATORS].clear()
        await async_unload_services(self.hass)
        self.assertFalse(self.hass.services.has_service(DOMAIN, "generate_dashboard"))

    async def test_policy_preview_service_requires_response_and_never_calls_notify(self):
        self.coordinator.async_preview_notification_policy = AsyncMock(return_value={"draft": True, "explanation": {"status": "blocked"}})
        await async_setup_services(self.hass)
        result = await self.hass.services.async_call(
            DOMAIN, "preview_notification_policy", {"notification_key": "synthetic", "policy": {
                "users": ["Alice"], "target_room": "Кухня", "presence": "someone_home", "quiet_hours": "mute",
            }},
            blocking=True, return_response=True,
        )
        self.assertTrue(result["draft"])
        self.coordinator.async_handle_service_notify.assert_not_awaited()
        self.coordinator.async_preview_notification_policy.assert_awaited_once()
        policy = self.coordinator.async_preview_notification_policy.await_args.args[0]["policy"]
        self.assertEqual(policy, {"users": ["person.alice"], "target_room": "kitchen", "presence": "someone_home", "quiet_hours": "mute"})
        self.hass.data[DOMAIN][DATA_COORDINATORS].clear()
        await async_unload_services(self.hass)
        self.assertFalse(self.hass.services.has_service(DOMAIN, "preview_notification_policy"))

    async def test_notify_schema_and_handler_use_real_service_registry(self):
        await async_setup_services(self.hass)
        await self.hass.services.async_call(
            DOMAIN, "notify", {"message": "Synthetic", "channels": [], "suppress": 3600}, blocking=True,
        )
        payload = self.coordinator.async_handle_service_notify.await_args.args[0]
        self.assertEqual(payload["channels"], [])
        self.assertEqual(payload["suppress"], 3600)
        self.assertTrue(payload["immediately"])
        # Omission reaches the request parser so legacy already_humanized and
        # explicit rewrite opt-outs retain their precedence.
        self.assertNotIn("rewrite", payload)
        await self.hass.services.async_call(
            DOMAIN, "notify", {"message": "Synthetic", "rewrite": False}, blocking=True,
        )
        self.assertFalse(self.coordinator.async_handle_service_notify.await_args.args[0]["rewrite"])

    async def test_entry_lifecycle_merges_options_and_cleans_up(self):
        coordinator = SimpleNamespace(async_config_entry_first_refresh=AsyncMock(), async_shutdown=AsyncMock())
        self.hass.data[DOMAIN] = {DATA_YAML_CONFIG: {"ollama": {"host": "http://example.invalid"}}}
        with (
            patch("custom_components.herald.coordinator.HeraldCoordinator", return_value=coordinator) as factory,
            patch("custom_components.herald._async_register_frontend", new=AsyncMock()),
            patch.object(self.hass.config_entries, "async_forward_entry_setups", new=AsyncMock()),
            patch.object(self.hass.config_entries, "async_unload_platforms", new=AsyncMock(return_value=True)),
        ):
            self.assertTrue(await async_setup_entry(self.hass, self.entry))
            self.assertEqual(factory.call_args.args[2]["ollama"], {
                "host": "http://example.invalid", "enabled": False, "model": "override",
            })
            self.assertEqual(len(self.entry.update_listeners), 1)
            self.assertTrue(await async_unload_entry(self.hass, self.entry))
            coordinator.async_shutdown.assert_awaited_once()
            self.assertNotIn(self.entry.entry_id, self.hass.data[DOMAIN][DATA_COORDINATORS])
            self.assertFalse(self.hass.services.has_service(DOMAIN, "notify"))

    async def test_real_diagnostic_redactor_never_exports_provider_key_or_text(self):
        config = HeraldConfig.from_raw({"channels": {"voice": {"type": "tts_hume", "data": {"api_key": "synthetic-secret"}}}})
        config.ollama.update({"provider": "openai", "api_key": "synthetic-openai-secret"})
        self.coordinator.config = config
        self.coordinator.trace_snapshot = lambda: {"recent_notifications": [{"message": "synthetic-private-text"}]}
        self.coordinator.data = {"last_notification": {"message": "synthetic-private-text"}}
        diagnostics = await async_get_config_entry_diagnostics(self.hass, self.entry)
        serialized = json.dumps(diagnostics)
        self.assertNotIn("synthetic-secret", serialized)
        self.assertNotIn("synthetic-private-text", serialized)

    async def test_coordinator_setup_snapshot_and_shutdown_with_real_ha(self):
        from custom_components.herald.coordinator import HeraldCoordinator

        async with aiohttp.ClientSession() as session:
            with patch("custom_components.herald.coordinator.async_get_clientsession", return_value=session):
                coordinator = HeraldCoordinator(self.hass, self.entry, {"ollama": {"enabled": False}})
            self.hass.data[DOMAIN][DATA_COORDINATORS][self.entry.entry_id] = coordinator
            try:
                await coordinator.async_config_entry_first_refresh()
                self.assertTrue(coordinator.last_update_success)
                self.assertEqual(coordinator.data["queue_size"], 0)
                self.assertIn("flow_policies", coordinator.data)
                coordinator._notification_registry = {"synthetic": {
                    "notification_key": "synthetic", "preview_request": {"channels": ["persistent_default"]},
                }}
                before = deepcopy(coordinator._state.to_dict())
                preview = await coordinator.async_preview_notification_policy({
                    "notification_key": "synthetic", "policy": {"enabled": False}, "scenario": "away",
                })
                self.assertEqual(preview["explanation"]["status"], "blocked")
                self.assertTrue(preview["presence"]["nobody_home"])
                self.assertEqual(coordinator._state.to_dict(), before)
                self.assertTrue(preview["effective_settings"])
                self.hass.states.async_set("person.alice", "home", {"friendly_name": "Alice"})
                options = coordinator.notification_registry_snapshot()["user_options"]
                self.assertIn({"value": "person.alice", "label": "Alice"}, options)
                constrained = await coordinator.async_preview_notification_policy({
                    "notification_key": "synthetic", "policy": {"users": [], "quiet_hours": "mute"},
                })
                self.assertEqual(constrained["prechecks"]["blocked_reason"], "notification_policy_no_recipients")
                self.assertEqual(coordinator._state.to_dict(), before)

            finally:
                await coordinator.async_shutdown()

    async def test_configuration_check_read_only_service_and_renamed_control(self):
        from custom_components.herald.coordinator import HeraldCoordinator

        with patch.object(self.hass.config_entries, "async_setup", new=AsyncMock(return_value=True)):
            await self.hass.config_entries.async_add(self.entry)
        async with aiohttp.ClientSession() as session:
            with patch("custom_components.herald.coordinator.async_get_clientsession", return_value=session):
                coordinator = HeraldCoordinator(self.hass, self.entry, {"ollama": {"enabled": False}})
            self.hass.data[DOMAIN][DATA_COORDINATORS][self.entry.entry_id] = coordinator
            try:
                await coordinator.async_config_entry_first_refresh()
                await async_setup_services(self.hass)
                name = next(iter(coordinator.config.channels))
                spec = coordinator.controls.spec(f"channel_enabled:{name}")
                registry = entity_registry.async_get(self.hass)
                registered = registry.async_get_or_create(
                    "switch", DOMAIN, f"{self.entry.entry_id}_{spec.object_id}",
                    config_entry=self.entry, suggested_object_id="synthetic_herald_channel",
                )
                renamed = "switch.synthetic_renamed_herald_channel"
                registry.async_update_entity(registered.entity_id, new_entity_id=renamed)
                self.hass.states.async_set(renamed, "on")
                await coordinator.async_request_refresh()
                from custom_components.herald.sensor import SENSORS

                status = next(item for item in SENSORS if item.key == "status")
                self.assertEqual(coordinator.data["control_entity_ids"][spec.key], renamed)
                self.assertEqual(status.extra_fn(coordinator.data)["control_entity_ids"][spec.key], renamed)
                before = deepcopy(coordinator._state.to_dict())
                with (
                    patch.object(coordinator, "_async_refresh_runtime_sources", new=AsyncMock()) as discovery,
                    patch.object(coordinator._store, "async_save", new=AsyncMock()) as save,
                    patch.object(coordinator, "async_handle_service_notify", new=AsyncMock()) as notify,
                    patch.object(coordinator.ai_client, "async_rewrite_payload", new=AsyncMock()) as rewrite,
                    patch.object(coordinator.controls, "effective_settings", side_effect=AssertionError("must reuse safe published settings")),
                ):
                    report = await self.hass.services.async_call(DOMAIN, "configuration_check", {}, blocking=True, return_response=True)
                    channel = next(item for item in report["channels"] if item["name"] == name)
                    self.assertEqual(channel["controls"]["enabled"], renamed)
                    self.assertEqual(report["schema_version"], 1)
                    self.assertTrue(report["limitations"])
                    self.assertEqual(coordinator._state.to_dict(), before)
                    for call in (discovery, save, notify, rewrite):
                        call.assert_not_awaited()
                snapshot = coordinator._build_snapshot(coordinator.presence.snapshot())
                self.assertEqual(snapshot["configuration_check"]["summary"]["total"], len(coordinator.config.channels))
                self.hass.data[DOMAIN][DATA_COORDINATORS].clear()
                await async_unload_services(self.hass)
                self.assertFalse(self.hass.services.has_service(DOMAIN, "configuration_check"))
            finally:
                await coordinator.async_shutdown()


if __name__ == "__main__":
    unittest.main()
