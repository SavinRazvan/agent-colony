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


def test_closed_campaign_rejects_handed_off_without_child_card(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="handoff-gap", mode="incident", item_id="PVTI_test")
    fid = debug_campaign.finding_add(
        root,
        "handoff-gap",
        kind="DBG",
        summary="queued for implementer",
    )
    debug_campaign.update_finding(root, "handoff-gap", fid, status="handed_off")
    index = json.loads((camp / "INDEX.json").read_text(encoding="utf-8"))
    index["status"] = "closed"
    debug_storage.atomic_write_json(camp / "INDEX.json", index)
    errors = debug_campaign.structural_validate(root, "handoff-gap")
    assert any("handed_off without child_card" in error for error in errors)


def test_validate_for_board_done_requires_closed_campaign(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    debug_campaign.init_campaign(root, slug="board-done", mode="incident", item_id="PVTI_test")
    errors = debug_campaign.validate_for_board(root, "board-done", board_status="done")
    assert any("need closed" in error for error in errors)


def test_project_atomics_debug_card_checks_pack_status(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    debug_campaign.init_campaign(root, slug="vcard", mode="incident", item_id="PVTI_test")
    debug_campaign.handoff_campaign(root, "vcard")
    body = (
        "## Acceptance\n\nok\n\n## Rollback\n\nok\n\n## Notes\n\n"
        "- `.local/workflow-artifacts/debug/vcard/publish/HANDOFF.json`\n"
        "- debug validate PASS\n"
    )
    item = {
        "id": "PVTI_test",
        "status": "In review",
        "content": {"body": body, "title": "[DEBUG] forensic"},
    }
    install_dir = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
    if str(install_dir) not in sys.path:
        sys.path.insert(0, str(install_dir))
    import project_atomics as pa  # noqa: E402

    problems: list[str] = []
    warnings: list[str] = []
    pa._append_debug_artifact_checks(
        problems=problems,
        warnings=warnings,
        item=item,
        body=body,
        status="in_review",
        root=root,
    )
    assert not any("need ready_for_consumer" in problem for problem in problems)

    problems_done: list[str] = []
    pa._append_debug_artifact_checks(
        problems=problems_done,
        warnings=[],
        item=item,
        body=body,
        status="done",
        root=root,
    )
    assert any("need closed" in problem for problem in problems_done)
