"""
File: test_project_promote.py
Path: tests/modules/install/test_project_promote.py
Role: Unit tests for Draft→Issue promote, mention-pr auto-promote, issue create.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_outbox.py
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
import project_outbox  # noqa: E402
from test_project_cli import SAMPLE_SSOT, VALID_PVTI  # noqa: E402
from test_project_outbox import VALID_ITEM_ID, _outbox_ssot, _valid_entry  # noqa: E402


def _ssot(**overrides):
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["default_repo"] = "SavinRazvan/agent-colony"
    data["conventions"] = {
        **data.get("conventions", {}),
        "promote_to_issue_on_pr": True,
        "item_kind_default": "draft",
        "body_sections": ["Acceptance", "Rollback", "Notes"],
    }
    data.update(overrides)
    if "conventions" in overrides:
        data["conventions"] = {**data["conventions"], **overrides["conventions"]}
    return data


def test_resolve_repository_id(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"data": {"repository": {"id": "R_repo123"}}}),
            stderr="",
        )

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    rid, err = project_cli.resolve_repository_id(_ssot(), "o/r")
    assert err is None
    assert rid == "R_repo123"
    # cache hit
    rid2, _ = project_cli.resolve_repository_id(_ssot(), "o/r")
    assert rid2 == "R_repo123"


def test_resolve_repository_id_missing() -> None:
    project_cli._REPO_ID_CACHE.clear()
    rid, err = project_cli.resolve_repository_id({**SAMPLE_SSOT, "default_repo": ""}, "")
    assert rid is None
    assert err and "repository required" in err


def test_promote_draft_graphql_args(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        joined = " ".join(args)
        if "repository(owner" in joined or "query($owner" in joined:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"data": {"repository": {"id": "R_abc"}}}),
                stderr="",
            )
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "data": {
                            "convertProjectV2DraftIssueItemToIssue": {
                                "item": {
                                    "id": VALID_PVTI,
                                    "content": {
                                        "__typename": "Issue",
                                        "number": 42,
                                        "url": "https://github.com/o/r/issues/42",
                                        "repository": {"nameWithOwner": "o/r"},
                                    },
                                }
                            }
                        }
                    }
                ),
                stderr="",
            )
        # resolve_item_content draft
        if "ProjectV2Item" in joined:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "data": {
                            "node": {
                                "content": {
                                    "__typename": "DraftIssue",
                                    "id": "DI_draft1",
                                    "title": "T",
                                    "body": "",
                                }
                            }
                        }
                    }
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = project_cli.promote_draft_item_to_issue(_ssot(), VALID_PVTI)
    assert ok
    assert "42" in detail
    assert meta["issue_number"] == "42"
    assert meta["item_id"] == VALID_PVTI
    mutate = [c for c in calls if any("convertProjectV2DraftIssueItemToIssue" in str(a) for a in c)]
    assert mutate
    flat = " ".join(mutate[0])
    assert f"input[itemId]={VALID_PVTI}" in flat
    assert "input[repositoryId]=R_abc" in flat


def test_promote_already_issue_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "9", {"repo": "o/r", "title": "T"}, None),
    )
    calls: list = []
    monkeypatch.setattr(
        project_cli, "run_gh", lambda *a, **k: calls.append(a) or SimpleNamespace(returncode=0, stdout="", stderr="")
    )
    ok, detail, meta = project_cli.promote_draft_item_to_issue(_ssot(), VALID_PVTI)
    assert ok
    assert meta.get("noop") is True
    assert "already Issue" in detail
    assert not calls


def test_cmd_promote_to_issue_happy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda ssot, iid, repo="": (
            True,
            "Issue #7",
            {
                "item_id": iid,
                "issue_number": "7",
                "url": "https://github.com/o/r/issues/7",
                "repo": "o/r",
                "noop": False,
            },
        ),
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, agent="implementer", repo="", limit=100
    )
    assert project_cli.cmd_promote_to_issue(args) == 0
    out = capsys.readouterr().out
    assert "Issue #7" in out
    assert "promoted" in out.lower() or "Issue" in out


def test_mention_pr_auto_promote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    promoted: list[str] = []

    def fake_promote(ssot, iid, repo=""):
        promoted.append(iid)
        return True, "Issue #1", {"issue_number": "1", "item_id": iid, "url": "u", "noop": False}

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {"number": 3, "url": "https://github.com/o/r/pull/3", "title": "x"}
            ),
            stderr="",
        ),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    monkeypatch.setattr(project_cli, "promote_draft_item_to_issue", fake_promote)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda ssot, limit=100: ([], None)
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, pr="3", agent="implementer", limit=100
    )
    assert project_cli.cmd_mention_pr(args) == 0
    assert promoted == [VALID_PVTI]


def test_mention_pr_convention_false_warns(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot(conventions={"promote_to_issue_on_pr": False})
    promoted: list = []
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {"number": 1, "url": "https://github.com/o/r/pull/1", "title": "x"}
            ),
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
        lambda *a, **k: promoted.append(1) or (True, "x", {}),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    monkeypatch.setattr(
        project_cli, "fetch_project_items", lambda ssot, limit=100: ([], None)
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, pr="1", agent="implementer", limit=100
    )
    assert project_cli.cmd_mention_pr(args) == 0
    assert not promoted
    assert "WARN" in capsys.readouterr().err


def test_create_board_item_issue_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["issue", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/o/r/issues/99\n",
                stderr="",
            )
        if args[:2] == ["project", "item-add"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"id": VALID_PVTI}),
                stderr="",
            )
        return SimpleNamespace(returncode=1, stdout="", stderr="bad")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ssot = _ssot(conventions={"item_kind_default": "issue"})
    item_id, raw, err = project_cli.create_board_item(ssot, "Title", "## Notes\n")
    assert err is None
    assert item_id == VALID_PVTI
    assert any(c[:2] == ["issue", "create"] for c in calls)
    assert any(c[:2] == ["project", "item-add"] for c in calls)
    assert not any(c[:2] == ["project", "item-create"] for c in calls)




def test_create_board_item_defaults_to_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing item_kind_default must create an Issue (not Draft)."""
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["issue", "create"]:
            return SimpleNamespace(
                returncode=0,
                stdout="https://github.com/o/r/issues/42\n",
                stderr="",
            )
        if args[:2] == ["project", "item-add"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"id": VALID_PVTI}),
                stderr="",
            )
        return SimpleNamespace(returncode=1, stdout="", stderr="bad")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ssot = _ssot(conventions={})  # no item_kind_default
    item_id, raw, err = project_cli.create_board_item(ssot, "Title", "## Notes\n")
    assert err is None
    assert item_id == VALID_PVTI
    assert any(c[:2] == ["issue", "create"] for c in calls)
    assert not any(c[:2] == ["project", "item-create"] for c in calls)

def test_apply_outbox_promote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["default_repo"] = "o/r"
    seen: list[str] = []

    def fake_promote(s, iid, repo=""):
        seen.append(iid)
        return True, "Issue #5", {
            "item_id": iid,
            "issue_number": "5",
            "url": "https://github.com/o/r/issues/5",
            "noop": False,
        }

    monkeypatch.setattr(project_cli, "promote_draft_item_to_issue", fake_promote)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="promote-to-issue", payload={"repo": "o/r"}),
    )
    assert ok
    assert seen == [VALID_ITEM_ID]


def test_enqueue_promote_op(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        agent="implementer",
        github_user="@test",
        op="promote-to-issue",
        item_id=VALID_ITEM_ID,
        payload={"repo": "o/r"},
    )
    assert not err
    assert entry is not None
    assert entry["op"] == "promote-to-issue"
