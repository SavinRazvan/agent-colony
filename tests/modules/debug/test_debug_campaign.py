"""
File: test_debug_campaign.py
Path: tests/modules/debug/test_debug_campaign.py
Role: Tests for debugger campaign lifecycle helpers.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/debug_campaign.py
 - .ai_infra/templates/debug-campaign/
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

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
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    return root


def test_init_inventory_finding_handoff_validate(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="demo", mode="incident", item_id="PVTI_test")
    assert (camp / "DEBUG-BRIEF.md").is_file()
    inventory = debug_campaign.inventory_campaign(root, "demo")
    assert inventory["files"]
    finding_id = debug_campaign.finding_add(
        root,
        "demo",
        kind="DBG",
        summary="Failure appears in src/app.py",
        paths=["src/app.py"],
    )
    assert finding_id == "DBG-001"
    payload = debug_campaign.handoff_campaign(root, "demo", next_agent="implementer")
    assert payload["status"] == "ready_for_consumer"
    assert debug_campaign.structural_validate(root, "demo") == []


def test_schema_failure_is_reported(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="bad-schema", mode="incident", item_id="PVTI_test")
    data = json.loads((camp / "INDEX.json").read_text(encoding="utf-8"))
    data["schema_version"] = "2"
    (camp / "INDEX.json").write_text(json.dumps(data), encoding="utf-8")
    errors = debug_campaign.structural_validate(root, "bad-schema")
    assert any("schema_version" in error for error in errors)


def test_closed_campaign_is_immutable(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    debug_campaign.init_campaign(root, slug="closed", mode="incident", item_id="PVTI_test")
    debug_campaign.close_campaign(root, "closed")
    with pytest.raises(debug_campaign.DebugCampaignError):
        debug_campaign.finding_add(root, "closed", kind="DBG", summary="after close")


def test_close_blocked_on_open_finding(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    debug_campaign.init_campaign(root, slug="open-bug", mode="incident", item_id="PVTI_test")
    debug_campaign.finding_add(
        root,
        "open-bug",
        kind="DBG",
        summary="Needs child card before close",
    )
    with pytest.raises(debug_campaign.DebugCampaignError, match="still open"):
        debug_campaign.close_campaign(root, "open-bug")


def test_finding_add_redacts_secrets_in_campaign_write(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="redact", mode="incident", item_id="PVTI_test")
    secret = "finding-secret-canary-abcdefghijklmnopqrstuvwxyz"
    debug_campaign.finding_add(
        root,
        "redact",
        kind="TR",
        summary=f"Authorization: Bearer {secret} in trace",
    )
    raw = (camp / "publish" / "findings" / "index.json").read_text(encoding="utf-8")
    assert secret not in raw
    assert "[REDACTED]" in raw


def test_status_digest_includes_budgets_and_next_action(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    debug_campaign.init_campaign(root, slug="digest", mode="incident", item_id="PVTI_test")
    digest = debug_campaign.status_digest(root, "digest")
    assert "runs=0/" in digest
    assert "latest_run=" in digest
    assert "findings=open:" in digest
    assert "next_action=" in digest


def test_repair_apply_requires_campaign_ack(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    camp = debug_campaign.init_campaign(root, slug="repair", mode="incident", item_id="PVTI_test")
    index = json.loads((camp / "INDEX.json").read_text(encoding="utf-8"))
    index["counters"]["runs_used"] = 99
    debug_storage.atomic_write_json(camp / "INDEX.json", index)
    assert debug_campaign.repair_check(root, "repair")
    with pytest.raises(debug_campaign.DebugCampaignError, match="--acknowledge"):
        debug_campaign.repair_apply(root, "repair", acknowledge="wrong-id")
    debug_campaign.repair_apply(root, "repair", acknowledge=str(index["campaign_id"]))
