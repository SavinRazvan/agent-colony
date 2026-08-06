"""
File: test_drift_coverage_edges.py
Path: tests/modules/workflow_drift/test_drift_coverage_edges.py
Role: Edge-case coverage for drift_checks helpers and DRIFT-009/010 defensive paths.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_DIR))

import drift_checks  # noqa: E402
from drift_checks import (  # noqa: E402
    _load_board_snapshot,
    _open_pr_bodies,
    _parse_session_board_field,
    _path_exists,
    check_drift004b,
    check_drift009,
    check_drift010,
    drift_paths,
)


def _write_collab(
    tmp: Path,
    *,
    enabled: bool = True,
    policy: str = "board_only",
    raw: str | None = None,
    default_repo: str = "SavinRazvan/agent-colony",
) -> None:
    settings = tmp / ".local" / "user_settings"
    settings.mkdir(parents=True, exist_ok=True)
    path = settings / "github.collaboration.yaml"
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
        return
    data = {
        "version": 1,
        "owner": {"display_name": "T", "github_user": "@t"},
        "project_ssot": {
            "enabled": enabled,
            "sync_policy": policy,
            "default_repo": default_repo,
        },
        "commit_provenance": {"ai_disclosure_mode": "none"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _planning(tmp: Path, tracker: str = "# Work Tracker\n\n## Active\n\n(none)\n") -> None:
    planning = tmp / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True, exist_ok=True)
    (planning / "work-tracker.md").write_text(tracker, encoding="utf-8")
    (planning / "session-pointer.md").write_text(
        "| Field | Value |\n|-------|--------|\n| **Board** | |\n",
        encoding="utf-8",
    )


def test_path_exists_glob(tmp_path: Path) -> None:
    nested = tmp_path / "tests" / "modules" / "x"
    nested.mkdir(parents=True)
    (nested / "foo.py").write_text("#\n", encoding="utf-8")
    assert _path_exists(tmp_path, "tests/**/foo.py") is True
    assert _path_exists(tmp_path, "tests/**/missing.py") is False


def test_parse_session_board_no_pvti() -> None:
    assert _parse_session_board_field("Ready only") == (None, "")
    assert _parse_session_board_field("") == (None, "")


def test_load_ssot_policy_parse_and_non_mapping(tmp_path: Path) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, raw=": not: valid: [[[")
    ssot, detail = drift_checks._load_ssot_policy(drift_paths(tmp_path))
    assert ssot is None
    assert "cannot parse" in detail

    _write_collab(tmp_path, raw="- just a list\n")
    ssot, detail = drift_checks._load_ssot_policy(drift_paths(tmp_path))
    assert ssot is None
    assert "not a mapping" in detail


def test_load_ssot_policy_pyyaml_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path)
    import builtins

    real_import = builtins.__import__

    def blocker(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocker)
    ssot, detail = drift_checks._load_ssot_policy(drift_paths(tmp_path))
    assert ssot is None
    assert "PyYAML missing" in detail


def test_drift004b_skips_non_board_only(tmp_path: Path) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, policy="mirror")
    result = check_drift004b(drift_paths(tmp_path))
    assert result.passed
    assert "board/session check skipped" in result.detail


def test_drift009_skips_non_board_only(tmp_path: Path) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, policy="local")
    result = check_drift009(drift_paths(tmp_path))
    assert result.passed
    assert "dual-write check skipped" in result.detail


def test_drift009_fails_yaml_parse(tmp_path: Path) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, raw="{broken")
    result = check_drift009(drift_paths(tmp_path))
    assert not result.passed
    assert "cannot parse" in result.detail


def test_drift009_pyyaml_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path)
    import builtins

    real_import = builtins.__import__

    def blocker(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocker)
    result = check_drift009(drift_paths(tmp_path))
    assert result.passed
    assert "PyYAML missing" in result.detail


def test_load_board_snapshot_bad_json_and_non_object(tmp_path: Path) -> None:
    _planning(tmp_path)
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text("not-json", encoding="utf-8")
    data, detail = _load_board_snapshot(drift_paths(tmp_path))
    assert data is None
    assert "cannot read snapshot" in detail

    (gen / "project-board-snapshot.json").write_text("[1,2]", encoding="utf-8")
    data, detail = _load_board_snapshot(drift_paths(tmp_path))
    assert data is None
    assert "not an object" in detail


def test_open_pr_bodies_gh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="gh pr list failed"),
    )
    prs, err = _open_pr_bodies("o/r")
    assert prs == []
    assert err and "gh pr list failed" in err


def test_open_pr_bodies_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="gh", timeout=1)

    monkeypatch.setattr(subprocess, "run", boom)
    prs, err = _open_pr_bodies("o/r")
    assert prs == []
    assert err


def test_open_pr_bodies_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="{", stderr=""),
    )
    prs, err = _open_pr_bodies("o/r")
    assert prs == []
    assert err and "invalid JSON" in err


def test_open_pr_bodies_non_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=json.dumps({"x": 1}), stderr=""
        ),
    )
    prs, err = _open_pr_bodies("o/r")
    assert prs == []
    assert err and "did not return a list" in err


def test_open_pr_bodies_success_filters_non_dicts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps([{"number": 1, "body": "ok"}, "skip", 3]),
            stderr="",
        ),
    )
    prs, err = _open_pr_bodies("o/r")
    assert err is None
    assert prs == [{"number": 1, "body": "ok"}]


def test_drift010_board_item_linked_via_pr_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Hit Board-Item: regex path (line ~712) when in_review is properly linked."""
    _planning(tmp_path)
    _write_collab(tmp_path)
    item = "PVTI_lAHOBl46-84A9KZxlinked1"
    snap = {
        "schema": "project-board-snapshot/v1",
        "items": [
            {
                "id": item,
                "title": "Linked review",
                "status_normalized": "in_review",
                "body_excerpt": "PR open",
            }
        ],
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(
        drift_checks,
        "_open_pr_bodies",
        lambda repo: (
            [
                {
                    "number": 11,
                    "body": f"Board-Item: {item}\n## Summary",
                    "url": "https://x/y/pull/11",
                }
            ],
            None,
        ),
    )
    result = check_drift010(drift_paths(tmp_path))
    assert result.passed
    assert "no mismatches" in result.detail


def test_drift010_flags_in_review_without_open_pr(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path)
    snap = {
        "schema": "project-board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_lAHOBl46-84A9KZxinrev1",
                "title": "Review me",
                "status_normalized": "in_review",
                "body_excerpt": "working",
            },
            "skip-me",
        ],
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(
        drift_checks,
        "_open_pr_bodies",
        lambda repo: (
            [{"number": 9, "body": "unrelated PR", "url": "https://x/y/pull/9"}],
            None,
        ),
    )
    result = check_drift010(drift_paths(tmp_path))
    assert not result.passed
    assert "in_review without open PR" in result.detail


