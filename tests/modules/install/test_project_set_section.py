"""
File: test_project_set_section.py
Path: tests/modules/install/test_project_set_section.py
Role: Tests for set-section CLI and body gates on handoff/set-status → in_review|done.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_atomics.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_atomics as atomics  # noqa: E402
import project_cli  # noqa: E402
from test_project_cli import SAMPLE_SSOT  # noqa: E402

VALID = "PVTI_lAHOBl46-84A9KZxsect01"


def _ssot(**overrides):
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["fields"] = {
        **data.get("fields", {}),
        "estimate": {"field_id": "PVTF_estimate"},
        "start_date": {"field_id": "PVTF_start"},
        "size": {
            "field_id": "PVTSSF_size",
            "options": {"xs": "x", "s": "9592a5a3", "m": "9728cbdc", "l": "l", "xl": "xl"},
        },
    }
    data["conventions"] = {
        **data.get("conventions", {}),
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "require_attribution_on_exit": True,
        "set_start_date_on_claim": True,
    }
    data.update(overrides)
    return data


def test_is_placeholder_list_tbd() -> None:
    assert atomics.is_placeholder_section_content("- (TBD)")
    assert atomics.is_placeholder_section_content("* (TBD)")
    assert atomics.is_placeholder_section_content("(TBD)")
    assert not atomics.is_placeholder_section_content("- real criterion")


def test_replace_section_content_roundtrip() -> None:
    body = "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- (TBD)\n\n## Notes\n\n"
    new, changed = atomics.replace_section_content(body, "Acceptance", "- done")
    assert changed
    assert atomics.section_body_content(new, "Acceptance") == "- done"
    assert "## Rollback" in new
    same, changed2 = atomics.replace_section_content(new, "Acceptance", "- done")
    assert not changed2
    with pytest.raises(ValueError, match="missing"):
        atomics.replace_section_content("no headings", "Acceptance", "x")


def test_normalize_set_section_rejects_notes() -> None:
    with pytest.raises(ValueError, match="acceptance\\|rollback"):
        atomics.normalize_set_section_name("Notes")
    assert atomics.normalize_set_section_name("ACCEPTANCE") == "Acceptance"


def test_assert_body_ready_blocks_tbd() -> None:
    ssot = _ssot()
    item = {
        "id": VALID,
        "status": "In Progress",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "start_date": "2026-07-21",
        "content": {
            "body": (
                "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- (TBD)\n\n"
                "## Notes\n\n- @test/implementer · claimed\n"
            )
        },
    }
    ok, detail = atomics.assert_body_ready_for_status(ssot, item, "in_review")
    assert not ok
    assert "Acceptance" in detail or "placeholder" in detail
    assert "set-section" in detail
    ok2, _ = atomics.assert_body_ready_for_status(ssot, item, "in_progress")
    assert ok2


def test_cmd_set_section_updates_body(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    body_box = {
        "body": (
            "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- keep\n\n"
            "## Notes\n\n- @test/implementer · claimed\n"
        )
    }
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [{"id": VALID, "title": "S", "status": "In Progress", "content": body_box}],
            None,
        ),
    )

    def fake_edit(ssot_arg, item_id, body):
        body_box["body"] = body
        return True, "ok"

    monkeypatch.setattr(project_cli, "edit_item_body", fake_edit)
    monkeypatch.setattr(project_cli, "note_successful_write", lambda *a, **k: None)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == 0
    assert "- criteria met" in body_box["body"]
    assert "set-section Acceptance" in body_box["body"]
    out = capsys.readouterr().out
    assert "Acceptance updated" in out


def test_cmd_set_section_rejects_notes_and_tbd(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="notes",
        text="nope",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_USAGE
    args2 = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="(TBD)",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args2) == project_cli.EXIT_VALIDATION


def test_handoff_to_in_review_blocked_on_tbd(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [
                {
                    "id": VALID,
                    "title": "H",
                    "status": "In Progress",
                    "priority": "p1",
                    "size": "s",
                    "estimate": "1",
                    "start_date": "2026-07-21",
                    "content": {
                        "body": (
                            "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n\n"
                            "## Notes\n\n- @test/implementer · claimed\n"
                        )
                    },
                }
            ],
            None,
        ),
    )
    called = {"status": False}

    def boom(*a, **k):
        called["status"] = True
        return True, "oid"

    monkeypatch.setattr(project_cli, "set_item_status", boom)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="",
        limit=50,
    )
    assert project_cli.cmd_handoff(args) == project_cli.EXIT_VALIDATION
    assert not called["status"]


def test_set_status_to_done_blocked_on_tbd(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [
                {
                    "id": VALID,
                    "title": "H",
                    "status": "In review",
                    "priority": "p1",
                    "size": "s",
                    "estimate": "1",
                    "start_date": "2026-07-21",
                    "content": {
                        "body": (
                            "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n\n"
                            "## Notes\n\n- @test/implementer · claimed\n"
                        )
                    },
                }
            ],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        to="done",
        agent="project-cli",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_VALIDATION


def test_handoff_ok_after_real_acceptance(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    body_box = {
        "body": (
            "## Acceptance\n\n- real\n\n## Rollback\n\n- revert\n\n"
            "## Notes\n\n- @test/implementer · claimed\n"
        )
    }
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [
                {
                    "id": VALID,
                    "title": "H",
                    "status": "In Progress",
                    "priority": "p1",
                    "size": "s",
                    "estimate": "1",
                    "start_date": "2026-07-21",
                    "content": body_box,
                }
            ],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))

    def fake_edit(ssot_arg, item_id, body):
        body_box["body"] = body
        return True, "ok"

    monkeypatch.setattr(project_cli, "edit_item_body", fake_edit)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="",
        limit=50,
    )
    assert project_cli.cmd_handoff(args) == 0
