"""Rule constraints remain explicit, fail closed, and never expand audiences."""

from copy import deepcopy

import pytest
import voluptuous as vol

from custom_components.herald.models import NotificationContext, PresenceSnapshot
from custom_components.herald.notification_policies import NotificationPolicyManager, NotificationPolicyOverride
from custom_components.herald.policy_editor import merge_policy
from custom_components.herald.policy_rules import apply_rule, has_rule_constraints
from custom_components.herald.services import PREVIEW_NOTIFICATION_POLICY_SCHEMA, SET_NOTIFICATION_POLICY_SCHEMA


def _context(**changes):
    return NotificationContext(**{
        "flow": "system_events", "title": "Title", "message": "Message", "level": "info",
        "source": "test", "timestamp": "2026-09-30T12:00:00+00:00", **changes,
    })


def test_legacy_missing_fields_inherit_without_changing_empty_audience():
    policy = NotificationPolicyOverride.from_dict({"notes": "old stored policy"}).to_dict()
    assert policy["users"] is None
    assert policy["target_room"] is None
    assert policy["presence"] == "any"
    assert policy["quiet_hours"] == "inherit"
    assert not has_rule_constraints(policy)
    context = _context(user="alice", room="kitchen")
    before = deepcopy(context.to_dict())
    assert apply_rule(context, policy, PresenceSnapshot(quiet_hours=True)) is None
    assert context.to_dict() == before


def test_partial_edits_preserve_constraints_and_explicit_resets_are_distinct():
    current = {"users": ["Alice", "person.alice", "person.retired"], "target_room": "Гостиная",
               "presence": "someone_home", "quiet_hours": "mute", "notes": "old"}
    edited = merge_policy(current, {"notes": "changed"}, {}).to_dict()
    assert edited["users"] == ["person.alice", "person.retired"]
    assert edited["target_room"] == "living_room"
    assert edited["presence"] == "someone_home"
    assert edited["quiet_hours"] == "mute"
    assert current["users"] == ["Alice", "person.alice", "person.retired"]
    empty = merge_policy(edited, {"users": []}, {}).to_dict()
    assert empty["users"] == []
    reset = merge_policy(empty, {"users": None, "target_room": None, "presence": "any", "quiet_hours": "inherit"}, {}).to_dict()
    assert not has_rule_constraints(reset)
    assert reset["notes"] == "changed"


def test_effective_and_stored_policies_expose_same_constraints(tmp_path):
    manager = NotificationPolicyManager(tmp_path)
    overrides = {"test": {"users": ["alice"], "target_room": "Кухня", "presence": "nobody_home", "quiet_hours": "text_only"}}
    effective = manager.effective_policy(notification_key="test", overrides=overrides, channels={})
    entry = manager.effective_registry(registry={"test": {"notification_key": "test"}}, overrides=overrides, channels={})[0]
    for field in ("users", "target_room", "presence", "quiet_hours"):
        assert effective[field] == entry["policy"][field] == entry["effective"][field]
    assert effective["users"] == ["person.alice"]
    assert effective["target_room"] == "kitchen"
    entry["policy"]["users"].append("person.bob")
    assert entry["effective"]["users"] == ["person.alice"]
    assert overrides["test"]["users"] == ["alice"]


@pytest.mark.parametrize("users", [None, [], ["Alice", "person.bob"]])
def test_set_and_preview_schemas_share_normalized_user_values(users):
    draft = {"users": users, "target_room": " living room ", "presence": "someone_home", "quiet_hours": "mute"}
    saved = SET_NOTIFICATION_POLICY_SCHEMA({"notification_key": "test", **draft})
    preview = PREVIEW_NOTIFICATION_POLICY_SCHEMA({"notification_key": "test", "policy": draft})["policy"]
    assert {key: saved[key] for key in draft} == preview
    assert preview["users"] == (None if users is None else ["person.alice", "person.bob"] if users else [])
    assert preview["target_room"] == "living_room"


@pytest.mark.parametrize("draft", [
    {"users": "alice"}, {"users": [""]}, {"users": ["sensor.alice"]}, {"users": ["alice,bob"]}, {"users": [None]},
    {"target_room": "   "}, {"target_room": 5}, {"presence": "unknown"}, {"presence": None},
    {"quiet_hours": "unknown"}, {"quiet_hours": None},
])
def test_set_and_preview_reject_identical_invalid_rule_values(draft):
    with pytest.raises(vol.Invalid):
        SET_NOTIFICATION_POLICY_SCHEMA({"notification_key": "test", **draft})
    with pytest.raises(vol.Invalid):
        PREVIEW_NOTIFICATION_POLICY_SCHEMA({"notification_key": "test", "policy": draft})


def test_alias_intersection_never_resurrects_silent_or_explicitly_excluded_user():
    context = _context(users=["alice", "person.bob"], user="charlie")
    policy = {"users": ["person.alice", "charlie"]}
    catalogs = {"known_users": ["alice", "bob", "person.charlie"]}
    before = deepcopy(policy)
    snapshot = PresenceSnapshot(people_home=["person.charlie"])
    assert apply_rule(context, policy, snapshot, **catalogs) is None
    assert context.users == ["person.alice"]
    assert context.user == "person.alice"
    assert context.metadata["audience_resolved"]
    assert context.metadata["policy_users_explicit"]
    assert apply_rule(context, policy, snapshot, **catalogs) is None
    assert context.users == ["person.alice"]
    context.users.clear()  # A current silent toggle removes the last recipient.
    assert apply_rule(context, policy, snapshot, **catalogs) == "notification_policy_no_recipients"
    assert context.user is None
    assert context.users == []
    assert policy == before
    assert snapshot.people_home == ["person.charlie"]