def test_drift010_warns_when_no_open_prs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path)
    snap = {
        "schema": "project-board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_lAHOBl46-84A9KZxwarn01",
                "title": "Review me",
                "status_normalized": "in_review",
                "body_excerpt": "working",
            }
        ],
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(drift_checks, "_open_pr_bodies", lambda repo: ([], None))
    result = check_drift010(drift_paths(tmp_path))
    assert not result.passed
    assert "0 open PRs" in result.detail


def test_drift010_flags_stale_in_progress(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path)
    snap = {
        "schema": "project-board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_lAHOBl46-84A9KZxstale1",
                "title": "Abandoned",
                "status_normalized": "in_progress",
                "body_excerpt": "(TBD)",
            }
        ],
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(
        drift_checks,
        "_open_pr_bodies",
        lambda repo: (
            [{"number": 2, "body": "other", "url": "https://x/y/pull/2"}],
            None,
        ),
    )
    result = check_drift010(drift_paths(tmp_path))
    assert not result.passed
    assert "stale in_progress" in result.detail


def test_drift010_skips_when_pr_list_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path)
    snap = {"schema": "project-board-snapshot/v1", "items": []}
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(
        drift_checks, "_open_pr_bodies", lambda repo: ([], "network down")
    )
    result = check_drift010(drift_paths(tmp_path))
    assert result.passed
    assert "cannot list open PRs" in result.detail


def test_drift010_repo_from_snapshot_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, default_repo="")
    snap = {
        "schema": "project-board-snapshot/v1",
        "project": {"default_repo": "org/from-snap"},
        "items": [],
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    seen: list[str] = []

    def capture(repo: str):
        seen.append(repo)
        return [], None

    monkeypatch.setattr(drift_checks, "_open_pr_bodies", capture)
    result = check_drift010(drift_paths(tmp_path))
    assert result.passed
    assert seen == ["org/from-snap"]


def test_drift010_skips_non_board_only(tmp_path: Path) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, policy="mirror")
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(
        json.dumps({"items": []}), encoding="utf-8"
    )
    result = check_drift010(drift_paths(tmp_path))
    assert result.passed
    assert "board/PR check skipped" in result.detail


def test_drift010_pyyaml_and_parse_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _planning(tmp_path)
    _write_collab(tmp_path, raw="{")
    result = check_drift010(drift_paths(tmp_path))
    assert not result.passed
    assert "cannot parse" in result.detail

    _write_collab(tmp_path)
    import builtins

    real_import = builtins.__import__

    def blocker(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocker)
    result = check_drift010(drift_paths(tmp_path))
    assert result.passed
    assert "PyYAML missing" in result.detail


def test_drift004b_fails_status_mismatch(tmp_path: Path) -> None:
    planning = tmp_path / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text(
        "# Work Tracker\n\n## Active\n\n(none)\n", encoding="utf-8"
    )
    (planning / "session-pointer.md").write_text(
        "| Field | Value |\n|-------|--------|\n"
        "| **Board** | PVTI_lAHOBl46-84A9KZxboard1 Ready |\n",
        encoding="utf-8",
    )
    _write_collab(tmp_path)
    snap = {
        "items": [
            {
                "id": "PVTI_lAHOBl46-84A9KZxboard1",
                "status_normalized": "in_progress",
                "status": "In Progress",
            }
        ]
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    result = check_drift004b(drift_paths(tmp_path))
    assert not result.passed
    assert "vs snapshot" in result.detail


def test_drift004b_passes_empty_pointer_status(tmp_path: Path) -> None:
    planning = tmp_path / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text(
        "# Work Tracker\n\n## Active\n\n(none)\n", encoding="utf-8"
    )
    (planning / "session-pointer.md").write_text(
        "| Field | Value |\n|-------|--------|\n"
        "| **Board** | PVTI_lAHOBl46-84A9KZxboard2 |\n",
        encoding="utf-8",
    )
    _write_collab(tmp_path)
    snap = {
        "items": [
            {
                "id": "PVTI_lAHOBl46-84A9KZxboard2",
                "status_normalized": "ready",
            }
        ]
    }
    gen = tmp_path / ".local" / "generated-data"
    gen.mkdir(parents=True)
    (gen / "project-board-snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
    result = check_drift004b(drift_paths(tmp_path))
    assert result.passed

