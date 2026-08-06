"""
File: test_project_cov100_gaps.py
Path: tests/modules/install/test_project_cov100_gaps.py
Role: Targeted tests for remaining scoped kit coverage gaps (project_* + gh adapter).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_handlers.py
 - .ai_infra/install/cursor_workflow/project_outbox.py
 - .ai_infra/install/cursor_workflow/project_recipes.py
 - .ai_infra/install/cursor_workflow/project_atomics.py
 - .ai_infra/install/cursor_workflow/gh_project_adapter.py
Notes:
 - Monkeypatches gh/GraphQL; no live network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import gh_project_adapter as gha  # noqa: E402
import project_atomics  # noqa: E402
import project_cli  # noqa: E402
import project_handlers  # noqa: E402
import project_outbox  # noqa: E402
import project_recipes  # noqa: E402
from test_project_cli import SAMPLE_SSOT, VALID_PVTI, _write_collab  # noqa: E402


def _ensure_pr_scripts(tmp_path: Path) -> None:
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr"
    dst = tmp_path / ".ai_infra" / "scripts" / "pr"
    dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "user_settings.py",
        "user_settings_load.py",
        "user_settings_resolve.py",
        "user_settings_render.py",
        "local_workflow_paths.py",
    ):
        file_src = src / name
        if file_src.is_file():
            (dst / name).write_text(file_src.read_text(encoding="utf-8"), encoding="utf-8")


def _ssot(**overrides: object) -> dict:
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
        data["conventions"] = {**data["conventions"], **overrides["conventions"]}  # type: ignore[arg-type]
    if "fields" in overrides:
        data["fields"] = {**data["fields"], **overrides["fields"]}  # type: ignore[arg-type]
    return data


def _outbox_ssot(tmp_path: Path, **outbox_overrides: object) -> dict:
    rel = "outbox/cov100-outbox.jsonl"
    outbox = {
        "enabled": True,
        "path": rel,
        "min_graphql_remaining": 200,
        "max_flush_per_run": 10,
        "retry_backoff_seconds": 0,
        **outbox_overrides,
    }
    return {**_ssot(), "outbox": outbox}


def _mock_graphql(monkeypatch: pytest.MonkeyPatch, *, remaining: int = 5000, error: str | None = None) -> None:
    if error:

        def _fail() -> dict:
            return {"remaining": None, "limit": None, "reset_epoch": None, "error": error}

        monkeypatch.setattr(project_outbox, "graphql_rate_limit", _fail)
    else:

        def _ok() -> dict:
            return {
                "remaining": remaining,
                "limit": 5000,
                "reset_epoch": 1700000000,
                "error": None,
            }

        monkeypatch.setattr(project_outbox, "graphql_rate_limit", _ok)


def _board_item(*, start_date: str = "", item_id: str = VALID_PVTI, status: str = "Ready") -> dict:
    item: dict = {
        "id": item_id,
        "title": "Slice",
        "status": status,
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "content": {
            "body": (
                "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n"
                "## Notes\n\n- @test/implementer · claimed\n"
            ),
        },
    }
    if start_date:
        item["start date"] = start_date
        item["start_date"] = start_date
    else:
        item["start_date"] = "2026-07-21"
    return item


def _create_template_args(**overrides: object) -> argparse.Namespace:
    base = {
        "directory": REPO_ROOT,
        "title": "[T] slice",
        "template": "slice",
        "acceptance": "do X",
        "rollback": "revert",
        "notes": "",
        "status": "",
        "priority": "p1",
        "size": None,
        "estimate": None,
        "agent": "",
        "no_assignee": False,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _stub_create_assignee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@SavinRazvan")
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "SavinRazvan"))


def _fake_create_gh(item_id: str = "PVTI_lAHOBl46-84A9KZxnew001"):
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
                stdout=json.dumps({"id": item_id}),
                stderr="",
            )
        if args[:2] == ["project", "item-edit"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    return fake_gh


# --- project_cli create-from-template gaps ---


@pytest.mark.parametrize(
    "estimate,expected",
    [
        ("not-a-number", "must be a number"),
        ("-1", ">= 0"),
    ],
)
def test_create_from_template_bad_estimate(
    monkeypatch: pytest.MonkeyPatch, estimate: str, expected: str
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "create_board_item",
        lambda *a, **k: ("PVTI_x", "", None),
    )
    args = _create_template_args(estimate=estimate)
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_USAGE


def test_create_from_template_priority_keyerror_after_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "create_board_item",
        lambda *a, **k: ("PVTI_x", "", None),
    )

    def raise_priority(ssot, field, value):
        if field == "priority":
            raise KeyError("priority field missing")
        return "fid", "oid"

    monkeypatch.setattr(project_cli, "resolve_field_option_id", raise_priority)
    args = _create_template_args()
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_USAGE


def test_create_from_template_priority_gh_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "create_board_item",
        lambda *a, **k: ("PVTI_x", "", None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="priority edit failed"),
    )
    args = _create_template_args()
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_GH


def test_create_from_template_size_and_estimate_warn_paths(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "create_board_item",
        lambda *a, **k: ("PVTI_x", "", None),
    )
    calls = {"n": 0}

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["project", "item-edit"]:
            calls["n"] += 1
            if calls["n"] == 1:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="size edit failed")
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(
        project_cli,
        "resolve_field_option_id",
        lambda ssot, field, value: ("fid", "oid"),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_number",
        lambda *a, **k: (False, "estimate edit failed"),
    )
    _stub_create_assignee(monkeypatch)
    args = _create_template_args(size="m", estimate="2")
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "size skipped" in err
    assert "estimate skipped" in err


def test_create_from_template_size_keyerror_warn(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "create_board_item",
        lambda *a, **k: ("PVTI_x", "", None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    def resolve(ssot, field, value):
        if field == "size":
            raise KeyError("size field missing")
        return "fid", "oid"

    monkeypatch.setattr(project_cli, "resolve_field_option_id", resolve)
    monkeypatch.setattr(project_cli, "set_item_number", lambda *a, **k: (True, "ok"))
    _stub_create_assignee(monkeypatch)
    args = _create_template_args(size="m", estimate="2")
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_OK
    assert "size skipped" in capsys.readouterr().err


def test_create_from_template_guessed_notes_with_agent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(project_cli, "run_gh", _fake_create_gh())
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    _stub_create_assignee(monkeypatch)
    args = _create_template_args(agent="implementer")
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "notes: Size/Estimate guessed" in out


def test_create_from_template_guessed_notes_fail_with_agent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(project_cli, "run_gh", _fake_create_gh("PVTI_lAHOBl46-84A9KZxnew003"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes failed", project_cli.EXIT_GH),
    )
    _stub_create_assignee(monkeypatch)
    args = _create_template_args(agent="implementer")
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_OK
    assert "guessed Notes failed" in capsys.readouterr().err


# --- project_cli guard precheck + set-status start_date warn ---


def test_cmd_set_status_precheck_queues_before_gh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        to="ready",
        agent="implementer",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_QUEUED


def test_cmd_set_status_start_date_warn_on_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        project_cli,
        "ensure_start_date_if_starting",
        lambda *a, **k: (False, "date write failed", False),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        to="in_progress",
        agent="implementer",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_OK
    assert "start_date skipped" in capsys.readouterr().err


def test_cmd_set_field_estimate_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        field="estimate",
        to="2",
        agent="implementer",
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_QUEUED


def test_cmd_set_field_priority_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        field="priority",
        to="p1",
        agent="implementer",
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_QUEUED


def test_cmd_append_notes_returns_queued_from_helper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "queued", project_cli.EXIT_QUEUED),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        text="x",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_append_notes(args) == project_cli.EXIT_QUEUED


def test_cmd_set_assignee_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        login="alice",
        agent="implementer",
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_QUEUED


# --- project_handlers gaps ---


def _claim_args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    base = {
        "directory": tmp_path,
        "id": VALID_PVTI,
        "last": False,
        "agent": "implementer",
        "text": "claimed",
        "limit": 100,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def _handoff_args(tmp_path: Path, **overrides: object) -> argparse.Namespace:
    base = {
        "directory": tmp_path,
        "id": VALID_PVTI,
        "last": False,
        "agent": "implementer",
        "next": "verifier",
        "to": "in_review",
        "text": "done",
        "limit": 100,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_run_claim_precheck_queues_before_fetch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    _mock_graphql(monkeypatch, remaining=50)
    assert project_handlers.run_claim(_claim_args(tmp_path)) == project_cli.EXIT_QUEUED


def test_run_claim_skips_start_date_when_already_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([_board_item(start_date="2026-07-01")], None),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    assert project_handlers.run_claim(_claim_args(tmp_path)) == project_cli.EXIT_OK


def test_run_claim_notes_exit_queued_direct(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([_board_item()], None),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "queued", project_cli.EXIT_QUEUED),
    )
    assert project_handlers.run_claim(_claim_args(tmp_path)) == project_cli.EXIT_QUEUED


def test_run_handoff_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    _mock_graphql(monkeypatch, remaining=50)
    assert project_handlers.run_handoff(_handoff_args(tmp_path)) == project_cli.EXIT_QUEUED


def test_run_handoff_start_date_warn_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([_board_item()], None),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(
        project_cli,
        "ensure_start_date_if_starting",
        lambda *a, **k: (False, "date write failed", False),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    assert project_handlers.run_handoff(_handoff_args(tmp_path, to="in_progress")) == project_cli.EXIT_OK
    assert "start_date skipped" in capsys.readouterr().err

    monkeypatch.setattr(
        project_cli,
        "ensure_start_date_if_starting",
        lambda *a, **k: (True, "skipped: fields.start_date.field_id missing", False),
    )
    assert project_handlers.run_handoff(_handoff_args(tmp_path, to="in_progress")) == project_cli.EXIT_OK
    assert "field_id missing" in capsys.readouterr().err


def test_run_handoff_notes_exit_queued_direct(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([_board_item(status="In Progress")], None),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "queued", project_cli.EXIT_QUEUED),
    )
    assert project_handlers.run_handoff(_handoff_args(tmp_path, to="")) == project_cli.EXIT_QUEUED


def test_run_mention_pr_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"number": 1, "url": "https://github.com/o/r/pull/1"}),
            stderr="",
        ),
    )
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_QUEUED


def test_run_promote_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_QUEUED


def test_run_promote_notes_exit_queued_direct(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (
            True,
            "Issue #1",
            {"item_id": VALID_PVTI, "issue_number": "1", "url": "u", "noop": False},
        ),
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "queued", project_cli.EXIT_QUEUED),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_QUEUED


# --- project_outbox gaps ---


def test_read_quota_cache_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    assert project_outbox.read_quota_cache(path) is None


def test_get_cached_invalid_fetched_at_refreshes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    cfg = project_outbox.load_outbox_config(ssot)
    path = project_outbox.quota_cache_path(tmp_path, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fetched_at": "not-a-float", "remaining": 999}), encoding="utf-8")
    calls = {"n": 0}

    def _rl() -> dict:
        calls["n"] += 1
        return {"remaining": 4000, "limit": 5000, "reset_epoch": 0, "error": None}

    monkeypatch.setattr(project_outbox, "graphql_rate_limit", _rl)
    info = project_outbox.get_cached_graphql_remaining(tmp_path, ssot)
    assert info["remaining"] == 4000
    assert info["from_cache"] is False
    assert calls["n"] == 1


def test_remaining_below_min_on_error_and_bad_remaining(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_outbox,
        "get_cached_graphql_remaining",
        lambda *a, **k: {"error": "gh down", "remaining": 0},
    )
    below, info = project_outbox.remaining_below_min(tmp_path, ssot)
    assert below is False
    assert info["error"] == "gh down"

    monkeypatch.setattr(
        project_outbox,
        "get_cached_graphql_remaining",
        lambda *a, **k: {"remaining": "many", "error": None},
    )
    below2, _ = project_outbox.remaining_below_min(tmp_path, ssot)
    assert below2 is False


def test_find_duplicate_pending_skips_wrong_status_op_and_item_id() -> None:
    entries = [
        _valid_outbox_entry(status="done", op="append-notes"),
        _valid_outbox_entry(status="pending", op="set-status"),
        _valid_outbox_entry(status="pending", op="append-notes", item_id="PVTI_other"),
    ]
    assert (
        project_outbox.find_duplicate_pending(
            entries,
            op="append-notes",
            item_id=VALID_PVTI,
            payload={"text": "queued note"},
        )
        is None
    )


def test_run_mention_pr_notes_exit_queued_direct(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"number": 1, "url": "https://github.com/o/r/pull/1"}),
            stderr="",
        ),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "9", {"repo": "o/r"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "queued", project_cli.EXIT_QUEUED),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_QUEUED


def _valid_outbox_entry(**overrides: object) -> dict:
    base = {
        "id": "00000000-0000-4000-8000-000000000001",
        "ts": "2026-07-18T10:00:00Z",
        "agent": "implementer",
        "github_user": "@test",
        "op": "append-notes",
        "item_id": VALID_PVTI,
        "payload": {"text": "queued note"},
        "status": "pending",
        "attempts": 0,
        "last_error": None,
    }
    base.update(overrides)
    return base


def test_maybe_enqueue_precheck_disabled_returns_none(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path, precheck_writes=False)
    assert (
        project_outbox.maybe_enqueue_on_low_quota(
            tmp_path,
            ssot,
            cmd="set-status",
            op="set-status",
            item_id=VALID_PVTI,
            agent="implementer",
            payload={"to": "ready"},
        )
        is None
    )


def test_maybe_enqueue_low_quota_enqueue_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _mock_graphql(monkeypatch, remaining=50)
    monkeypatch.setattr(project_outbox, "enqueue_op", lambda *a, **k: (None, "disk full"))
    code = project_outbox.maybe_enqueue_on_low_quota(
        tmp_path,
        ssot,
        cmd="set-status",
        op="set-status",
        item_id=VALID_PVTI,
        agent="implementer",
        payload={"to": "ready"},
    )
    assert code == project_cli.EXIT_GH
    assert "low-quota enqueue failed" in capsys.readouterr().err


def test_note_successful_write_noop_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path, enabled=False)
    calls = {"n": 0}
    monkeypatch.setattr(
        project_outbox,
        "get_cached_graphql_remaining",
        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or {},
    )
    project_outbox.note_successful_write(tmp_path, ssot)
    assert calls["n"] == 0


def test_apply_outbox_set_status_fail_and_start_date_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["fields"] = {**ssot["fields"], "start_date": {"field_id": "PVTF_start"}}
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (False, "status failed"))
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_outbox_entry(op="set-status", payload={"to": "in_progress"}),
    )
    assert not ok and detail == "status failed"

    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "ok"))
    monkeypatch.setattr(project_cli, "set_item_date", lambda *a, **k: (False, "date failed"))
    ok2, detail2 = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_outbox_entry(
            op="set-status",
            payload={"to": "in_progress", "start_date": "2026-07-18"},
        ),
    )
    assert not ok2 and "start_date failed" in detail2

    monkeypatch.setattr(
        project_cli,
        "ensure_start_date_if_starting",
        lambda *a, **k: (False, "ensure failed", False),
    )
    ok3, detail3 = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_outbox_entry(op="set-status", payload={"to": "in_progress"}),
    )
    assert not ok3 and "start_date failed" in detail3


def test_apply_outbox_handoff_in_progress_start_date_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "ok"))
    monkeypatch.setattr(
        project_cli,
        "ensure_start_date_if_starting",
        lambda *a, **k: (False, "handoff date failed", False),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_outbox_entry(
            op="handoff",
            payload={"next": "verifier", "to": "in_progress", "note": "x"},
        ),
    )
    assert not ok and "start_date failed" in detail


# --- gh_project_adapter + atomics + recipes ---


def test_create_board_item_routes_to_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot(conventions={"item_kind_default": "draft"})
    called: list[str] = []

    def fake_draft(ssot, title, body):
        called.append("draft")
        return "DI_x", "raw", None

    monkeypatch.setattr(project_cli, "create_draft_item", fake_draft)
    item_id, raw, err = gha.create_board_item(ssot, "T", "B")
    assert called == ["draft"]
    assert item_id == "DI_x" and err is None


def test_item_start_date_value_non_dict() -> None:
    assert project_atomics.item_start_date_value(None) == ""
    assert project_atomics.item_start_date_value("not-a-dict") == ""  # type: ignore[arg-type]


def test_append_notes_helper_precheck_queues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    _mock_graphql(monkeypatch, remaining=50)
    ok, detail, code = project_recipes.append_notes_helper(
        tmp_path,
        ssot,
        VALID_PVTI,
        agent="implementer",
        text="queued via precheck",
        limit=50,
        skip_precheck=False,
    )
    assert not ok
    assert "queued to outbox" in detail
    assert code == project_cli.EXIT_QUEUED


def test_cmd_set_status_post_gh_rate_limit_returns_queued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Cover project_cli.cmd_set_status return after _try_queue_rate_limit (L861)."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "guard_write_or_queue", lambda *a, **k: None)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=1, stdout="", stderr="API rate limit exceeded"
        ),
    )
    monkeypatch.setattr(
        project_cli,
        "_try_queue_rate_limit",
        lambda *a, **k: project_cli.EXIT_QUEUED,
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        last=False,
        to="ready",
        agent="implementer",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_QUEUED
