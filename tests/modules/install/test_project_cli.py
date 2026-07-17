"""
File: test_project_cli.py
Path: tests/modules/install/test_project_cli.py
Role: Unit tests for project_ssot CLI (option mapping, disabled path, list filter).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
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

import project_cli  # noqa: E402


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
    "number": 3,
    "url": "https://github.com/users/SavinRazvan/projects/3",
    "project_id": "PVT_kwHOBl46-84A9KZx",
    "sync_policy": "board_only",
    "fallback": "local_trackers",
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
    "conventions": {"body_sections": ["Acceptance", "Rollback"]},
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
        id="PVTI_test",
        to="in_progress",
    )
    assert project_cli.cmd_set_status(args) == 0
    assert calls
    assert "--single-select-option-id" in calls[0]
    assert "47fc9ee4" in calls[0]


def test_cmd_list_filters_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
    args = argparse.Namespace(directory=tmp_path, status="ready", limit=50, json=True)
    assert project_cli.cmd_list(args) == 0
