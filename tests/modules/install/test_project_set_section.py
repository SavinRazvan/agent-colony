"""
File: test_project_set_section.py
Path: tests/modules/install/test_project_set_section.py
Role: Tests for set-section CLI and body gates on handoff/set-status → in_review|done.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/project_atomics.py
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


def test_is_placeholder_all_whitespace_lines() -> None:
    """Line 89: lines list is empty after stripping whitespace-only lines."""
    assert atomics.is_placeholder_section_content("   \n   \n   ")


def test_is_placeholder_list_tbd() -> None:
    assert atomics.is_placeholder_section_content("- (TBD)")
    assert atomics.is_placeholder_section_content("* (TBD)")
    assert atomics.is_placeholder_section_content("(TBD)")
    assert not atomics.is_placeholder_section_content("- real criterion")


def test_replace_section_content_empty_name_noop() -> None:
    """Line 131: replace_section_content returns (body, False) when name is empty."""
    body = "## Acceptance\n\nok\n"
    result, changed = atomics.replace_section_content(body, "", "new text")
    assert not changed
    assert result == body


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


def test_assert_body_ready_item_not_mapping() -> None:
    """Line 172: assert_body_ready_for_status returns (False, ...) when item is not a dict."""
    ssot = _ssot()
    ok, detail = atomics.assert_body_ready_for_status(ssot, None, "in_review")
    assert not ok
    assert "not a mapping" in detail


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


# --- project_cli.py: set-status body gate (lines 816, 819) ---


def test_cmd_set_status_body_gate_fetch_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 816: fetch_project_items fails during body gate → EXIT_GH."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "gh item-list failed"),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        to="done",
        agent="project-cli",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_GH


def test_cmd_set_status_body_gate_item_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 819: item not found during body gate → EXIT_NOT_FOUND."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], None),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        to="in_review",
        agent="project-cli",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_NOT_FOUND


# --- project_cli.py: cmd_set_section edge paths ---


def test_cmd_set_section_ssot_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 1018: _load_enabled_ssot returns None → return code."""
    ssot_disabled = {**SAMPLE_SSOT, "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot_disabled, []))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="ok",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) != 0


def test_cmd_set_section_id_not_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 1021: resolve_item_id_arg returns None → return id_code."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (None, project_cli.EXIT_NOT_FOUND),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=None,
        last=False,
        section="acceptance",
        text="ok",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_NOT_FOUND


def test_cmd_set_section_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 1028: empty text → EXIT_USAGE."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_USAGE


def test_cmd_set_section_guard_queues(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 1048: guard_write_or_queue returns non-None → return pre."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: project_cli.EXIT_QUEUED)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_QUEUED


def test_cmd_set_section_fetch_fails_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lines 1051-1063: fetch_project_items fails with rate limit → EXIT_QUEUED via try_queue."""
    import yaml
    ssot = _ssot()
    outbox_rel = "outbox/set-section-test.jsonl"
    ssot["outbox"] = {"enabled": True, "path": outbox_rel, "precheck_writes": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "API rate limit exceeded"),
    )
    collab_path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    collab_path.parent.mkdir(parents=True, exist_ok=True)
    collab_path.write_text(yaml.safe_dump({
        "version": 1,
        "owner": {"display_name": "Test User", "github_user": "@test"},
        "project_ssot": ssot,
        "commit_provenance": {"ai_disclosure_mode": "assisted_by"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }), encoding="utf-8")
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="implementer",
        limit=50,
    )
    result = project_cli.cmd_set_section(args)
    assert result in (project_cli.EXIT_QUEUED, project_cli.EXIT_GH)


def test_cmd_set_section_fetch_fails_not_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 1063: fetch fails, not a rate limit → EXIT_GH."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "some other gh error"),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_GH


def test_cmd_set_section_item_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 1066: item not found → EXIT_NOT_FOUND."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(project_cli, "fetch_project_items", lambda *a, **k: ([], None))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_NOT_FOUND


def test_cmd_set_section_replace_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 1070-1071: replace_section_content raises ValueError (missing heading)."""
    ssot = _ssot()
    body_no_heading = {"body": "no section headings here"}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": body_no_heading}], None),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_VALIDATION


def test_cmd_set_section_edit_fails_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lines 1075-1087: edit_item_body fails → try rate-limit queue → EXIT_QUEUED."""
    import yaml
    ssot = _ssot()
    ssot["outbox"] = {"enabled": True, "path": "outbox/set-section-edit.jsonl", "precheck_writes": False}
    body = "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": {"body": body}}], None),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (False, "API rate limit exceeded"),
    )
    collab_path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    collab_path.parent.mkdir(parents=True, exist_ok=True)
    collab_path.write_text(yaml.safe_dump({
        "version": 1,
        "owner": {"display_name": "Test User", "github_user": "@test"},
        "project_ssot": ssot,
        "commit_provenance": {"ai_disclosure_mode": "assisted_by"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }), encoding="utf-8")
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="",
        limit=50,
    )
    result = project_cli.cmd_set_section(args)
    assert result in (project_cli.EXIT_QUEUED, project_cli.EXIT_GH)


def test_cmd_set_section_edit_fails_not_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 1087: edit_item_body fails, not rate limit → EXIT_GH."""
    ssot = _ssot()
    body = "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": {"body": body}}], None),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (False, "some gh error"),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_GH


