"""
File: test_debug_storage.py
Path: tests/modules/debug/test_debug_storage.py
Role: Tests for debugger storage safety primitives.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/debug_storage.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

import debug_storage  # noqa: E402


def test_resolve_under_rejects_dot_segments_and_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "safe").mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)

    assert debug_storage.resolve_under(root, "safe/file.txt") == root.resolve() / "safe" / "file.txt"
    with pytest.raises(debug_storage.DebugStorageError):
        debug_storage.resolve_under(root, "../outside/file.txt")
    with pytest.raises(debug_storage.DebugStorageError):
        debug_storage.resolve_under(root, "link/file.txt")


def test_campaign_lock_is_atomic(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    with debug_storage.CampaignLock(campaign):
        assert (campaign / ".lock" / "owner.json").is_file()
        with pytest.raises(debug_storage.DebugStorageError):
            with debug_storage.CampaignLock(campaign):
                pass
    assert not (campaign / ".lock").exists()


def test_atomic_json_and_append_jsonl(tmp_path: Path) -> None:
    target = tmp_path / "data" / "index.json"
    debug_storage.atomic_write_json(target, {"schema_version": "1", "value": 1})
    assert json.loads(target.read_text(encoding="utf-8"))["value"] == 1

    events = tmp_path / "data" / "events.jsonl"
    debug_storage.append_jsonl(events, {"schema_version": "1", "event": "note_appended"})
    rows, errors = debug_storage.read_jsonl(events)
    assert errors == []
    assert rows[0]["event"] == "note_appended"
