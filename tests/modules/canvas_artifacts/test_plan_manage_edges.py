"""
File: test_plan_manage_edges.py
Path: tests/modules/canvas_artifacts/test_plan_manage_edges.py
Role: Edge coverage for plan_manage miss lines (ADR-010).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/plan_manage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import plan_manage  # noqa: E402


def _seed_lwp(root: Path) -> None:
    pr = root / ".ai_infra" / "scripts" / "pr"
    pr.mkdir(parents=True)
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "local_workflow_paths.py"
    (pr / "local_workflow_paths.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    exemplars = root / ".ai_infra" / "templates" / "local-workspace" / "exemplars"
    exemplars.mkdir(parents=True)
    idx = REPO_ROOT / ".ai_infra" / "templates" / "local-workspace" / "exemplars" / "local-plans-index.md"
    (exemplars / "local-plans-index.md").write_text(idx.read_text(encoding="utf-8"), encoding="utf-8")


def test_validate_slug_invalid() -> None:
    with pytest.raises(ValueError, match="kebab-case"):
        plan_manage.validate_slug("Not_Valid")


def test_resolve_cursor_plan_adds_suffix(tmp_path: Path, monkeypatch) -> None:
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "foo.plan.md").write_text("# f\n", encoding="utf-8")
    monkeypatch.setattr(plan_manage.cursor_host_paths, "cursor_plans_dir", lambda: plans)
    path = plan_manage.resolve_plan_source(tmp_path, "cursor-plan:foo")
    assert path == plans / "foo.plan.md"


def test_resolve_relative_path(tmp_path: Path) -> None:
    rel = Path("docs") / "plan-x.md"
    (tmp_path / "docs").mkdir()
    (tmp_path / rel).write_text("# x\n", encoding="utf-8")
    path = plan_manage.resolve_plan_source(tmp_path, str(rel))
    assert path == (tmp_path / rel).resolve() or path == tmp_path / rel


def test_snapshot_collision_timestamp(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    plan_dir = tmp_path / ".local" / "index-and-planning" / "current"
    plan_dir.mkdir(parents=True)
    (plan_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    dst1, _ = plan_manage.snapshot_plan(tmp_path, slug="collide")
    dst2, _ = plan_manage.snapshot_plan(tmp_path, slug="collide")
    assert dst1 != dst2
    assert dst1.is_file() and dst2.is_file()


def test_list_snapshots_empty_dir(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    assert plan_manage.list_snapshots(tmp_path) == []


def test_list_snapshots_no_meta_and_bad_meta(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    plans = tmp_path / ".local" / "plans"
    plans.mkdir(parents=True)
    (plans / "2026-08-05-plain.plan.md").write_text("# p\n", encoding="utf-8")
    (plans / "2026-08-05-bad.plan.md").write_text("# b\n", encoding="utf-8")
    (plans / "2026-08-05-bad.meta.yaml").write_text("- not a dict\n", encoding="utf-8")
    rows = plan_manage.list_snapshots(tmp_path)
    assert len(rows) == 2
    slugs = {r["slug"] for r in rows}
    assert "plain" in slugs


def test_canvas_base_from_plan_variants() -> None:
    assert plan_manage.canvas_base_from_plan("2026-08-05-my-slug.plan.md") == "my-slug"
    assert plan_manage.canvas_base_from_plan("odd.plan.md") == "odd"


def test_find_latest_empty_plans_dir(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    with pytest.raises(FileNotFoundError):
        plan_manage.find_latest_snapshot(tmp_path, "none")


def test_find_latest_from_filename_when_meta_missing(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    plans = tmp_path / ".local" / "plans"
    plans.mkdir(parents=True)
    path = plans / "2026-08-05-from-name.plan.md"
    path.write_text("# n\n", encoding="utf-8")
    latest = plan_manage.find_latest_snapshot(tmp_path, "from-name")
    assert latest == path


def test_snapshot_slug_meta_without_slug_key(tmp_path: Path) -> None:
    plans = tmp_path / "plans"
    plans.mkdir()
    path = plans / "2026-08-05-x.plan.md"
    path.write_text("# x\n", encoding="utf-8")
    (plans / "2026-08-05-x.meta.yaml").write_text("agent: implementer\n", encoding="utf-8")
    assert plan_manage._snapshot_slug(path) == "x"


def test_append_plan_index_dedup(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    plans = tmp_path / ".local" / "plans"
    plans.mkdir(parents=True)
    index = plans / "index.md"
    index.write_text(
        "# Plans\n\n| snapshot | slug | agent | board | source |\n| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )
    plan_manage._append_plan_index(
        tmp_path,
        snapshot="snap-a",
        slug="slug-a",
        agent="implementer",
        board_item="PVTI_x",
        source="plan.md",
    )
    text1 = index.read_text(encoding="utf-8")
    assert "snap-a" in text1
    plan_manage._append_plan_index(
        tmp_path,
        snapshot="snap-a",
        slug="slug-a",
        agent=None,
        board_item=None,
        source="plan.md",
    )
    assert text1 == index.read_text(encoding="utf-8")


def test_find_latest_no_matching_slug(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    plans = tmp_path / ".local" / "plans"
    plans.mkdir(parents=True)
    (plans / "2026-08-05-other.plan.md").write_text("# o\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="no plan snapshot"):
        plan_manage.find_latest_snapshot(tmp_path, "wanted")


def test_append_plan_index_missing_file(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    plan_manage._append_plan_index(
        tmp_path,
        snapshot="x",
        slug="x",
        agent=None,
        board_item=None,
        source="plan.md",
    )
