"""
File: test_debug_validation.py
Path: tests/modules/debug/test_debug_validation.py
Role: Tests for debugger campaign validation failure modes.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/debug_campaign.py
 - .ai_infra/install/agent_colony/debug_storage.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

import debug_campaign  # noqa: E402
import debug_storage  # noqa: E402


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".ai_infra" / "templates").mkdir(parents=True)
    shutil.copytree(
        REPO_ROOT / ".ai_infra" / "templates" / "debug-campaign",
        root / ".ai_infra" / "templates" / "debug-campaign",
    )
    return root


def test_validation_detects_partial_jsonl_and_part_file(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="broken", mode="incident", item_id="PVTI_test")
    (camp / "vault" / "logs" / "events.jsonl").write_text('{"schema_version":"1"', encoding="utf-8")
    run_dir = camp / "vault" / "logs" / "by-run" / "run-000001"
    run_dir.mkdir()
    (run_dir / "stdout.log.part").write_text("partial", encoding="utf-8")
    errors = debug_campaign.structural_validate(root, "broken")
    assert any("partial" in error for error in errors)
    assert any("incomplete capture" in error for error in errors)


def test_validation_detects_event_index_divergence(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="diverge", mode="incident", item_id="PVTI_test")
    debug_storage.append_jsonl(
        camp / "vault" / "logs" / "events.jsonl",
        {
            "schema_version": "1",
            "event": "capture_finished",
            "timestamp": "2026-01-01T00:00:00Z",
            "run_id": "run-000001",
        },
    )
    errors = debug_campaign.structural_validate(root, "diverge")
    assert any("runs_used" in error for error in errors)


def test_validation_blocks_closed_with_active_probe(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="probe", mode="incident", item_id="PVTI_test")
    probes = {
        "schema_version": "1",
        "probes": [
            {
                "schema_version": "1",
                "id": "P1",
                "status": "active",
                "path": "src/app.py",
                "note": "",
                "created_at": "now",
                "updated_at": "now",
            }
        ],
    }
    debug_storage.atomic_write_json(camp / "vault" / "probes" / "index.json", probes)
    index = json.loads((camp / "INDEX.json").read_text(encoding="utf-8"))
    index["status"] = "closed"
    debug_storage.atomic_write_json(camp / "INDEX.json", index)
    errors = debug_campaign.structural_validate(root, "probe")
    assert any("active probes" in error for error in errors)
