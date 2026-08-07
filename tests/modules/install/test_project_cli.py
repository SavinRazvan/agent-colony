"""
File: test_project_cli.py
Path: tests/modules/install/test_project_cli.py
Role: Unit tests for project_ssot CLI (option mapping, disabled path, list filter).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/project_cli.py
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
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_cli  # noqa: E402

VALID_PVTI = "PVTI_lAHOBl46-84A9KZxcli01"


def _write_collab(tmp: Path, ssot: dict) -> None:
    path = tmp / ".local" / "user_settings" / "github.collaboration.yaml"
    path.parent.mkdir(parents=True)
    data = {
        "version": 1,
        "owner": {"display_name": "Test User", "github_user": "@test"},
        "project_ssot": ssot,
        "commit_provenance": {"ai_disclosure_mode": "assisted_by"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    # Minimal pr scripts so _import_user_settings can find the package when using real load —
    # tests monkeypatch load instead when needed.

SAMPLE_SSOT = {
    "enabled": True,
    "name": "Playground",
    "owner": "SavinRazvan",
    "default_repo": "SavinRazvan/agent-colony",
    "number": 3,
    "url": "https://github.com/users/SavinRazvan/projects/3",
    "project_id": "PVT_kwHOBl46-84A9KZx",
    "sync_policy": "board_only",
    "fallback": "local_trackers",
    # Unit tests expect immediate live writes; avoid low-quota precheck enqueueing
    # (which otherwise depends on the runner's current `gh api rate_limit` state).
    # Keep outbox enabled for "enqueue on GH throttle" tests, but disable
    # low-quota precheck enqueueing (it depends on the runner's current `gh`
    # GraphQL remaining value and is flaky).
    "outbox": {"enabled": True, "precheck_writes": False},
    "fields": {
        "status": {
            "field_id": "PVTSSF_status",
            "options": {
                "backlog": "f75ad846",
                "ready": "08afe404",
                "in_progress": "47fc9ee4",
                "in_review": "4cc61d42",
                "done": "98236657",
            },
        },
        "priority": {
            "field_id": "PVTSSF_priority",
            "options": {"p0": "79628723", "p1": "0a877460", "p2": "da944a9c"},
        },
        "size": {
            "field_id": "PVTSSF_size",
            "options": {"s": "9592a5a3", "m": "9728cbdc"},
        },
    },
    "conventions": {
        "body_sections": ["Acceptance", "Rollback"],
        "require_attribution_on_exit": True,
        "attribution_format": "{github_user}/{agent}",
    },
}


def test_resolve_status_option_id() -> None:
    assert project_cli.resolve_status_option_id(SAMPLE_SSOT, "ready") == "08afe404"
    assert project_cli.resolve_status_option_id(SAMPLE_SSOT, "in-progress") == "47fc9ee4"
    with pytest.raises(KeyError):
        project_cli.resolve_status_option_id(SAMPLE_SSOT, "nope")


def test_resolve_field_option_id() -> None:
    fid, oid = project_cli.resolve_field_option_id(SAMPLE_SSOT, "priority", "p1")
    assert fid == "PVTSSF_priority"
    assert oid == "0a877460"


def test_require_enabled_false() -> None:
    ssot = {**SAMPLE_SSOT, "enabled": False}
    errs = project_cli.require_enabled(ssot)
    assert errs
    assert "local_trackers" in errs[0]


def test_cmd_status_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**SAMPLE_SSOT, "enabled": False}
    monkeypatch.setattr(
        project_cli,
        "load_project_ssot",
        lambda root: (ssot, []),
    )
    args = argparse.Namespace(directory=tmp_path, json=False)
    assert project_cli.cmd_status(args) == 2


def test_cmd_set_status_maps_and_calls_gh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        to="in_progress",
    )
    assert project_cli.cmd_set_status(args) == 0
    assert calls
    assert "--single-select-option-id" in calls[0]
    assert "47fc9ee4" in calls[0]
    assert VALID_PVTI in calls[0]
    # Status must not GraphQL-resolve to DI_
    assert not any(c[:2] == ["api", "graphql"] for c in calls)
    assert not any(any(str(a).startswith("DI_") for a in c) for c in calls)


def test_set_item_status_uses_pvti_not_di(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.set_item_status(SAMPLE_SSOT, "PVTI_status_only", "done")
    assert ok
    assert detail == "98236657"
    assert calls and calls[0][:2] == ["project", "item-edit"]
    assert "PVTI_status_only" in calls[0]
    assert "--field-id" in calls[0]
    assert not any(c[:2] == ["api", "graphql"] for c in calls)
    assert "DI_" not in " ".join(calls[0])


def test_cmd_list_filters_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = {
        "items": [
            {"id": "a", "title": "Hello", "status": "Ready"},
            {"id": "b", "title": "Other", "status": "Backlog"},
        ]
    }

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    args = argparse.Namespace(directory=tmp_path, status="ready", limit=50, json=False)
    assert project_cli.cmd_list(args) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out and out[0].count("\t") == 5


def test_append_notes_to_body_idempotent() -> None:
    body, changed = project_cli.append_notes_to_body("", "Merged: https://example/pull/1 @ abc")
    assert changed
    assert "## Notes" in body
    assert "Merged:" in body
    body2, changed2 = project_cli.append_notes_to_body(body, "Merged: https://example/pull/1 @ abc")
    assert not changed2
    assert body2 == body


def test_parse_board_item_from_text() -> None:
    assert (
        project_cli.parse_board_item_from_text("- Board-Item: PVTI_abc123\n")
        == "PVTI_abc123"
    )
    assert project_cli.parse_board_item_from_text("no item") is None


def test_cmd_get(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "items": [
            {
                "id": VALID_PVTI,
                "title": "Slice",
                "status": "In progress",
                "content": {"body": "## Notes\n\nhello"},
            }
        ]
    }

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    args = argparse.Namespace(directory=tmp_path, id=VALID_PVTI, limit=50, json=True)
    assert project_cli.cmd_get(args) == 0


def test_cmd_append_notes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "items": [
            {
                "id": VALID_PVTI,
                "title": "Slice",
                "status": "In review",
                "content": {"body": "## Acceptance\n\nok"},
            }
        ]
    }
    calls: list[list[str]] = []
    gql = {
        "data": {
            "node": {
                "id": VALID_PVTI,
                "content": {
                    "__typename": "DraftIssue",
                    "id": "DI_draft_x",
                    "title": "Slice",
                    "body": "## Acceptance\n\nok",
                },
            }
        }
    }

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["project", "item-list"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
        if args[:2] == ["api", "graphql"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(gql), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_PVTI,
        text="Merged: url @ sha",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_append_notes(args) == 0
    assert any("--body" in c for c in calls)
    edit_calls = [c for c in calls if c[:2] == ["project", "item-edit"]]
    assert edit_calls
    assert "DI_draft_x" in edit_calls[0]
    assert "--title" in edit_calls[0]
    assert "Slice" in edit_calls[0]
    body_arg = edit_calls[0][edit_calls[0].index("--body") + 1]
    assert "@test/implementer" in body_arg


def test_edit_item_body_resolves_pvti_to_di(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    gql = {
        "data": {
            "node": {
                "content": {
                    "__typename": "DraftIssue",
                    "id": "DI_abc",
                    "title": "Card Title",
                    "body": "old",
                }
            }
        }
    }

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["api", "graphql"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(gql), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.edit_item_body(SAMPLE_SSOT, "PVTI_item", "new body")
    assert ok
    assert detail == "ok"
    edit = [c for c in calls if c[:2] == ["project", "item-edit"]][0]
    assert "DI_abc" in edit
    assert "--title" in edit
    assert "Card Title" in edit
    assert "new body" in edit
    assert "PVTI_item" not in edit  # body edit must not use PVTI_


def test_edit_item_body_accepts_di_directly(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["api", "graphql"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"data": {"node": {"id": "DI_only", "title": "T"}}}),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, _ = project_cli.edit_item_body(SAMPLE_SSOT, "DI_only", "body")
    assert ok
    edit = [c for c in calls if c[:2] == ["project", "item-edit"]][0]
    assert "DI_only" in edit


def test_edit_item_body_resolve_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.edit_item_body(SAMPLE_SSOT, "PVTI_missing", "x")
    assert not ok
    assert "boom" in detail


def test_resolve_draft_content(monkeypatch: pytest.MonkeyPatch) -> None:
    gql = {
        "data": {
            "node": {
                "content": {
                    "__typename": "DraftIssue",
                    "id": "DI_z",
                    "title": "Hello",
                }
            }
        }
    }

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(gql), stderr=""),
    )
    cid, title, err = project_cli.resolve_draft_content(SAMPLE_SSOT, "PVTI_z")
    assert err is None
    assert cid == "DI_z"
    assert title == "Hello"


def test_resolve_item_id_from_pr_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["pr", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 7,
                        "url": "https://github.com/o/r/pull/7",
                        "body": "- Board-Item: PVTI_from_pr\n",
                    }
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    item_id, cands, err = project_cli.resolve_item_id_for_pr(SAMPLE_SSOT, pr="7")
    assert item_id == "PVTI_from_pr"
    assert err is None
    assert cands == ["PVTI_from_pr"]


def test_find_items_mentioning_pr() -> None:
    items = [
        {
            "id": "a",
            "status": "In review",
            "title": "Work",
            "content": {"body": "See https://github.com/o/r/pull/9"},
        },
        {"id": "b", "status": "Done", "title": "Other", "content": {"body": "pull/9"}},
    ]
    matches = project_cli.find_items_mentioning_pr(
        items, pr_number="9", pr_url="https://github.com/o/r/pull/9"
    )
    assert matches[0]["id"] == "a"


def test_resolve_item_content_empty_id() -> None:
    kind, cid, meta, err = project_cli.resolve_item_content(SAMPLE_SSOT, "")
    assert kind is None
    assert cid is None
    assert meta is None
    assert err == "empty item id"


def test_resolve_item_content_unsupported_typename(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gql = {
        "data": {
            "node": {
                "content": {
                    "__typename": "PullRequest",
                    "id": "PR_abc",
                    "title": "Not editable",
                }
            }
        }
    }

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(gql), stderr=""),
    )
    kind, cid, meta, err = project_cli.resolve_item_content(SAMPLE_SSOT, "PVTI_pr")
    assert kind is None
    assert cid is None
    assert meta is None
    assert "unsupported content type" in (err or "")
    assert "PullRequest" in (err or "")


def test_edit_item_body_issue_backed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    gql = {
        "data": {
            "node": {
                "content": {
                    "__typename": "Issue",
                    "id": "I_ignored",
                    "number": 42,
                    "title": "Issue card",
                    "body": "old issue body",
                    "repository": {"nameWithOwner": "SavinRazvan/repo"},
                }
            }
        }
    }

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["api", "graphql"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(gql), stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.edit_item_body(SAMPLE_SSOT, "PVTI_issue", "new issue body")
    assert ok
    assert detail == "ok"
    issue_edit = [c for c in calls if c[:2] == ["issue", "edit"]]
    assert issue_edit
    assert "42" in issue_edit[0]
    assert "--body" in issue_edit[0]
    assert "new issue body" in issue_edit[0]
    assert "--repo" in issue_edit[0]
    assert "SavinRazvan/repo" in issue_edit[0]
    assert not any(c[:2] == ["project", "item-edit"] for c in calls)


def test_edit_item_body_graphql_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    gql = {"errors": [{"message": "Resource not accessible by integration"}]}

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(gql), stderr=""),
    )
    ok, detail = project_cli.edit_item_body(SAMPLE_SSOT, "PVTI_bad", "body")
    assert not ok
    assert "Resource not accessible" in detail


def test_cmd_append_notes_idempotent_skip_with_di_resolve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Idempotent skip must not call item-edit even when DI resolve would run."""
    fixed_ts = "2026-07-18T10:14:40Z"
    monkeypatch.setattr(project_cli, "utc_note_timestamp", lambda: fixed_ts)
    note = f"@test/implementer · {fixed_ts} · Merged: https://example/pull/1 @ abc"
    payload = {
        "items": [
            {
                "id": VALID_PVTI,
                "title": "Slice",
                "status": "In review",
                "content": {"body": f"## Notes\n\n- {note}"},
            }
        ]
    }
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        if args[:2] == ["project", "item-list"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
        if args[:2] == ["api", "graphql"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "data": {
                            "node": {
                                "content": {
                                    "__typename": "DraftIssue",
                                    "id": "DI_draft_x",
                                    "title": "Slice",
                                }
                            }
                        }
                    }
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, text=note, agent="implementer", limit=50
    )
    assert project_cli.cmd_append_notes(args) == 0
    assert not any(c[:2] == ["project", "item-edit"] for c in calls)
    assert not any(c[:2] == ["issue", "edit"] for c in calls)


