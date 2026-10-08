"""Static notification discovery without Home Assistant or template execution."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from custom_components.herald.notification_policies import NotificationPolicyManager, snapshot_registry_states


def _write(root: Path, name: str, value: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    return path


def test_scan_static_calls_in_main_scripts_packages_and_structural_includes(tmp_path: Path) -> None:
    _write(tmp_path, "configuration.yaml", """
automation: !include includes/events.yml
script:
  main:
    sequence:
      - action: herald.notify
        data: {event: main_script, message: test}
homeassistant:
  packages: !include_dir_named packages
unrelated_password: !secret synthetic_password
""")
    _write(tmp_path, "includes/events.yml", """
- id: included
  action:
    - choose:
        - conditions: []
          sequence:
            - service: herald.notify
              data: {event: included_event, message: test, channels: [mobile_test]}
""")
    _write(tmp_path, "scripts.yaml", """
script_test:
  sequence:
    - action: herald.notify
      data: {event: script_event, message: test}
""")
    _write(tmp_path, "packages/laundry.yml", """
automation:
  - actions:
      - action: herald.notify
        data: {event: package_event, message: test}
""")
    manager = NotificationPolicyManager(tmp_path)
    registry = manager.scan(channels={}, states={})
    assert set(registry) == {"main_script", "included_event", "script_event", "package_event"}
    assert registry["included_event"]["default_channels"] == ["mobile_test"]
    assert registry["included_event"]["source_files"] == ["includes/events.yml"]
    assert manager.scan_issues == []


def test_scan_never_reads_secret_or_outside_include_targets(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path, "configuration.yaml", """
automation: !include secrets.yaml
script: !include ../outside.yaml
template: !include alias.yaml
automation extra: !include secret_alias.yaml
password: !secret token
""")
    outside = _write(tmp_path.parent, "outside.yaml", "action: herald.notify\ndata: {event: should_not_read}")
    (tmp_path / "alias.yaml").symlink_to(outside)
    secrets = _write(tmp_path, "secrets.yaml", "token: should_not_read")
    (tmp_path / "secret_alias.yaml").symlink_to(secrets)
    opened = []
    original = Path.open

    def recording_open(path, *args, **kwargs):
        opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", recording_open)
    manager = NotificationPolicyManager(tmp_path)
    assert manager.scan(channels={}, states={}) == {}
    assert opened == [tmp_path / "configuration.yaml"]
    assert any(issue["reason"] == "unsafe_include" for issue in manager.scan_issues)
    assert "should_not_read" not in str(manager.scan_issues)


def test_dynamic_key_is_reported_without_inventing_a_policy(tmp_path: Path) -> None:
    _write(tmp_path, "automations.yaml", """
- actions:
    - action: herald.notify
      data: {event: "{{ states('sensor.event') }}", message: test}
    - service: herald.notify
      data: {event: static_event, message: "{{ secret_message }}", channels: "{{ selected_channels }}"}
""")
    manager = NotificationPolicyManager(tmp_path)
    registry = manager.scan(channels={}, states={})
    assert set(registry) == {"static_event"}
    assert registry["static_event"]["default_channels"] == []
    assert registry["static_event"]["defaults_dynamic"] is True
    assert {issue["reason"] for issue in manager.scan_issues} == {"dynamic_notification_key", "dynamic_route_defaults"}


def test_duplicate_events_merge_sources_without_guessing_route_defaults(tmp_path: Path) -> None:
    _write(tmp_path, "automations/first.yaml", "action: herald.notify\ndata: {event: repeated, channels: [mobile_test]}")
    _write(tmp_path, "scripts/second.yml", "action: herald.notify\ndata: {event: repeated, channels: [dashboard]}")
    manager = NotificationPolicyManager(tmp_path)
    entry = manager.scan(channels={}, states={})["repeated"]
    assert entry["source_count"] == 2
    assert entry["default_channels"] == []
    assert entry["defaults_ambiguous"] is True


def test_include_cycles_and_yaml_alias_cycles_are_bounded(tmp_path: Path) -> None:
    _write(tmp_path, "configuration.yaml", "automation: !include events.yaml")
    _write(tmp_path, "events.yaml", """
sequence: !include configuration.yaml
loop: &loop {again: *loop}
action: herald.notify
data: {event: cycle_event, message: test}
""")
    assert set(NotificationPolicyManager(tmp_path).scan(channels={}, states={})) == {"cycle_event"}


def test_selected_event_route_uses_snapshot_fields_with_action_syntax(tmp_path: Path) -> None:
    _write(tmp_path, "automations/selected.yml", """
- id: selected_alert_delivery
  variables:
    selected_state: "{{ states('sensor.test_selected') }}"
  action:
    - action: herald.notify
      data:
        event: "{{ selected_state }}"
        message: test
        channels: [dashboard]
""")
    _write(tmp_path, "templates/test.yml", """
- sensor:
    - unique_id: test_selected
      state: "{{ 'washer_finished' if is_state('binary_sensor.test', 'on') else 'idle' }}"
      attributes:
        label: "{{ 'done' if this.state == 'washer_finished' else 'idle' }}"
""")
    manager = NotificationPolicyManager(tmp_path)
    registry = manager.scan(channels={}, states={
        "sensor.test_selected": {"state": "washer_finished", "attributes": {"title_ru": "Fixture title"}},
    })
    assert set(registry) == {"washer_finished"}
    assert registry["washer_finished"]["active"] is True
    assert registry["washer_finished"]["selected_title_ru"] == "Fixture title"


def test_snapshot_copies_only_needed_values_and_is_detached() -> None:
    attributes = {"title_ru": "Fixture", "state_ru": "Ready", "unneeded_private": "not copied"}
    state = SimpleNamespace(entity_id="sensor.test", state="ready", attributes=attributes)
    hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: [state]))
    snapshot = snapshot_registry_states(hass)
    attributes["title_ru"] = "Changed"
    assert snapshot == {"sensor.test": {"state": "ready", "attributes": {"title_ru": "Fixture", "state_ru": "Ready"}}}


def test_parse_failures_are_explicit_without_payload_contents(tmp_path: Path) -> None:
    _write(tmp_path, "automations.yaml", "broken: [synthetic_private_value")
    manager = NotificationPolicyManager(tmp_path)
    assert manager.scan(channels={}, states={}) == {}
    assert manager.scan_issues == [{"file": "automations.yaml", "reason": "unreadable_yaml"}]


def test_named_package_and_nested_action_includes(tmp_path: Path) -> None:
    _write(tmp_path, "configuration.yaml", "homeassistant:\n  packages:\n    fixture: !include custom/package.yml")
    _write(tmp_path, "custom/package.yml", "automation:\n  - actions: !include actions.yml")
    _write(tmp_path, "custom/actions.yml", "- action: herald.notify\n  data: {event: nested_include}")
    manager = NotificationPolicyManager(tmp_path)
    assert set(manager.scan(channels={}, states={})) == {"nested_include"}
    assert manager.scan_issues == []


def test_service_data_examples_are_not_discovered_as_executable_calls(tmp_path: Path) -> None:
    _write(tmp_path, "automations.yaml", """
- action: herald.notify
  data:
    event: real_event
    message: test
    metadata:
      example:
        service: herald.notify
        data: {event: not_an_action}
""")
    assert set(NotificationPolicyManager(tmp_path).scan(channels={}, states={})) == {"real_event"}