@pytest.mark.parametrize("users", [[], ["bob"]])
def test_empty_intersection_blocks_even_forced_requests(users):
    context = _context(users=["person.alice"], user="alice", force=True)
    assert apply_rule(context, {"users": users}, PresenceSnapshot(), known_users=["alice", "bob"]) == "notification_policy_no_recipients"
    assert context.users == []
    assert context.user is None
    assert context.metadata["audience_resolved"]


def test_mixed_known_and_unknown_user_selection_is_preserved_and_blocks_all():
    policy = merge_policy(None, {"users": ["alice", "removed_user"]}, {}).to_dict()
    context = _context(users=["person.alice"])
    assert apply_rule(context, policy, PresenceSnapshot(), known_users=["alice"]) == "policy_unknown_user"
    assert policy["users"] == ["person.alice", "person.removed_user"]


def test_room_alias_is_an_explicit_target_and_unknown_room_is_not_inheritance():
    policy = merge_policy(None, {"target_room": "Гостиная"}, {}).to_dict()
    context = _context(room="bedroom")
    assert apply_rule(context, policy, PresenceSnapshot(), known_rooms=["living_room", "bedroom"]) is None
    assert context.room == "living_room"
    assert context.metadata["policy_target_room"] == "living_room"
    assert apply_rule(context, policy, PresenceSnapshot(), known_rooms=["bedroom"]) == "policy_unknown_room"
    assert policy["target_room"] == "living_room"


def test_missing_catalogs_fail_closed_except_already_verified_context_values():
    assert apply_rule(_context(), {"users": ["alice"]}, PresenceSnapshot()) == "policy_unknown_user"
    assert apply_rule(_context(), {"target_room": "office"}, PresenceSnapshot()) == "policy_unknown_room"
    context = _context(users=["alice"], room="Кухня")
    assert apply_rule(context, {"users": ["person.alice"], "target_room": "kitchen"}, PresenceSnapshot()) is None
    # Explicit empty catalogs must not trigger the compatibility fallback.
    assert apply_rule(context, {"users": ["alice"]}, PresenceSnapshot(), known_users=[]) == "policy_unknown_user"
    assert apply_rule(context, {"target_room": "kitchen"}, PresenceSnapshot(), known_rooms=[]) == "policy_unknown_room"


@pytest.mark.parametrize(("rule", "nobody_home", "reason"), [
    ("someone_home", True, "policy_someone_home"), ("someone_home", False, None),
    ("nobody_home", False, "policy_nobody_home"), ("nobody_home", True, None),
    ("any", True, None),
])
def test_presence_rules_recheck_current_snapshot_without_force_bypass(rule, nobody_home, reason):
    context = _context(force=True)
    assert apply_rule(context, {"presence": rule}, PresenceSnapshot(nobody_home=nobody_home)) == reason


def test_quiet_hours_mute_and_text_only_refresh_from_current_snapshot_even_with_force():
    context = _context(force=True, channels=["voice", "phone"])
    assert apply_rule(context, {"quiet_hours": "mute"}, PresenceSnapshot(quiet_hours=True)) == "policy_quiet_hours"
    assert apply_rule(context, {"quiet_hours": "mute"}, PresenceSnapshot(quiet_hours=False)) is None
    assert apply_rule(context, {"quiet_hours": "text_only"}, PresenceSnapshot(quiet_hours=True)) is None
    assert context.metadata["policy_text_only"] is True
    assert context.channels == ["voice", "phone"]  # Router applies transport restrictions.
    assert apply_rule(context, {"quiet_hours": "text_only"}, PresenceSnapshot(quiet_hours=False)) is None
    assert "policy_text_only" not in context.metadata


@pytest.mark.parametrize("invalid", [{"presence": "bad"}, {"quiet_hours": "bad"}, {"target_room": ""}])
def test_malformed_stored_constraints_do_not_become_unrestricted(invalid):
    policy = NotificationPolicyOverride.from_dict(invalid).to_dict()
    assert has_rule_constraints(policy)
    assert apply_rule(_context(), policy, PresenceSnapshot()) is not None


def test_empty_restrictive_channel_mode_survives_rule_edits(tmp_path):
    policy = merge_policy({"delivery_mode": "custom", "channels": ["missing"]}, {"quiet_hours": "text_only"}, {}).to_dict()
    effective = NotificationPolicyManager(tmp_path).effective_policy(notification_key="test", overrides={"test": policy}, channels={}, inherited_channels=["fallback"])
    assert effective["channels"] == []
    assert effective["delivery_mode"] == "custom"
    context = _context(channels=[], metadata={"channels_explicit": True})
    assert apply_rule(context, effective, PresenceSnapshot(quiet_hours=True)) is None
    assert context.channels == []
    assert context.metadata["channels_explicit"]
