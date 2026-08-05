"""
File: test_plan_cli_dispatch.py
Path: tests/modules/canvas_artifacts/test_plan_cli_dispatch.py
Role: Dispatch coverage for plan_cli via cli.main (ADR-010).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/cli.py
 - .ai_infra/install/cursor_workflow/plan_cli.py
 - .ai_infra/install/cursor_workflow/plan_manage.py
Notes:
 - Imports package modules via sys.path so coverage attributes correctly.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import cli  # noqa: E402
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


def _write_plan_md(root: Path, body: str = "# Plan\n\nSlice.\n") -> Path:
    plan_dir = root / ".local" / "index-and-planning" / "current"
    plan_dir.mkdir(parents=True)
    path = plan_dir / "plan.md"
    path.write_text(body, encoding="utf-8")
    return path


def _write_snapshot(plans_dir: Path, base: str, slug: str, body: str = "# snap\n") -> Path:
    plans_dir.mkdir(parents=True, exist_ok=True)
    path = plans_dir / f"{base}.plan.md"
    path.write_text(body, encoding="utf-8")
    (plans_dir / f"{base}.meta.yaml").write_text(f"slug: {slug}\nagent: implementer\n", encoding="utf-8")
    return path


def test_plan_snapshot_success(tmp_path: Path, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_plan_md(tmp_path)
    assert (
        cli.main(
            [
                "plan",
                "snapshot",
                "--directory",
                str(tmp_path),
                "--slug",
                "slice-one",
                "--agent",
                "implementer",
                "--board-item",
                "PVTI_x",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "plan snapshot:" in out
    assert "meta:" in out


def test_plan_snapshot_missing_source(tmp_path: Path, capsys) -> None:
    _seed_lwp(tmp_path)
    code = cli.main(
        ["plan", "snapshot", "--directory", str(tmp_path), "--slug", "no-src"]
    )
    assert code == plan_manage.EXIT_NOT_FOUND
    assert "FAIL" in capsys.readouterr().err


def test_plan_snapshot_invalid_slug(tmp_path: Path, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_plan_md(tmp_path)
    code = cli.main(
        ["plan", "snapshot", "--directory", str(tmp_path), "--slug", "Bad_Slug"]
    )
    assert code == plan_manage.EXIT_VALIDATION
    assert "FAIL" in capsys.readouterr().err


def test_plan_list_empty(tmp_path: Path, capsys) -> None:
    _seed_lwp(tmp_path)
    assert cli.main(["plan", "list", "--directory", str(tmp_path)]) == 0
    assert "(none)" in capsys.readouterr().out


def test_plan_list_with_build_bridge(tmp_path: Path, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_snapshot(tmp_path / ".local" / "plans", "2026-08-05-alpha", "alpha")
    assert cli.main(["plan", "list", "--directory", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "build_bridge: plan open --slug alpha" in out
    assert "alpha" in out


def test_plan_list_verbose(tmp_path: Path, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_snapshot(tmp_path / ".local" / "plans", "2026-08-05-beta", "beta")
    assert cli.main(["plan", "list", "--directory", str(tmp_path), "--verbose"]) == 0
    out = capsys.readouterr().out
    assert "# local:" in out
    assert "# build_bridge: plan open --slug beta" in out


def test_plan_open_success(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_snapshot(tmp_path / ".local" / "plans", "2026-08-05-bridge", "bridge")
    cursor_plans = tmp_path / "cursor-plans"
    monkeypatch.setattr(plan_manage.cursor_host_paths, "cursor_plans_dir", lambda: cursor_plans)
    assert cli.main(["plan", "open", "--directory", str(tmp_path), "--slug", "bridge"]) == 0
    out = capsys.readouterr().out
    assert "plan open:" in out
    assert "hint:" in out
    assert (cursor_plans / "bridge.plan.md").is_file()


def test_plan_open_requires_force(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_snapshot(tmp_path / ".local" / "plans", "2026-08-05-force", "force-me")
    cursor_plans = tmp_path / "cursor-plans"
    cursor_plans.mkdir()
    (cursor_plans / "force-me.plan.md").write_text("old\n", encoding="utf-8")
    monkeypatch.setattr(plan_manage.cursor_host_paths, "cursor_plans_dir", lambda: cursor_plans)
    code = cli.main(["plan", "open", "--directory", str(tmp_path), "--slug", "force-me"])
    assert code == plan_manage.EXIT_VALIDATION
    assert "FAIL" in capsys.readouterr().err


def test_plan_open_force(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    _write_snapshot(tmp_path / ".local" / "plans", "2026-08-05-force2", "force-me", "v2\n")
    cursor_plans = tmp_path / "cursor-plans"
    cursor_plans.mkdir()
    (cursor_plans / "force-me.plan.md").write_text("old\n", encoding="utf-8")
    monkeypatch.setattr(plan_manage.cursor_host_paths, "cursor_plans_dir", lambda: cursor_plans)
    assert (
        cli.main(
            ["plan", "open", "--directory", str(tmp_path), "--slug", "force-me", "--force"]
        )
        == 0
    )
    assert "v2" in (cursor_plans / "force-me.plan.md").read_text(encoding="utf-8")


def test_plan_open_missing(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    monkeypatch.setattr(
        plan_manage.cursor_host_paths, "cursor_plans_dir", lambda: tmp_path / "cp"
    )
    code = cli.main(["plan", "open", "--directory", str(tmp_path), "--slug", "ghost"])
    assert code == plan_manage.EXIT_NOT_FOUND
