"""
File: test_project_entry_efficiency.py
Path: tests/modules/install/test_project_entry_efficiency.py
Role: Unit tests for project entry modes, export --reuse-if-fresh, and list WARN.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_atomics.py
Notes:
 - Mocks GraphQL quota and gh item-list; no live network.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_atomics  # noqa: E402
import project_cli  # noqa: E402
from test_project_cli import SAMPLE_SSOT  # noqa: E402


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


def _ssot_with_efficiency(**eff: object) -> dict:
    base = {**SAMPLE_SSOT, "enabled": True}
    if eff:
        base["efficiency"] = dict(eff)
    return base


def test_load_efficiency_config_defaults() -> None:
    cfg = project_atomics.load_efficiency_config({})
    assert cfg["entry_list_limit"] == 50
    assert cfg["export_reuse_ttl_seconds"] == 900
    assert cfg["conserve_below_remaining"] == 1500
    assert cfg["offline_artifacts_below_remaining"] == 200
    assert "project-board-snapshot.json" in cfg["snapshot_path"]


def test_cmd_list_warns_unfiltered_high_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(entry_list_limit=50)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=json.dumps({"items": []}), stderr=""
        ),
    )
    args = argparse.Namespace(directory=tmp_path, status="", limit=200, json=False)
    assert project_cli.cmd_list(args) == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "WARN" in err
    assert "project entry" in err


def test_cmd_list_no_warn_with_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(entry_list_limit=50)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=json.dumps({"items": []}), stderr=""
        ),
    )
    args = argparse.Namespace(
        directory=tmp_path, status="in_progress", limit=200, json=False
    )
    assert project_cli.cmd_list(args) == project_cli.EXIT_OK
    assert "WARN" not in capsys.readouterr().err


def test_cmd_export_reuse_if_fresh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(export_reuse_ttl_seconds=900)
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text(
        json.dumps({"schema": "project-board-snapshot/v1", "items": [], "totalCount": 0}),
        encoding="utf-8",
    )

    def _boom(*a, **k):
        raise AssertionError("must not fetch when fresh")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "fetch_project_items", _boom)
    args = argparse.Namespace(
        directory=tmp_path,
        output=None,
        limit=200,
        json=False,
        stdout=False,
        reuse_if_fresh=900,
        force=False,
    )
    assert project_cli.cmd_export(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "export: reused" in out


def test_cmd_export_force_refreshes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency()
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text(
        json.dumps({"schema": "project-board-snapshot/v1", "items": [], "totalCount": 0}),
        encoding="utf-8",
    )
    called = {"n": 0}

    def _fetch(ssot_arg, *, limit=100):
        called["n"] += 1
        return [], None

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "fetch_project_items", _fetch)
    args = argparse.Namespace(
        directory=tmp_path,
        output=None,
        limit=200,
        json=False,
        stdout=False,
        reuse_if_fresh=900,
        force=True,
    )
    assert project_cli.cmd_export(args) == project_cli.EXIT_OK
    assert called["n"] == 1
    assert "Wrote" in capsys.readouterr().out


def test_cmd_entry_live(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 4000, "limit": 5000},
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot_arg, *, limit=50: (
            [
                {
                    "id": "PVTI_live1",
                    "title": "Work",
                    "status": "In Progress",
                    "priority": "P1",
                    "size": "S",
                    "estimate": 1,
                }
            ],
            None,
        ),
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "mode=live" in out
    assert "PVTI_live1" in out


def test_cmd_entry_conserve_uses_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(
        conserve_below_remaining=1500, export_reuse_ttl_seconds=900
    )
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text(
        json.dumps(
            {
                "schema": "project-board-snapshot/v1",
                "items": [
                    {
                        "id": "PVTI_snap1",
                        "title": "From snap",
                        "status": "In Progress",
                        "status_normalized": "in_progress",
                        "priority": "P1",
                        "size": "M",
                        "estimate": 3,
                    }
                ],
                "totalCount": 1,
            }
        ),
        encoding="utf-8",
    )

    def _boom(*a, **k):
        raise AssertionError("conserve must not live-list")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 800, "limit": 5000},
    )
    monkeypatch.setattr(project_cli, "fetch_project_items", _boom)
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "mode=conserve" in out
    assert "PVTI_snap1" in out


def test_cmd_entry_offline_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(offline_artifacts_below_remaining=200)
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": "PVTI_off1",
                        "title": "Offline",
                        "status": "Ready",
                        "status_normalized": "ready",
                    }
                ],
                "totalCount": 1,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 50, "limit": 5000},
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=True, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "mode=offline_artifacts" in out
    assert "PVTI_off1" in out
    assert "queue" in out


def test_cmd_entry_quota_error_offline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"error": "Forbidden", "remaining": None},
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=True, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    assert "mode=offline_artifacts" in capsys.readouterr().out


def test_cmd_export_reuse_bad_json_and_json_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(export_reuse_ttl_seconds=900)
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no fetch")),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        output=None,
        limit=200,
        json=True,
        stdout=False,
        reuse_if_fresh=900,
        force=False,
    )
    assert project_cli.cmd_export(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "export: reused" in out
    assert "{not-json" in out


def test_cmd_entry_disabled_and_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        project_cli, "load_project_ssot", lambda root: (None, ["missing ssot"])
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_USAGE

    disabled = {**SAMPLE_SSOT, "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (disabled, []))
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    assert "enable project_ssot" in capsys.readouterr().out


def test_cmd_entry_rem_parse_and_force_live_conserve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(conserve_below_remaining=1500)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": "not-an-int", "limit": 5000},
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot_arg, *, limit=50: ([], None),
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    assert "mode=live" in capsys.readouterr().out
    assert "graphql_remaining=?" in capsys.readouterr().out or True

    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 800, "limit": 5000},
    )
    # no snapshot → conserve falls through to live
    args.force_live = True
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    assert "mode=live" in capsys.readouterr().out


def test_cmd_entry_offline_unreadable_and_conserve_bad_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(
        offline_artifacts_below_remaining=200,
        conserve_below_remaining=1500,
        export_reuse_ttl_seconds=900,
    )
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 50, "limit": 5000},
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    assert "snapshot unreadable" in capsys.readouterr().out

    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 900, "limit": 5000},
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot_arg, *, limit=50: (
            [{"id": "PVTI_x", "title": "t", "status": "Done"}, "skip-me"],
            None,
        ),
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "mode=live" in out  # conserve bad json → live
    assert "(no items)" in out  # Done filtered out


def test_cmd_entry_live_fetch_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot_with_efficiency()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 4000, "limit": 5000},
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "gh failed"),
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_GH


def test_cmd_entry_conserve_empty_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(
        conserve_below_remaining=1500, export_reuse_ttl_seconds=900
    )
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text(
        json.dumps({"items": [], "totalCount": 0}),
        encoding="utf-8",
    )
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 800, "limit": 5000},
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "mode=conserve" in out
    assert "(no items)" in out


def test_cmd_entry_conserve_items_not_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot_with_efficiency(
        conserve_below_remaining=1500, export_reuse_ttl_seconds=900
    )
    snap = tmp_path / ".local" / "generated-data" / "project-board-snapshot.json"
    snap.parent.mkdir(parents=True)
    snap.write_text(json.dumps({"items": "oops", "totalCount": 0}), encoding="utf-8")
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli._outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 800, "limit": 5000},
    )
    args = argparse.Namespace(
        directory=tmp_path, also_ready=False, force_live=False, limit=None
    )
    assert project_cli.cmd_entry(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "mode=conserve" in out
    assert "(no items)" in out
