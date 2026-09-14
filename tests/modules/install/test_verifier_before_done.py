"""
File: test_verifier_before_done.py
Path: tests/modules/install/test_verifier_before_done.py
Role: Tests for shippable verifier-before-Done machine gate (ADR-013).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/project_atomics.py
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/project_outbox.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_atomics as atomics  # noqa: E402
import project_cli  # noqa: E402
import project_handlers  # noqa: E402
import project_outbox  # noqa: E402
from test_project_cli import SAMPLE_SSOT  # noqa: E402

VALID = "PVTI_lAHOBl46-84A9KZxzg3edeQ"


def _ssot(**overrides):
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["fields"] = {
        **data.get("fields", {}),
        "estimate": {"field_id": "PVTF_estimate"},
        "start_date": {"field_id": "PVTF_start"},
        "end_date": {"field_id": "PVTF_end"},
        "size": {
            "field_id": "PVTSSF_size",
            "options": {"xs": "x", "s": "9592a5a3", "m": "9728cbdc", "l": "l", "xl": "xl"},
        },
    }
    data["conventions"] = {
        **data.get("conventions", {}),
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "require_attribution_on_exit": True,
        "require_verifier_before_done": True,
        "set_start_date_on_claim": True,
        "set_end_date_on_done": True,
    }
    data.update(overrides)
    return data


def _ready_item(
    *,
    priority: str = "p2",
    title: str = "chore",
    notes: str = "- @test/implementer · claimed\n",
    extra_body: str = "",
) -> dict:
    body = (
        "## Acceptance\n\n- real\n\n## Rollback\n\n- revert\n\n"
        f"## Notes\n\n{notes}{extra_body}"
    )
    return {
        "id": VALID,
        "title": title,
        "status": "In review",
        "priority": priority,
        "size": "s",
        "estimate": "1",
        "start_date": "2026-09-14",
        "content": {"body": body, "type": "Issue"},
        "assignees": ["SavinRazvan"],
    }


def test_item_is_shippable_pr_audit_priority() -> None:
    assert atomics.item_is_shippable(
        {"priority": "p2", "title": "x"}, "see #123 and notes"
    )
    assert atomics.item_is_shippable(
        {"priority": "p2", "title": "[AUDIT] pass"}, "## Audit Scope\n"
    )
    assert atomics.item_is_shippable({"priority": "p0", "title": "x"}, "no pr")
    assert atomics.item_is_shippable({"priority": "p1", "title": "x"}, "no pr")
    assert not atomics.item_is_shippable({"priority": "p2", "title": "chore"}, "docs only")


def test_notes_show_verifier_hop() -> None:
    assert atomics.notes_show_verifier_hop(
        "- @u/implementer · 2026-01-01T00:00:00Z · next=@u/verifier"
    )
    assert atomics.notes_show_verifier_hop("next=verifier · ok")
    assert not atomics.notes_show_verifier_hop("next=@u/test-runner")


def test_shippable_implementer_done_blocked() -> None:
    ssot = _ssot()
    item = _ready_item(priority="p2", notes="- @test/implementer · PR #999\n")
    ok, detail = atomics.assert_body_ready_for_status(
        ssot, item, "done", agent="implementer"
    )
    assert not ok
    assert "verifier hop" in detail


def test_shippable_prior_notes_verifier_pass() -> None:
    ssot = _ssot()
    item = _ready_item(
        priority="p1",
        notes="- @test/implementer · next=@test/verifier\n",
    )
    ok, detail = atomics.assert_body_ready_for_status(
        ssot, item, "done", agent="implementer"
    )
    assert ok, detail


def test_shippable_agent_verifier_pass() -> None:
    ssot = _ssot()
    item = _ready_item(priority="p1")
    ok, detail = atomics.assert_body_ready_for_status(
        ssot, item, "done", agent="verifier"
    )
    assert ok, detail


def test_non_shippable_chore_pass() -> None:
    ssot = _ssot()
    item = _ready_item(priority="p2", title="docs chore")
    ok, detail = atomics.assert_body_ready_for_status(
        ssot, item, "done", agent="implementer"
    )
    assert ok, detail


def test_convention_off_skips_gate() -> None:
    ssot = _ssot()
    ssot["conventions"]["require_verifier_before_done"] = False
    item = _ready_item(priority="p0")
    ok, detail = atomics.assert_body_ready_for_status(
        ssot, item, "done", agent="implementer"
    )
    assert ok, detail


def test_allow_skip_without_rationale_exit_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        to="done",
        agent="implementer",
        allow_skip_verifier=True,
        skip_verifier_rationale="",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_USAGE


def test_allow_skip_with_rationale_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    item = _ready_item(priority="p1")
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda *a, **k: ([item], None)
    )
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        project_cli, "ensure_end_date_if_done", lambda *a, **k: (True, "2026-09-14", True)
    )
    monkeypatch.setattr(project_cli, "save_last_item_id", lambda *a, **k: None)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        to="done",
        agent="implementer",
        allow_skip_verifier=True,
        skip_verifier_rationale="emergency board hygiene",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_OK


def test_handoff_same_command_next_verifier_to_done_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate runs before Notes append — implementer --next verifier --to done fails."""
    ssot = _ssot()
    item = _ready_item(priority="p1")
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda *a, **k: ([item], None)
    )
    called = {"status": False}

    def boom_status(*a, **k):
        called["status"] = True
        return True, "oid"

    monkeypatch.setattr(project_cli, "set_item_status", boom_status)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        agent="implementer",
        next="verifier",
        to="done",
        text="",
        limit=50,
        allow_skip_verifier=False,
        skip_verifier_rationale="",
    )
    assert project_cli.cmd_handoff(args) == project_cli.EXIT_VALIDATION
    assert not called["status"]


