"""Tests for Herald helper bootstrap storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.herald.helpers import HeraldHelperManager


class _FakeConfig:
    def __init__(self, root: Path) -> None:
        self._root = root

    def path(self, value: str) -> str:
        return str(self._root / value)


class _FakeHass:
    def __init__(self, root: Path) -> None:
        self.config = _FakeConfig(root)

    async def async_add_executor_job(self, func, *args):
        return func(*args)


@pytest.mark.asyncio
async def test_helper_manager_bootstraps_storage_files(tmp_path: Path) -> None:
    manager = HeraldHelperManager(_FakeHass(tmp_path))

    bootstrap = await manager.async_ensure_helpers(
        room_names=["living_room", "bedroom"],
        user_slugs=["aleksandr_meshcheriakov"],
        character_options=["hestia", "domovoy"],
    )

    assert "input_boolean.herald_channel_voice" in bootstrap.input_booleans
    assert "input_select.herald_user_aleksandr_meshcheriakov_language" in bootstrap.input_selects

    input_boolean = json.loads((tmp_path / ".storage/input_boolean").read_text(encoding="utf-8"))
    input_select = json.loads((tmp_path / ".storage/input_select").read_text(encoding="utf-8"))

    assert any(item["id"] == "herald_room_living_room_presence" for item in input_boolean["data"]["items"])
    assert any(item["id"] == "herald_user_aleksandr_meshcheriakov_character" for item in input_select["data"]["items"])
