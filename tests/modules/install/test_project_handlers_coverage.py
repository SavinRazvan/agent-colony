"""
File: test_project_handlers_coverage.py
Path: tests/modules/install/test_project_handlers_coverage.py
Role: Error-path coverage for project_handlers.py (mention-pr, promote-to-issue, doctor).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_handlers.py
Notes:
 - Calls handlers directly; monkeypatches project_cli facade.
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
import project_handlers  # noqa: E402
import project_outbox  # noqa: E402
from test_project_cli import SAMPLE_SSOT, VALID_PVTI  # noqa: E402


def _ssot(**overrides: object) -> dict:
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["default_repo"] = "SavinRazvan/mas-workflow-kit-project-ssot"
    data["conventions"] = {
        **data.get("conventions", {}),
        "promote_to_issue_on_pr": True,
        "body_sections": ["Acceptance", "Rollback", "Notes"],
    }
    data.update(overrides)
    if "conventions" in overrides:
        data["conventions"] = {**data["conventions"], **overrides["conventions"]}  # type: ignore[arg-type]
    return data


def test_run_mention_pr_ssot_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (None, project_cli.EXIT_USAGE),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_USAGE


def test_run_mention_pr_missing_item_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (None, project_cli.EXIT_USAGE),
    )
    args = argparse.Namespace(directory=tmp_path, id="", pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_USAGE


def test_run_mention_pr_missing_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_USAGE


def test_run_mention_pr_missing_pr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_USAGE


def test_run_mention_pr_gh_view_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="pr view failed"),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_GH


def test_run_mention_pr_invalid_pr_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="not-json", stderr=""),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_GH


def test_run_mention_pr_missing_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps({"number": 1}), stderr=""),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_GH


def test_run_mention_pr_promote_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (False, "promote failed", {}),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: None)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_GH


def test_run_mention_pr_append_notes_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            stdout=json.dumps({"number": 2, "url": "https://github.com/o/r/pull/2"}),
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
        lambda *a, **k: (False, "notes failed", project_cli.EXIT_GH),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: None)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="2", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_GH


def test_run_mention_pr_find_by_pr_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            stdout=json.dumps({"number": 5, "url": "https://github.com/o/r/pull/5"}),
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
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([{"id": "PVTI_other"}], None),
    )
    monkeypatch.setattr(
        project_cli,
        "find_items_mentioning_pr",
        lambda items, pr_number="", pr_url="": [{"id": "PVTI_other"}],
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="5", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_OK
    assert "find-by-pr candidates" in capsys.readouterr().out


def test_run_promote_to_issue_ssot_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (None, project_cli.EXIT_USAGE),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_USAGE


def test_run_promote_to_issue_missing_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_USAGE


def test_run_promote_to_issue_promote_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (False, "promote failed", {}),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: None)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_GH


def test_run_promote_to_issue_noop_already_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            "already Issue #9",
            {"item_id": VALID_PVTI, "issue_number": "9", "url": "u", "noop": True},
        ),
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (False, "draft skip"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_OK
    assert "already Issue" in capsys.readouterr().out


def test_run_promote_to_issue_assignee_warn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            "Issue #3",
            {"item_id": VALID_PVTI, "issue_number": "3", "url": "u", "noop": False},
        ),
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (False, "assignee failed"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_OK
    assert "assignee skipped" in capsys.readouterr().err


def test_run_promote_to_issue_notes_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            "Issue #4",
            {"item_id": VALID_PVTI, "issue_number": "4", "url": "u", "noop": False},
        ),
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes failed", project_cli.EXIT_NOT_FOUND),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_NOT_FOUND


def test_run_doctor_warns_missing_tier1_fields(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot(fields={**SAMPLE_SSOT["fields"], "start_date": {}, "estimate": {}})
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items":[]}', stderr=""),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )
    args = argparse.Namespace(directory=REPO_ROOT)
    assert project_handlers.run_doctor(args) == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "fields.start_date.field_id missing" in err
    assert "fields.estimate.field_id missing" in err


def test_run_mention_pr_promote_queued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (False, "rate limited", {}),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_QUEUED


def test_run_mention_pr_notes_queued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
        lambda *a, **k: (False, "rate limited", project_cli.EXIT_GH),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100)
    assert project_handlers.run_mention_pr(args) == project_cli.EXIT_QUEUED


def test_run_promote_to_issue_missing_item_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (None, project_cli.EXIT_USAGE),
    )
    args = argparse.Namespace(directory=tmp_path, id="", agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_USAGE


def test_run_promote_to_issue_promote_queued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_arg",
        lambda root, args, cmd: (VALID_PVTI, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (False, "rate limited", {}),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_QUEUED


def test_run_promote_to_issue_resolve_user_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            "Issue #2",
            {"item_id": VALID_PVTI, "issue_number": "2", "url": "u", "noop": False},
        ),
    )
    calls = {"n": 0}

    def flaky_user(root: Path) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return "@test"

    monkeypatch.setattr(project_cli, "resolve_human_github_user", flaky_user)
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_OK


def test_run_promote_to_issue_notes_queued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (_ssot(), []))
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
            "Issue #6",
            {"item_id": VALID_PVTI, "issue_number": "6", "url": "u", "noop": False},
        ),
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "rate limited", project_cli.EXIT_GH),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100)
    assert project_handlers.run_promote_to_issue(args) == project_cli.EXIT_QUEUED
    assert "QUEUED" in capsys.readouterr().err


def test_run_doctor_warns_missing_default_repo(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot(default_repo="")
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items":[]}', stderr=""),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )
    args = argparse.Namespace(directory=REPO_ROOT)
    assert project_handlers.run_doctor(args) == project_cli.EXIT_OK
    assert "default_repo missing" in capsys.readouterr().err


def test_run_doctor_prints_tier1_field_ids(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot(
        fields={
            **SAMPLE_SSOT["fields"],
            "start_date": {"field_id": "PVTF_start"},
            "estimate": {"field_id": "PVTF_estimate"},
        }
    )
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items":[]}', stderr=""),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )
    args = argparse.Namespace(directory=REPO_ROOT)
    assert project_handlers.run_doctor(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "tier1.start_date: PVTF_start" in out
    assert "tier1.estimate: PVTF_estimate" in out


def test_run_close_linked_issue_flag_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": False}), []),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_OK
    assert "SKIPPED" in capsys.readouterr().out


def test_run_close_linked_issue_ssot_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (None, project_cli.EXIT_USAGE),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_USAGE


def test_run_close_linked_issue_missing_pr(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    args = argparse.Namespace(directory=tmp_path, pr="", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_USAGE


def test_run_close_linked_issue_no_linked_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (None, [], "no project item found for this PR"),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_OK
    assert "SKIPPED" in capsys.readouterr().out


def test_run_close_linked_issue_no_linked_issue_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (VALID_PVTI, [VALID_PVTI], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda ssot, item_id: ("draft", "DI_x", {"title": "Draft-only"}, None),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_OK
    assert "SKIPPED" in capsys.readouterr().out


def test_run_close_linked_issue_already_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (VALID_PVTI, [VALID_PVTI], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda ssot, item_id: ("issue", "84", {"repo": "org/repo"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"state": "CLOSED"}', stderr=""),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_OK
    assert "already closed" in capsys.readouterr().out


def test_run_close_linked_issue_view_fails_deferred(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (VALID_PVTI, [VALID_PVTI], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda ssot, item_id: ("issue", "84", {"repo": "org/repo"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="rate limited"),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_GH
    assert "DEFERRED" in capsys.readouterr().out


def test_run_close_linked_issue_dry_run_open_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (VALID_PVTI, [VALID_PVTI], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda ssot, item_id: ("issue", "84", {"repo": "org/repo"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"state": "OPEN"}', stderr=""),
    )
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=True)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_OK
    assert "DRY-RUN" in capsys.readouterr().out


def test_run_close_linked_issue_closes_open_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (VALID_PVTI, [VALID_PVTI], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda ssot, item_id: ("issue", "84", {"repo": "org/repo"}, None),
    )
    calls: list[list[str]] = []

    def _fake_run_gh(cmd_args: list[str]) -> SimpleNamespace:
        calls.append(cmd_args)
        if cmd_args[:2] == ["issue", "view"]:
            return SimpleNamespace(returncode=0, stdout='{"state": "OPEN"}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", _fake_run_gh)
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_OK
    assert "PASS" in capsys.readouterr().out
    assert any(c[:2] == ["issue", "close"] for c in calls)


def test_run_close_linked_issue_close_fails_deferred(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (_ssot(conventions={"close_linked_issue_on_cleanup": True}), []),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda ssot, pr, repo=None, limit=100: (VALID_PVTI, [VALID_PVTI], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda ssot, item_id: ("issue", "84", {"repo": "org/repo"}, None),
    )

    def _fake_run_gh(cmd_args: list[str]) -> SimpleNamespace:
        if cmd_args[:2] == ["issue", "view"]:
            return SimpleNamespace(returncode=0, stdout='{"state": "OPEN"}', stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="permission denied")

    monkeypatch.setattr(project_cli, "run_gh", _fake_run_gh)
    args = argparse.Namespace(directory=tmp_path, pr="162", repo="", dry_run=False)
    assert project_handlers.run_close_linked_issue(args) == project_cli.EXIT_GH
    assert "DEFERRED" in capsys.readouterr().out