def test_outbox_flush_shippable_without_hop_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    ssot["outbox"] = {
        "enabled": True,
        "path": str(tmp_path / "outbox.jsonl"),
        "min_graphql_remaining": 0,
    }
    item = _ready_item(priority="p1")
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda *a, **k: ([item], None)
    )
    entry = {
        "id": "11111111-1111-4111-8111-111111111111",
        "op": "set-status",
        "item_id": VALID,
        "agent": "implementer",
        "payload": {"to": "done"},
        "status": "pending",
        "attempts": 0,
    }
    ok, detail = project_outbox.apply_outbox_entry(tmp_path, ssot, entry)
    assert not ok
    assert "verifier hop" in detail


def test_outbox_flush_heal_cards_allow_skip_passes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Queued heal-cards CLOSED→Done must flush with allow-skip (ungated contract)."""
    ssot = _ssot()
    # Avoid live end_date GraphQL — focus verifier allow-skip path.
    ssot["conventions"]["set_end_date_on_done"] = False
    item = _ready_item(priority="p1")
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda *a, **k: ([item], None)
    )
    monkeypatch.setattr(
        project_cli, "set_item_status", lambda *a, **k: (True, "oid")
    )
    entry = {
        "id": "22222222-2222-4222-8222-222222222222",
        "op": "set-status",
        "item_id": VALID,
        "agent": "heal-cards",
        "payload": {
            "to": "done",
            "allow_skip_verifier": True,
            "skip_verifier_rationale": "heal-cards CLOSED→Done hygiene",
        },
        "status": "pending",
        "attempts": 0,
    }
    ok, detail = project_outbox.apply_outbox_entry(tmp_path, ssot, entry)
    assert ok, detail


def test_heal_cards_queues_allow_skip_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """heal-cards --apply must enqueue set-status with allow_skip_verifier."""
    ssot = _ssot()
    ssot["outbox"] = {
        "enabled": True,
        "path": str(tmp_path / "outbox.jsonl"),
        "min_graphql_remaining": 200,
        "precheck_writes": True,
    }
    captured: dict = {}

    def fake_guard(*a, **k):
        captured["payload"] = k.get("payload") or (a[5] if len(a) > 5 else None)
        # Non-None return = queued (EXIT_QUEUED path)
        return project_cli.EXIT_QUEUED

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (ssot, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(project_cli, "guard_write_or_queue", fake_guard)
    # api-ready path inside heal-cards
    monkeypatch.setattr(
        project_outbox,
        "api_ready",
        lambda *a, **k: (True, 0, "api-ready=yes"),
    )
    item = {
        "id": VALID,
        "title": "closed",
        "status": "In Progress",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "content": {
            "body": (
                "## Acceptance\n\n- ok\n\n## Rollback\n\n- ok\n\n"
                "## Notes\n\n- @u/a · x\n"
            ),
            "state": "CLOSED",
            "type": "Issue",
        },
    }
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda *a, **k: ([item], None)
    )
    args = argparse.Namespace(
        directory=tmp_path,
        apply=True,
        check=False,
        dry_run=False,
        fill_tier1=False,
        id="",
        last=False,
        json=False,
        agent="heal-cards",
        limit=50,
    )
    # run_heal_cards needs classify — ensure heal_done_candidate
    code = project_handlers.run_heal_cards(args)
    assert code == project_cli.EXIT_OK
    payload = captured.get("payload") or {}
    assert payload.get("to") == "done"
    assert payload.get("allow_skip_verifier") is True
    assert "heal-cards" in str(payload.get("skip_verifier_rationale") or "")


def test_mcp_validate_item_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    from agent_colony_mcp import project_tools as pt

    monkeypatch.setattr(
        pt,
        "_run_cmd",
        lambda root, cmd_fn, args, next_ok=None: pt.format_envelope(
            0, "validate-item: ok", next_ok, None
        ),
    )
    raw = pt.run_project_validate_item(REPO_ROOT, use_last=True)
    data = json.loads(raw)
    assert data["exit_code"] == 0
    assert data["next_recommended_tool"] == "workflow_project_handoff"
