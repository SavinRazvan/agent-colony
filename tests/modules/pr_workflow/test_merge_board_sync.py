"""
File: test_merge_board_sync.py
Path: tests/modules/pr_workflow/test_merge_board_sync.py
Role: Unit tests for post-merge GitHub Project board sync in merge.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/merge.py
 - .ai_infra/install/cursor_workflow/project_cli.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PR_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"
_CW_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
for p in (_PR_DIR, _CW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import merge as merge_mod  # noqa: E402
import project_cli  # noqa: E402


SAMPLE_SSOT = {
    "enabled": True,
    "name": "Playground",
    "owner": "SavinRazvan",
    "number": 3,
    "url": "https://github.com/users/SavinRazvan/projects/3",
    "project_id": "PVT_kwHOBl46-84A9KZx",
    "default_repo": "SavinRazvan/mas-workflow-kit-project-ssot",
    "sync_policy": "board_only",
    "fields": {
        "status": {
            "field_id": "PVTSSF_status",
            "options": {
                "done": "98236657",
                "in_review": "4cc61d42",
            },
        },
    },
    "conventions": {"done_status": "done"},
}


def test_sync_board_skip_flag(tmp_path: Path) -> None:
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="1", merge_sha="abc", skip=True
    )
    assert "skipped" in line


def test_sync_board_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**SAMPLE_SSOT, "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    line = merge_mod.sync_board_after_merge(root=tmp_path, pr="1", merge_sha="abc")
    assert "not operational" in line


def test_sync_board_happy_with_item_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "98236657"))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [{"id": "PVTI_x", "content": {"body": "## Notes\n\n- old"}}],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "edit_item_body", lambda *a, **k: (True, "ok"))
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="42", merge_sha="deadbeef", item_id="PVTI_x"
    )
    assert "PVTI_x" in line
    assert "done" in line
    assert "Merged:" in line


def test_sync_board_warn_when_no_item(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: (None, [], "no project item found"),
    )
    line = merge_mod.sync_board_after_merge(root=tmp_path, pr="99", merge_sha="sha")
    assert "warn" in line
