"""
File: test_project_recipes.py
Path: tests/modules/install/test_project_recipes.py
Role: Edge-case tests for board Pattern A recipes (claim/handoff/templates/doctor).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/templates/project-board/
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

import project_cli  # noqa: E402
from test_project_cli import SAMPLE_SSOT  # noqa: E402


def _ssot(**overrides):
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["default_repo"] = data.get("default_repo") or "SavinRazvan/agent-colony"
    data["fields"] = {
        **data.get("fields", {}),
        "estimate": {"field_id": "PVTF_estimate"},
        "start_date": {"field_id": "PVTF_start"},
    }
    data["conventions"] = {
        **data.get("conventions", {}),
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "require_attribution_on_exit": True,
        "one_in_progress_per_assignee": True,
        "claim": "set_assignee",
        "set_start_date_on_claim": True,
    }
    data.update(overrides)
    if "conventions" in overrides:
        data["conventions"] = {
            **data["conventions"],
            **overrides["conventions"],
        }
    if "fields" in overrides:
        data["fields"] = {
            **data["fields"],
            **overrides["fields"],
        }
    return data


def _validate_item(
    *,
    status: str,
    body: str,
    item_id: str,
    priority: str | None = "p1",
    size: str | None = "s",
    estimate: str | None = "1",
    start_date: str | None = None,
) -> dict:
    item = {
        "id": item_id,
        "title": "Validate item",
        "status": status,
        "content": {"body": body},
    }
    if priority is not None:
        item["priority"] = priority
    if size is not None:
        item["size"] = size
    if estimate is not None:
        item["estimate"] = estimate
    if start_date is not None:
        item["start date"] = start_date
    return item


def test_validate_card_body_missing() -> None:
    missing = project_cli.validate_card_body("# x\n", ["Acceptance", "Notes"])
    assert missing == ["Acceptance", "Notes"]
    assert project_cli.validate_card_body("## Acceptance\n## Notes\n", ["Acceptance", "Notes"]) == []


def test_render_card_template_placeholders() -> None:
    tmpl = project_cli.load_card_template(REPO_ROOT, "slice")
    body = project_cli.render_card_template(
        tmpl, acceptance="A1", rollback="R1", notes="- seed"
    )
    assert "## Acceptance" in body
    assert "A1" in body
    assert "## Rollback" in body
    assert "R1" in body
    assert "## Notes" in body
    assert project_cli.validate_card_body(body, ["Acceptance", "Rollback", "Notes"]) == []


def test_fail_prints_code(capsys: pytest.CaptureFixture[str]) -> None:
    code = project_cli.fail("claim", project_cli.EXIT_VALIDATION, "boom")
    assert code == 5
    err = capsys.readouterr().err
    assert "CODE=5" in err
    assert "boom" in err


def test_cmd_create_from_template(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    calls: list[list[str]] = []
    assignee_calls: list[tuple] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["issue", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/SavinRazvan/agent-colony/issues/99\n",
                stderr="",
            )
        if args[:2] == ["project", "item-add"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"id": "PVTI_lAHOBl46-84A9KZxnew001"}),
                stderr="",
            )
        if args[:2] == ["project", "item-edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: "@SavinRazvan",
    )

    def fake_assignee(ssot, item_id, login):
        assignee_calls.append((item_id, login))
        return True, login

    monkeypatch.setattr(project_cli, "set_item_assignee", fake_assignee)
    # Templates load from real repo root via args.directory — point at REPO_ROOT
    args = argparse.Namespace(
        directory=REPO_ROOT,
        title="[T] slice",
        template="slice",
        acceptance="do X",
        rollback="revert",
        notes="",
        status="ready",
        priority="p1",
        size=None,
        estimate=None,
        agent="",
        no_assignee=False,
    )
    assert project_cli.cmd_create_from_template(args) == 0
    captured = capsys.readouterr()
    out = captured.out
    assert "assignee=@SavinRazvan" in out
    assert assignee_calls and assignee_calls[0][1] == "SavinRazvan"
    assert "item_id=PVTI_lAHOBl46-84A9KZxnew001" in out
    assert "priority=p1" in out
    assert "size=s" in out
    assert "estimate=1.0" in out
    assert "Size/Estimate guessed" in captured.err
    assert any(c[:2] == ["issue", "create"] for c in calls)
    assert any(c[:2] == ["project", "item-add"] for c in calls)
    assert any("--single-select-option-id" in c for c in calls)


def test_cmd_create_from_template_no_assignee(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["issue", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/SavinRazvan/agent-colony/issues/99\n",
                stderr="",
            )
        if args[:2] == ["project", "item-add"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"id": "PVTI_lAHOBl46-84A9KZxnew002"}),
                stderr="",
            )
        if args[:2] == ["project", "item-edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should skip assignee")),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        title="[T] slice",
        template="slice",
        acceptance="do X",
        rollback="revert",
        notes="",
        status="ready",
        priority="p1",
        size="s",
        estimate="1",
        agent="",
        no_assignee=True,
    )
    assert project_cli.cmd_create_from_template(args) == 0
    assert "assignee=skipped:--no-assignee" in capsys.readouterr().out


def test_cmd_validate_item_ready_empty_assignees(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "## Acceptance\n- ok\n## Rollback\n- ok\n## Notes\n"
    item = _validate_item(
        status="Ready",
        body=body,
        item_id="PVTI_lAHOBl46-84A9KZxvaldAsn",
    )
    item["assignees"] = []
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([item], None),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id=item["id"], last=False, limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_create_from_template_requires_priority(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        title="[T] slice",
        template="slice",
        acceptance="do X",
        rollback="revert",
        notes="",
        status="ready",
        priority="",
        size=None,
        estimate=None,
        agent="",
        no_assignee=False,
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_USAGE


def test_cmd_create_from_template_explicit_size_estimate_no_guess_warn(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["issue", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/SavinRazvan/agent-colony/issues/99\n",
                stderr="",
            )
        if args[:2] == ["project", "item-add"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"id": "PVTI_lAHOBl46-84A9KZxnew002"}),
                stderr="",
            )
        if args[:2] == ["project", "item-edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@SavinRazvan")
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "SavinRazvan"))
    args = argparse.Namespace(
        directory=REPO_ROOT,
        title="[T] slice",
        template="slice",
        acceptance="do X",
        rollback="revert",
        notes="",
        status="ready",
        priority="p0",
        size="m",
        estimate="3",
        agent="implementer",
        no_assignee=False,
    )
    assert project_cli.cmd_create_from_template(args) == 0
    captured = capsys.readouterr()
    assert "size=m" in captured.out
    assert "estimate=3.0" in captured.out
    assert "guessed" not in captured.err
    assert "guessed" not in captured.out


def test_cmd_claim_draft_warns_assignee(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": "PVTI_lAHOBl46-84A9KZxclaim1",
                    "title": "Work",
                    "status": "Ready",
                    "content": {
                        "body": "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n"
                    },
                }
            ],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "DraftIssue has no GitHub Assignees"),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (True, "ok"),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxclaim1", agent="implementer", text="claimed", limit=100
    )
    assert project_cli.cmd_claim(args) == 0
    captured = capsys.readouterr()
    assert "WARN" in captured.err
    assert "item_id=PVTI_lAHOBl46-84A9KZxclaim1" in captured.out
    assert "@test/implementer" in captured.out


def test_cmd_claim_conflict_one_in_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": "PVTI_lAHOBl46-84A9KZxother1",
                    "title": "Other",
                    "status": "In Progress",
                    "content": {"body": "## Notes\n\n- @test/implementer · claimed\n"},
                },
                {
                    "id": "PVTI_lAHOBl46-84A9KZxnew001",
                    "title": "New",
                    "status": "Ready",
                    "content": {"body": "## Acceptance\n\n## Rollback\n\n## Notes\n"},
                },
            ],
            None,
        ),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxnew001", agent="implementer", text="claimed", limit=100
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_VALIDATION


def test_cmd_handoff_prefixes_next(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    body_box = {
        "body": "## Acceptance\n\na\n\n## Rollback\n\nb\n\n## Notes\n\n- @test/implementer · claimed\n"
    }
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": "PVTI_lAHOBl46-84A9KZxhand01",
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

    def fake_edit(ssot, item_id, body):
        body_box["body"] = body
        return True, "ok"

    monkeypatch.setattr(project_cli, "edit_item_body", fake_edit)
    args = argparse.Namespace(
        directory=REPO_ROOT,
        id="PVTI_lAHOBl46-84A9KZxhand01",
        agent="implementer",
        next="verifier",
        to="in_review",
        text="PR opened",
        limit=100,
    )
    assert project_cli.cmd_handoff(args) == 0
    out = capsys.readouterr().out
    assert "next=@test/verifier" in out
    assert "@test/implementer" in out
    assert "next=@test/verifier" in body_box["body"]


def test_cmd_validate_item_missing_section(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [{"id": "PVTI_lAHOBl46-84A9KZxval001", "title": "V", "status": "Ready", "content": {"body": "# only\n"}}],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxval001", limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_validate_item_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": "PVTI_lAHOBl46-84A9KZxok0001",
                    "title": "OK",
                    "status": "Ready",
                    "priority": "p1",
                    "size": "s",
                    "estimate": "1",
                    "content": {
                        "body": (
                            "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n"
                            "## Notes\n\n- @test/implementer · claimed\n"
                        )
                    },
                }
            ],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxok0001", limit=100)
    assert project_cli.cmd_validate_item(args) == 0


def test_cmd_validate_item_ready_tbd_warns(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    body = "## Acceptance\n\n(TBD)\n\n## Rollback\n\nfixed\n\n## Notes\n\n"
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                _validate_item(
                    status="Ready",
                    body=body,
                    item_id="PVTI_lAHOBl46-84A9KZxvalwarn1",
                )
            ],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxvalwarn1", limit=100)
    assert project_cli.cmd_validate_item(args) == 0
    err = capsys.readouterr().err
    assert "WARN" in err


def test_cmd_validate_item_ready_missing_priority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                _validate_item(
                    status="Ready",
                    body="## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n",
                    item_id="PVTI_lAHOBl46-84A9KZxvalready1",
                    priority=None,
                )
            ],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxvalready1", limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_validate_item_done_tbd_and_start_date_and_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    body = "## Acceptance\n\n(TBD)\n\n## Rollback\n\nfixed\n\n## Notes\n\n- @test/implementer · claimed\n"
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                _validate_item(
                    status="Done",
                    body=body,
                    item_id="PVTI_lAHOBl46-84A9KZxvaldone1",
                    start_date="2026-07-20",
                )
            ],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxvaldone1", limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_validate_item_done_missing_start_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    body = "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n- @test/implementer · claimed\n"
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [_validate_item(status="Done", body=body, item_id="PVTI_lAHOBl46-84A9KZxvald2")],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxvald2", limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_validate_item_done_empty_notes_requires_attribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    body = "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n"
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                _validate_item(
                    status="Done",
                    body=body,
                    item_id="PVTI_lAHOBl46-84A9KZxvaldone2",
                    start_date="2026-07-20",
                )
            ],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxvaldone2", limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_validate_item_in_progress_missing_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    body = "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n- @test/implementer · claimed\n"
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                _validate_item(
                    status="In Progress",
                    body=body,
                    item_id="PVTI_lAHOBl46-84A9KZxvalip01",
                    size=None,
                    start_date="2026-07-20",
                )
            ],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxvalip01", limit=100)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_doctor_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda args, *, timeout_s=60.0: SimpleNamespace(
            returncode=0, stdout='{"items":[]}', stderr=""
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT)
    assert project_cli.cmd_doctor(args) == 0


def test_cmd_get_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda ssot, limit=100: ([], None)
    )
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxmiss01", limit=100, json=False)
    assert project_cli.cmd_get(args) == project_cli.EXIT_NOT_FOUND


def test_cmd_set_status_unknown_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    args = argparse.Namespace(directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxstub01", to="nope")
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_USAGE


def test_cmd_list_gh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda args, *, timeout_s=60.0: SimpleNamespace(
            returncode=1, stdout="", stderr="network down"
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, status="", limit=10, json=False)
    assert project_cli.cmd_list(args) == project_cli.EXIT_GH


def test_append_notes_requires_agent_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    args = argparse.Namespace(
        directory=REPO_ROOT, id="PVTI_lAHOBl46-84A9KZxstub01", text="hi", agent="", limit=100
    )
    assert project_cli.cmd_append_notes(args) == project_cli.EXIT_USAGE

def test_placeholder_item_id_rejected() -> None:
    assert project_cli.is_placeholder_item_id("PVTI_…")
    assert project_cli.is_placeholder_item_id("PVTI_...")
    assert not project_cli.is_placeholder_item_id("PVTI_lAHOBl46-84A9KZxzgzRDnc")


def test_claim_rejects_placeholder_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    args = argparse.Namespace(
        directory=tmp_path,
        id="PVTI_…",
        last=False,
        agent="implementer",
        text="claimed",
        limit=100,
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_USAGE


def test_claim_uses_last(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    project_cli.save_last_item_id(tmp_path, "PVTI_lAHOBl46-84A9KZxlast01", title="T", action="create")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": "PVTI_lAHOBl46-84A9KZxlast01",
                    "title": "T",
                    "status": "Ready",
                    "content": {"body": "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n"},
                }
            ],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "DraftIssue has no GitHub Assignees"),
    )
    monkeypatch.setattr(project_cli, "edit_item_body", lambda *a, **k: (True, "ok"))
    args = argparse.Namespace(
        directory=tmp_path, id="", last=True, agent="implementer", text="claimed", limit=100
    )
    assert project_cli.cmd_claim(args) == 0
    assert project_cli.load_last_item_id(tmp_path) == "PVTI_lAHOBl46-84A9KZxlast01"


def test_cmd_guide_prints_last(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project_cli.save_last_item_id(tmp_path, "PVTI_lAHOBl46-84A9KZxguide1")
    args = argparse.Namespace(directory=tmp_path, agent="implementer", next="verifier")
    assert project_cli.cmd_guide(args) == 0
    out = capsys.readouterr().out
    assert "--last" in out
    assert "PVTI_…" not in out
    assert "PVTI_lAHOBl46-84A9KZxguide1" in out

