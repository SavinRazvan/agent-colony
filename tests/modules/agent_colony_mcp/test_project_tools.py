"""
File: test_project_tools.py
Path: tests/modules/agent_colony_mcp/test_project_tools.py
Role: Unit tests for Pattern A MCP adapters and envelopes (ADR-012).
Used By:
 - pytest
Depends On:
 - agent_colony_mcp.project_tools
Notes:
 - Mocks cmd_* — no live GraphQL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from agent_colony_mcp import project_tools as pt

REPO_ROOT = Path(__file__).resolve().parents[3]


def _parse(raw: str) -> dict[str, Any]:
    return json.loads(raw)


def _load_project_cli() -> Any:
    pt._ensure_install_path(REPO_ROOT)
    import project_cli as pc

    return pc


def _load_doc_cli() -> Any:
    pt._ensure_install_path(REPO_ROOT)
    import doc_cli as dc

    return dc


def test_format_envelope_exit_queued_forces_outbox() -> None:
    raw = pt.format_envelope(6, "queued", "workflow_project_claim", None)
    data = _parse(raw)
    assert data["exit_code"] == 6
    assert data["next_recommended_tool"] == "workflow_project_outbox_status"
    assert "do not retry" in data["summary"].lower()
    assert data["detail"] is None


def test_project_entry_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = _load_project_cli()

    def fake_entry(args: argparse.Namespace) -> int:
        assert args.digest is True
        print("mode=live · items=0 · next=claim")
        return 0

    monkeypatch.setattr(pc, "cmd_entry", fake_entry)
    raw = pt.run_project_entry(REPO_ROOT, digest=True)
    data = _parse(raw)
    assert data["exit_code"] == 0
    assert "mode=live" in data["summary"]
    assert data["next_recommended_tool"] == "workflow_project_claim"
    assert data["detail"] is None


def test_project_claim_exit_queued(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = _load_project_cli()

    def fake_claim(args: argparse.Namespace) -> int:
        assert args.last is True
        assert args.agent == "implementer"
        print("claim: EXIT_QUEUED", file=sys.stderr)
        return 6

    monkeypatch.setattr(pc, "cmd_claim", fake_claim)
    raw = pt.run_project_claim(REPO_ROOT, agent="implementer")
    data = _parse(raw)
    assert data["exit_code"] == 6
    assert data["next_recommended_tool"] == "workflow_project_outbox_status"
    assert "do not retry" in data["summary"].lower()


def test_project_handoff_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = _load_project_cli()

    def fake_handoff(args: argparse.Namespace) -> int:
        assert args.next == "verifier"
        assert args.to == "in_review"
        print("handoff: ok")
        return 0

    monkeypatch.setattr(pc, "cmd_handoff", fake_handoff)
    raw = pt.run_project_handoff(
        REPO_ROOT, agent="implementer", next_agent="verifier", to="in_review"
    )
    data = _parse(raw)
    assert data["exit_code"] == 0
    assert data["summary"].startswith("handoff:")
    assert data["detail"] is None


def test_project_outbox_status(monkeypatch: pytest.MonkeyPatch) -> None:
    pc = _load_project_cli()

    def fake_status(args: argparse.Namespace) -> int:
        print("outbox: pending=0 remaining=5000")
        return 0

    monkeypatch.setattr(pc, "cmd_outbox_status", fake_status)
    raw = pt.run_project_outbox_status(REPO_ROOT)
    data = _parse(raw)
    assert data["exit_code"] == 0
    assert "outbox:" in data["summary"]


def test_doc_skill_section(monkeypatch: pytest.MonkeyPatch) -> None:
    dc = _load_doc_cli()

    def fake_section(args: argparse.Namespace) -> int:
        assert args.skill == "board-ssot"
        assert args.section == "Continuation"
        print("skill=board-ssot · section=Continuation · bytes=12")
        print("section body")
        return 0

    monkeypatch.setattr(dc, "cmd_doc_skill_section", fake_section)
    raw = pt.run_doc_skill_section(
        REPO_ROOT, skill="board-ssot", section="Continuation"
    )
    data = _parse(raw)
    assert data["exit_code"] == 0
    assert "board-ssot" in data["summary"]


def test_session_entry_composite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pc = _load_project_cli()

    def fake_entry(args: argparse.Namespace) -> int:
        print("mode=live · items=1")
        return 0

    def fake_last(args: argparse.Namespace) -> int:
        print("PVTI_test")
        return 0

    monkeypatch.setattr(pc, "cmd_entry", fake_entry)
    monkeypatch.setattr(pc, "cmd_last", fake_last)

    idx = tmp_path / ".local" / "index-and-planning" / "current"
    idx.mkdir(parents=True)
    (idx / "change-index.md").write_text(
        "| Date | Change |\n| --- | --- |\n| 2026-08-22 | row-one |\n",
        encoding="utf-8",
    )

    # Point session helpers at tmp_path while reusing patched CLI cmds
    monkeypatch.setattr(
        pt,
        "run_project_entry",
        lambda root, digest=True, also_ready=False, force_live=False: pt.format_envelope(
            0, "mode=live · items=1", "workflow_project_claim", None
        ),
    )
    monkeypatch.setattr(pt, "_ensure_install_path", lambda root: pt._install_pkg(REPO_ROOT))

    # cmd_last still needs project_cli on path; use real module with fake_last
    raw = pt.run_session_entry(tmp_path)
    data = _parse(raw)
    assert data["exit_code"] == 0
    assert "mode=live" in data["summary"]
    assert "PVTI_test" in data["summary"]
    assert "row-one" in data["summary"]
    assert data["next_recommended_tool"] == "workflow_project_claim"


def test_session_entry_missing_change_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pc = _load_project_cli()

    def fake_last(args: argparse.Namespace) -> int:
        return 2  # no last item

    monkeypatch.setattr(pc, "cmd_last", fake_last)
    monkeypatch.setattr(
        pt,
        "run_project_entry",
        lambda root, digest=True, also_ready=False, force_live=False: pt.format_envelope(
            0, "mode=offline", "workflow_project_claim", None
        ),
    )
    monkeypatch.setattr(pt, "_ensure_install_path", lambda root: pt._install_pkg(REPO_ROOT))

    raw = pt.run_session_entry(tmp_path)
    data = _parse(raw)
    assert data["exit_code"] == 0
    assert "mode=offline" in data["summary"]
    assert "change-index=" not in data["summary"]
    assert "last=" not in data["summary"]
