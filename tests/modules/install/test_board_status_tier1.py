"""
File: test_board_status_tier1.py
Path: tests/modules/install/test_board_status_tier1.py
Role: Unit tests for empty-Status detection, heal-cards, and completeness helpers.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/project_atomics.py
 - .ai_infra/install/agent_colony/project_handlers.py
 - .ai_infra/install/agent_colony/project_cli.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_CW = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_CW) not in sys.path:
    sys.path.insert(0, str(_CW))

import project_atomics as pa  # noqa: E402
import project_cli  # noqa: E402
import project_handlers  # noqa: E402

SAMPLE_SSOT = {
    "enabled": True,
    "name": "Playground",
    "owner": "SavinRazvan",
    "number": 3,
    "url": "https://github.com/users/SavinRazvan/projects/3",
    "project_id": "PVT_kwHOBl46-84A9KZx",
    "default_repo": "SavinRazvan/agent-colony",
    "sync_policy": "board_only",
    "fields": {
        "status": {
            "field_id": "PVTSSF_status",
            "options": {
                "ready": "08afe404",
                "done": "98236657",
                "in_progress": "47fc9ee4",
                "in_review": "4cc61d42",
            },
        },
        "priority": {
            "field_id": "PVTSSF_priority",
            "options": {"p1": "0a877460", "p2": "p2id"},
        },
        "size": {
            "field_id": "PVTSSF_size",
            "options": {"s": "9592a5a3"},
        },
        "estimate": {"field_id": "PVTF_estimate"},
        "end_date": {"field_id": "PVTF_end"},
    },
    "conventions": {
        "done_status": "done",
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "require_attribution_on_exit": False,
        "set_end_date_on_done": True,
    },
}


def test_collect_validate_missing_status_flags_tier1() -> None:
    item = {
        "id": "PVTI_x",
        "title": "orphan",
        "content": {
            "body": "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n",
            "state": "CLOSED",
        },
    }
    problems, warnings = pa.collect_validate_item_problems(SAMPLE_SSOT, item)
    assert "missing Status" in problems
    assert "missing Priority" in problems
    assert "missing Size" in problems
    assert "missing Estimate" in problems
    assert any("CLOSED" in w for w in warnings)


def test_summarize_card_completeness_counts() -> None:
    items = [
        {
            "id": "PVTI_a",
            "title": "a",
            "status": "",
            "content": {"body": "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n", "state": "CLOSED"},
        },
        {
            "id": "PVTI_b",
            "title": "b",
            "status": "Done",
            "priority": "p1",
            "size": "s",
            "estimate": "1",
            "content": {
                "body": (
                    "## Acceptance\n\n- ok\n\n## Rollback\n\n- revert\n\n"
                    "## Notes\n\n- @u/a · note\n"
                ),
                "state": "CLOSED",
            },
        },
    ]
    summary = pa.summarize_card_completeness(SAMPLE_SSOT, items)
    assert summary["total"] == 2
    assert summary["empty_status"] == 1
    assert summary["closed_not_done"] == 1
    assert summary["incomplete"] >= 1


def test_collect_validate_done_missing_end_date() -> None:
    item = {
        "id": "PVTI_done",
        "title": "done no end",
        "status": "Done",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "start date": "2026-08-01",
        "content": {
            "body": (
                "## Acceptance\n\n- ok\n\n## Rollback\n\n- revert\n\n"
                "## Notes\n\n- @u/a · note\n"
            ),
            "state": "CLOSED",
        },
    }
    problems, warnings = pa.collect_validate_item_problems(SAMPLE_SSOT, item)
    assert "missing End date" in problems


def test_ensure_end_date_and_classify_missing_flag() -> None:
    item = {
        "id": "PVTI_done",
        "title": "done",
        "status": "Done",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "start date": "2026-08-01",
        "content": {
            "body": (
                "## Acceptance\n\n- ok\n\n## Rollback\n\n- revert\n\n"
                "## Notes\n\n- @u/a · note\n"
            ),
            "state": "CLOSED",
        },
    }
    row = pa.classify_card_completeness(SAMPLE_SSOT, item)
    assert row["missing_end_date"] is True
    summary = pa.summarize_card_completeness(SAMPLE_SSOT, [item])
    assert summary["missing_end_date"] == 1


def test_heal_cards_check_and_dry_run_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    items = [
        {
            "id": "PVTI_heal",
            "title": "broken",
            "status": "",
            "priority": "p1",
            "size": "s",
            "estimate": "1",
            "content": {
                "body": "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n",
                "state": "CLOSED",
            },
        }
    ]
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (SAMPLE_SSOT, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(project_cli, "fetch_project_items", lambda ssot, limit=200: (items, None))
    args = argparse.Namespace(
        directory=tmp_path,
        apply=False,
        fill_tier1=False,
        dry_run=False,
        limit=50,
        json=False,
        agent="heal-cards",
    )
    assert project_handlers.run_heal_cards(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "incomplete=" in out
    assert "PVTI_heal" in out

    args.apply = True
    args.dry_run = True
    assert project_handlers.run_heal_cards(args) == project_cli.EXIT_OK
    assert "DRY-RUN" in capsys.readouterr().out


def test_heal_cards_json_check(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (SAMPLE_SSOT, project_cli.EXIT_OK),
    )
    monkeypatch.setattr(project_cli, "fetch_project_items", lambda ssot, limit=200: ([], None))
    args = argparse.Namespace(
        directory=tmp_path,
        apply=False,
        fill_tier1=False,
        dry_run=False,
        limit=50,
        json=True,
        agent="heal-cards",
    )
    assert project_handlers.run_heal_cards(args) == project_cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 0


def test_cmd_heal_cards_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"n": 0}

    def fake_run(args: argparse.Namespace) -> int:
        called["n"] += 1
        return project_cli.EXIT_OK

    monkeypatch.setattr(project_handlers, "run_heal_cards", fake_run)
    assert project_cli.cmd_heal_cards(argparse.Namespace()) == project_cli.EXIT_OK
    assert called["n"] == 1