def test_cmd_set_section_idempotent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Line 1091: body unchanged → print 'unchanged (idempotent)'."""
    ssot = _ssot()
    body = "## Acceptance\n\n- criteria met\n\n## Rollback\n\n- revert\n"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": {"body": body}}], None),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_OK
    assert "unchanged (idempotent)" in capsys.readouterr().out


def test_cmd_set_section_notes_exit_queued(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 1103-1104: append_notes_helper returns EXIT_QUEUED → propagate EXIT_QUEUED."""
    ssot = _ssot()
    body = "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": {"body": body}}], None),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (True, "ok"),
    )
    monkeypatch.setattr(project_cli, "note_successful_write", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "queued", project_cli.EXIT_QUEUED),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_QUEUED


def test_cmd_set_section_notes_gh_fail_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lines 1105-1117: notes fails with EXIT_GH → try rate-limit queue."""
    import yaml
    ssot = _ssot()
    ssot["outbox"] = {"enabled": True, "path": "outbox/set-section-notes.jsonl", "precheck_writes": False}
    body = "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": {"body": body}}], None),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (True, "ok"),
    )
    monkeypatch.setattr(project_cli, "note_successful_write", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "API rate limit exceeded", project_cli.EXIT_GH),
    )
    collab_path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    collab_path.parent.mkdir(parents=True, exist_ok=True)
    collab_path.write_text(yaml.safe_dump({
        "version": 1,
        "owner": {"display_name": "Test User", "github_user": "@test"},
        "project_ssot": ssot,
        "commit_provenance": {"ai_disclosure_mode": "assisted_by"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }), encoding="utf-8")
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="implementer",
        limit=50,
    )
    result = project_cli.cmd_set_section(args)
    assert result in (project_cli.EXIT_QUEUED, project_cli.EXIT_GH)


def test_cmd_set_section_notes_non_gh_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 1118: notes fails with non-EXIT_GH/QUEUED → fail with that code."""
    ssot = _ssot()
    body = "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([{"id": VALID, "title": "T", "content": {"body": body}}], None),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (True, "ok"),
    )
    monkeypatch.setattr(project_cli, "note_successful_write", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes write failed", project_cli.EXIT_VALIDATION),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id=VALID,
        last=False,
        section="acceptance",
        text="- criteria met",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_set_section(args) == project_cli.EXIT_VALIDATION


# --- project_cli.py: cmd_board_shell_init and cmd_close_linked_issue delegates ---


def test_cmd_board_shell_init_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 1228-1230: cmd_board_shell_init calls run_board_shell_init."""
    called = {"n": 0}

    def fake_run(args):
        called["n"] += 1
        return project_cli.EXIT_OK

    monkeypatch.setattr(project_handlers, "run_board_shell_init", fake_run)
    args = SimpleNamespace(directory=REPO_ROOT, minimal=True, force=False)
    assert project_cli.cmd_board_shell_init(args) == project_cli.EXIT_OK
    assert called["n"] == 1


def test_cmd_close_linked_issue_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 1331-1332: cmd_close_linked_issue calls run_close_linked_issue."""
    called = {"n": 0}

    def fake_run(args):
        called["n"] += 1
        return project_cli.EXIT_OK

    monkeypatch.setattr(project_handlers, "run_close_linked_issue", fake_run)
    args = SimpleNamespace(directory=REPO_ROOT)
    assert project_cli.cmd_close_linked_issue(args) == project_cli.EXIT_OK
    assert called["n"] == 1