def test_format_agent_attribution_and_note_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixed_ts = "2026-07-18T10:14:40Z"
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@SavinRazvan")
    monkeypatch.setattr(project_cli, "utc_note_timestamp", lambda: fixed_ts)
    assert project_cli.format_agent_attribution(tmp_path, "implementer") == (
        "@SavinRazvan/implementer"
    )
    line = project_cli.format_note_line(tmp_path, "implementer", "claimed")
    assert line == f"@SavinRazvan/implementer · {fixed_ts} · claimed"
    stamped = project_cli.format_note_line(
        tmp_path,
        "implementer",
        f"@SavinRazvan/implementer · {fixed_ts} · claimed",
    )
    assert stamped == f"@SavinRazvan/implementer · {fixed_ts} · claimed"
    restamped = project_cli.format_note_line(
        tmp_path,
        "implementer",
        f"@SavinRazvan/implementer · {fixed_ts} · claimed",
    )
    assert restamped == stamped


def test_format_note_line_adds_timestamp_to_existing_attribution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixed_ts = "2026-07-18T10:14:40Z"
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@SavinRazvan")
    monkeypatch.setattr(project_cli, "utc_note_timestamp", lambda: fixed_ts)
    line = project_cli.format_note_line(
        tmp_path, "implementer", "@SavinRazvan/implementer · claimed"
    )
    assert line == f"@SavinRazvan/implementer · {fixed_ts} · claimed"


