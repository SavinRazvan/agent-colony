"""
File: test_plan_cli.py
Path: tests/modules/canvas_artifacts/test_plan_cli.py
Role: Tests for plan snapshot CLI.
Used By:
 - pytest
Depends On:
 - plan_manage
Notes:
 - Uses temporary plan sources and .local/plans layout.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"


def _load(name: str):
    if str(PKG) not in sys.path:
        sys.path.insert(0, str(PKG))
    spec = importlib.util.spec_from_file_location(name, PKG / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_lwp(root: Path) -> None:
    pr = root / ".ai_infra" / "scripts" / "pr"
    pr.mkdir(parents=True)
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "local_workflow_paths.py"
    (pr / "local_workflow_paths.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    ui = root / ".ai_infra" / "templates" / "local-workspace" / "exemplars"
    ui.mkdir(parents=True)
    idx = REPO_ROOT / ".ai_infra" / "templates" / "local-workspace" / "exemplars" / "local-plans-index.md"
    (ui / "local-plans-index.md").write_text(idx.read_text(encoding="utf-8"), encoding="utf-8")


def test_snapshot_from_plan_md(tmp_path: Path) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    plan_dir = tmp_path / ".local" / "index-and-planning" / "current"
    plan_dir.mkdir(parents=True)
    (plan_dir / "plan.md").write_text("# Plan\n\nSlice work.\n", encoding="utf-8")

    dst, meta = manage.snapshot_plan(tmp_path, slug="slice-one", from_spec="plan.md", agent="implementer")
    assert dst.is_file()
    assert meta is not None and meta.is_file()
    assert "Slice work" in dst.read_text(encoding="utf-8")


def test_snapshot_from_cursor_plan(tmp_path: Path, monkeypatch) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    cursor_plans = tmp_path / "cursor-plans"
    cursor_plans.mkdir()
    (cursor_plans / "my-plan.plan.md").write_text("# Cursor plan\n", encoding="utf-8")
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_plans_dir", lambda: cursor_plans)

    dst, _ = manage.snapshot_plan(tmp_path, slug="my-plan", from_spec="cursor-plan:my-plan")
    assert dst.is_file()
    assert "# Cursor plan" in dst.read_text(encoding="utf-8")


def test_list_snapshots(tmp_path: Path) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    plan_dir = tmp_path / ".local" / "index-and-planning" / "current"
    plan_dir.mkdir(parents=True)
    (plan_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    manage.snapshot_plan(
        tmp_path,
        slug="alpha",
        agent="implementer",
        board_item="PVTI_test",
    )
    rows = manage.list_snapshots(tmp_path)
    assert len(rows) == 1
    assert rows[0]["slug"] == "alpha"
    assert rows[0]["agent"] == "implementer"
    assert rows[0]["board_item"] == "PVTI_test"
    assert rows[0]["source"]  # absolute path to plan.md


def _write_snapshot(plans_dir: Path, base: str, slug: str, body: str) -> Path:
    path = plans_dir / f"{base}.plan.md"
    path.write_text(body, encoding="utf-8")
    meta_path = plans_dir / f"{base}.meta.yaml"
    meta_path.write_text(f"slug: {slug}\n", encoding="utf-8")
    return path


def test_find_latest_snapshot(tmp_path: Path) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    plans_dir = tmp_path / ".local" / "plans"
    plans_dir.mkdir(parents=True)
    older = _write_snapshot(plans_dir, "2026-08-01-alpha", "alpha", "older\n")
    newer = _write_snapshot(plans_dir, "2026-08-05-alpha", "alpha", "newer\n")
    import os
    import time

    os.utime(older, (time.time() - 3600, time.time() - 3600))
    os.utime(newer, (time.time(), time.time()))

    latest = manage.find_latest_snapshot(tmp_path, "alpha")
    assert latest == newer
    assert "newer" in latest.read_text(encoding="utf-8")


def test_open_plan_copies(tmp_path: Path, monkeypatch) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    plans_dir = tmp_path / ".local" / "plans"
    plans_dir.mkdir(parents=True)
    _write_snapshot(plans_dir, "2026-08-05-bridge", "bridge", "---\nname: bridge\n---\n# Plan\n")

    cursor_plans = tmp_path / "cursor-plans"
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_plans_dir", lambda: cursor_plans)

    dest = manage.open_plan(tmp_path, slug="bridge")
    assert dest == cursor_plans / "bridge.plan.md"
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == (plans_dir / "2026-08-05-bridge.plan.md").read_text(encoding="utf-8")


def test_open_plan_requires_force(tmp_path: Path, monkeypatch) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    plans_dir = tmp_path / ".local" / "plans"
    plans_dir.mkdir(parents=True)
    _write_snapshot(plans_dir, "2026-08-05-force", "force-test", "v1\n")

    cursor_plans = tmp_path / "cursor-plans"
    cursor_plans.mkdir()
    (cursor_plans / "force-test.plan.md").write_text("existing\n", encoding="utf-8")
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_plans_dir", lambda: cursor_plans)

    import pytest

    with pytest.raises(ValueError, match="--force"):
        manage.open_plan(tmp_path, slug="force-test")

    dest = manage.open_plan(tmp_path, slug="force-test", force=True)
    assert "v1" in dest.read_text(encoding="utf-8")


def test_open_plan_missing_slug(tmp_path: Path) -> None:
    manage = _load("plan_manage")
    _seed_lwp(tmp_path)
    import pytest

    with pytest.raises(FileNotFoundError):
        manage.open_plan(tmp_path, slug="missing-slug")
