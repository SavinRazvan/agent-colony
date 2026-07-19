"""
File: test_project_tier1.py
Path: tests/modules/install/test_project_tier1.py
Role: Unit tests for Tier-1 board fields (start date, estimate, mention-pr).
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


def _tier1_ssot(**overrides):
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["fields"] = {
        **data["fields"],
        "start_date": {"field_id": "PVTF_start"},
        "end_date": {"field_id": "PVTF_end"},
        "estimate": {"field_id": "PVTF_estimate"},
    }
    data["conventions"] = {
        **data.get("conventions", {}),
        "set_start_date_on_claim": True,
        "claim": "set_assignee",
        "one_in_progress_per_assignee": False,
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "promote_to_issue_on_pr": True,
    }
    data["default_repo"] = "SavinRazvan/mas-workflow-kit-project-ssot"
    data.update(overrides)
    if "fields" in overrides:
        data["fields"] = {**data["fields"], **overrides["fields"]}
    if "conventions" in overrides:
        data["conventions"] = {**data["conventions"], **overrides["conventions"]}
    return data


def test_utc_today_iso_shape() -> None:
    day = project_cli.utc_today_iso()
    assert len(day) == 10
    assert day[4] == "-" and day[7] == "-"


def test_resolve_plain_field_id() -> None:
    ssot = _tier1_ssot()
    assert project_cli.resolve_plain_field_id(ssot, "estimate") == "PVTF_estimate"
    with pytest.raises(KeyError):
        project_cli.resolve_plain_field_id(SAMPLE_SSOT, "estimate")
    ssot_missing_id = json.loads(json.dumps(_tier1_ssot()))
    ssot_missing_id["fields"]["estimate"] = {}
    with pytest.raises(KeyError, match="field_id missing"):
        project_cli.resolve_plain_field_id(ssot_missing_id, "estimate")


def test_set_item_date_arg_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.set_item_date(
        _tier1_ssot(), VALID_PVTI, "start_date", "2026-07-18"
    )
    assert ok
    assert detail == "2026-07-18"
    assert calls[0][:2] == ["project", "item-edit"]
    assert "--date" in calls[0]
    assert "2026-07-18" in calls[0]
    assert "PVTF_start" in calls[0]


def test_set_item_date_rejects_bad_iso() -> None:
    ok, detail = project_cli.set_item_date(
        _tier1_ssot(), VALID_PVTI, "start_date", "18/07/2026"
    )
    assert not ok
    assert "YYYY-MM-DD" in detail


def test_set_item_number_arg_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail = project_cli.set_item_number(_tier1_ssot(), VALID_PVTI, "estimate", 3.0)
    assert ok
    assert detail == "3.0"
    assert "--number" in calls[0]
    assert "3.0" in calls[0]
    assert "PVTF_estimate" in calls[0]


def test_cmd_set_field_estimate_ok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[list[str]] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_tier1_ssot(), []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, field="estimate", to="3", agent="implementer"
    )
    assert project_cli.cmd_set_field(args) == 0
    assert "estimate → 3.0" in capsys.readouterr().out
    assert "--number" in calls[0]


def test_cmd_set_field_estimate_bad_to(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_tier1_ssot(), []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, field="estimate", to="nope", agent=None
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_USAGE


def test_cmd_set_field_estimate_negative(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_tier1_ssot(), []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, field="estimate", to="-1", agent=None
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_USAGE


def test_cmd_claim_sets_start_date(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _tier1_ssot()
    date_calls: list[tuple] = []

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": VALID_PVTI,
                    "title": "Work",
                    "status": "Ready",
                    "content": {"body": "## Acceptance\n\n## Rollback\n\n## Notes\n"},
                }
            ],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))

    def fake_date(ssot, item_id, field_key, date_iso):
        date_calls.append((item_id, field_key, date_iso))
        return True, date_iso

    monkeypatch.setattr(project_cli, "set_item_date", fake_date)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, agent="implementer", text="claimed", limit=100
    )
    assert project_cli.cmd_claim(args) == 0
    assert date_calls and date_calls[0][1] == "start_date"
    assert date_calls[0][2] == project_cli.utc_today_iso()
    assert "start_date=" in capsys.readouterr().out


def test_cmd_claim_start_date_warn_on_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _tier1_ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [{"id": VALID_PVTI, "title": "W", "status": "Ready", "content": {"body": "## Notes\n"}}],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli, "set_item_date", lambda *a, **k: (False, "gh date failed")
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, agent="implementer", text="claimed", limit=100
    )
    assert project_cli.cmd_claim(args) == 0
    err = capsys.readouterr().err
    assert "WARN" in err
    assert "start_date skipped" in err


def test_cmd_mention_pr_appends_notes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    notes: list[str] = []

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["pr", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 12,
                        "url": "https://github.com/o/r/pull/12",
                        "title": "Tier1",
                    }
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=1, stdout="", stderr="unexpected")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_tier1_ssot(), []))
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "I_x", {"title": "T"}, None),
    )

    def fake_notes(root, ssot, item_id, *, agent, text, limit=100):
        notes.append(text)
        return True, "updated", project_cli.EXIT_OK

    monkeypatch.setattr(project_cli, "append_notes_helper", fake_notes)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: (
            [
                {
                    "id": VALID_PVTI,
                    "title": "W",
                    "content": {"body": "PR 12: https://github.com/o/r/pull/12"},
                }
            ],
            None,
        ),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_PVTI, pr="12", agent="implementer", limit=100
    )
    assert project_cli.cmd_mention_pr(args) == 0
    assert notes and "https://github.com/o/r/pull/12" in notes[0]
    out = capsys.readouterr().out
    assert "mention-pr:" in out
    assert "find-by-pr" in out


def test_cmd_mention_pr_draft_warn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _tier1_ssot(conventions={"promote_to_issue_on_pr": False})
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
    assert "DraftIssue" in capsys.readouterr().err


def test_apply_outbox_set_field_estimate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["fields"] = {
        **ssot["fields"],
        "estimate": {"field_id": "PVTF_estimate"},
    }
    seen: list[float] = []

    def fake_number(s, iid, key, val):
        seen.append(val)
        return True, str(val)

    monkeypatch.setattr(project_cli, "set_item_number", fake_number)
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-field", payload={"field": "estimate", "to": 5}),
    )
    assert ok
    assert seen == [5.0]


def test_apply_outbox_claim_with_start_date(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["fields"] = {
        **ssot["fields"],
        "start_date": {"field_id": "PVTF_start"},
    }
    dates: list[str] = []
    monkeypatch.setattr(
        project_cli, "set_item_status", lambda *a, **k: (True, "47fc9ee4")
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_date",
        lambda s, iid, key, d: dates.append(d) or (True, d),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(
            op="claim",
            payload={
                "to": "in_progress",
                "text": "claimed",
                "start_date": "2026-07-18",
            },
        ),
    )
    assert ok
    assert detail == "claimed"
    assert dates == ["2026-07-18"]


def test_enqueue_allows_set_field_op(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        agent="implementer",
        github_user="@test",
        op="set-field",
        item_id=VALID_ITEM_ID,
        payload={"field": "estimate", "to": 2},
    )
    assert not err
    assert entry is not None
    assert entry["op"] == "set-field"
    assert entry["status"] == "pending"
