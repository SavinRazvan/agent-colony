"""
File: test_merge_board_sync.py
Path: tests/modules/pr_workflow/test_merge_board_sync.py
Role: Unit tests for post-merge GitHub Project board sync in merge.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/merge.py
 - .ai_infra/install/agent_colony/project_cli.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PR_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"
_CW_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
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
    "default_repo": "SavinRazvan/agent-colony",
    "sync_policy": "board_only",
    "fields": {
        "status": {
            "field_id": "PVTSSF_status",
            "options": {
                "done": "98236657",
                "in_review": "4cc61d42",
            },
        },
        "priority": {
            "field_id": "PVTSSF_priority",
            "options": {"p1": "0a877460"},
        },
        "size": {
            "field_id": "PVTSSF_size",
            "options": {"s": "9592a5a3"},
        },
    },
    "conventions": {
        "done_status": "done",
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "require_attribution_on_exit": True,
    },
}

READY_BODY = (
    "## Acceptance\n\n- ok\n\n## Rollback\n\n- revert\n\n"
    "## Notes\n\n- @test/implementer · claimed\n"
)


def _ready_item(item_id: str = "PVTI_x") -> dict:
    return {
        "id": item_id,
        "status": "In review",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "content": {"body": READY_BODY},
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
        "fetch_project_item_by_id",
        lambda *a, **k: (_ready_item(), None),
    )
    monkeypatch.setattr(project_cli, "edit_item_body", lambda *a, **k: (True, "ok"))
    monkeypatch.setattr(
        project_cli,
        "format_note_line",
        lambda root, agent, text: f"@test/{agent} · {text}",
    )
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="42", merge_sha="deadbeef", item_id="PVTI_x"
    )
    assert "PVTI_x" in line
    assert "done" in line
    assert "Merged:" in line
    assert "@test/merge.py" in line


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


def test_sync_board_warn_edit_item_body_fails_after_set_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Status set succeeds; edit_item_body failure yields notes warn line."""
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "98236657"))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_item_by_id",
        lambda *a, **k: (_ready_item(), None),
    )
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (False, "graphql resolve failed"),
    )
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="7", merge_sha="abc123", item_id="PVTI_x"
    )
    assert "status→done on PVTI_x" in line
    assert "notes warn" in line
    assert "graphql resolve failed" in line
    err = capsys.readouterr().err
    assert "[WARN] board sync append-notes failed" in err


def test_sync_board_notes_via_edit_item_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """merge sync must call edit_item_body (which resolves DI_) for Notes."""
    edited: list[tuple] = []

    def capture_edit(ssot, item_id, body):
        edited.append((item_id, body))
        return True, "ok"

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "98236657"))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_item_by_id",
        lambda *a, **k: (_ready_item(), None),
    )
    monkeypatch.setattr(project_cli, "edit_item_body", capture_edit)
    monkeypatch.setattr(
        project_cli,
        "format_note_line",
        lambda root, agent, text: f"@test/{agent} · {text}",
    )
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="7", merge_sha="abc123", item_id="PVTI_x"
    )
    assert "Notes:" in line
    assert edited
    assert edited[0][0] == "PVTI_x"
    assert "Merged:" in edited[0][1]
    assert "abc123" in edited[0][1]
    assert "@test/merge.py" in edited[0][1]


def test_pr_url_passthrough_http(tmp_path: Path) -> None:
    url = "https://github.com/org/repo/pull/99"
    assert merge_mod._pr_url(tmp_path, url, "") == url


def test_pr_url_builds_from_gh_repo_view(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        merge_mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout="acme/kit\n", stderr=""
        ),
    )
    assert merge_mod._pr_url(tmp_path, "42", "") == "https://github.com/acme/kit/pull/42"


def test_pr_url_fallback_without_repo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        merge_mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="fail"),
    )
    assert merge_mod._pr_url(tmp_path, "#7", "") == "PR #7"


def test_sync_board_import_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import builtins

    real_import = builtins.__import__

    def blocker(name, *args, **kwargs):
        if name == "project_cli" or name.endswith(".project_cli"):
            raise ImportError("blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocker)
    # Force re-import path inside sync by temporarily removing from sys.modules
    saved = sys.modules.pop("project_cli", None)
    try:
        line = merge_mod.sync_board_after_merge(root=tmp_path, pr="1", merge_sha="x")
    finally:
        if saved is not None:
            sys.modules["project_cli"] = saved
    assert "project_cli unavailable" in line


def test_sync_board_candidates_in_warn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: (None, ["PVTI_a", "PVTI_b"], "ambiguous"),
    )
    line = merge_mod.sync_board_after_merge(root=tmp_path, pr="3", merge_sha="sha")
    assert "warn" in line
    assert "candidates=PVTI_a,PVTI_b" in line
    assert "candidates=" in capsys.readouterr().err


def test_sync_board_set_status_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_item_by_id",
        lambda *a, **k: (_ready_item(), None),
    )
    monkeypatch.setattr(
        project_cli, "set_item_status", lambda *a, **k: (False, "rate limited")
    )
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="1", merge_sha="abc", item_id="PVTI_x"
    )
    assert "set-status failed" in line
    assert "rate limited" in line
    assert "[WARN] board sync set-status failed" in capsys.readouterr().err


def test_sync_board_list_failure_before_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_item_by_id",
        lambda *a, **k: (None, "list boom"),
    )
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="1", merge_sha="abc", item_id="PVTI_x"
    )
    assert "fetch failed" in line
    assert "list boom" in line
    assert "[WARN] board sync fetch failed" in capsys.readouterr().err


def test_sync_board_body_gate_blocks_tbd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (SAMPLE_SSOT, []))
    tbd_item = {
        "id": "PVTI_x",
        "status": "In review",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "content": {
            "body": (
                "## Acceptance\n\n- (TBD)\n\n## Rollback\n\n- ok\n\n"
                "## Notes\n\n- @test/implementer · claimed\n"
            )
        },
    }
    monkeypatch.setattr(
        project_cli,
        "fetch_project_item_by_id",
        lambda *a, **k: (tbd_item, None),
    )
    called = {"status": False}

    def boom(*a, **k):
        called["status"] = True
        return True, "oid"

    monkeypatch.setattr(project_cli, "set_item_status", boom)
    line = merge_mod.sync_board_after_merge(
        root=tmp_path, pr="1", merge_sha="abc", item_id="PVTI_x"
    )
    assert "body gate failed" in line
    assert not called["status"]
    err = capsys.readouterr().err
    assert "[ERROR] board sync blocked" in err
    assert "set-section" in err


def test_merge_reload_sys_path_bootstrap() -> None:
    """Re-exec merge module body after stripping CW path (covers line 33 when absent)."""
    import importlib

    cw_resolved = _CW_DIR.resolve()
    sys.path[:] = [
        p for p in sys.path if not (p and Path(p).resolve() == cw_resolved)
    ]
    reloaded = importlib.reload(merge_mod)
    assert hasattr(reloaded, "sync_board_after_merge")
    # Ensure project_cli remains importable for later tests in this module
    if not any(p and Path(p).resolve() == cw_resolved for p in sys.path):
        sys.path.insert(0, str(cw_resolved))
    globals()["merge_mod"] = reloaded