def test_format_note_line_empty_text_stamps_attribution_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixed_ts = "2026-07-18T10:14:40Z"
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@SavinRazvan")
    monkeypatch.setattr(project_cli, "utc_note_timestamp", lambda: fixed_ts)
    line = project_cli.format_note_line(tmp_path, "implementer", "")
    assert line == f"@SavinRazvan/implementer · {fixed_ts}"


def test_cmd_append_notes_requires_agent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, text="no agent", agent="", limit=50
    )
    assert project_cli.cmd_append_notes(args) == 2


def test_set_item_assignee_draft_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    ok, detail = project_cli.set_item_assignee(SAMPLE_SSOT, VALID_PVTI, "SavinRazvan")
    assert not ok
    assert "DraftIssue" in detail


def test_set_item_assignee_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: (
            "issue",
            "42",
            {"title": "T", "repo": "org/repo"},
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.set_item_assignee(SAMPLE_SSOT, VALID_PVTI, "@alice")
    assert ok
    assert detail == "alice"
    assert calls[0][:3] == ["issue", "edit", "42"]
    assert "--add-assignee" in calls[0]
    assert "alice" in calls[0]


def test_cmd_export_stdout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "items": [
            {"id": "a", "title": "T", "status": "Ready", "content": {"body": "x" * 600}}
        ]
    }

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    args = argparse.Namespace(
        directory=tmp_path, output=None, limit=50, json=False, stdout=True
    )
    assert project_cli.cmd_export(args) == 0