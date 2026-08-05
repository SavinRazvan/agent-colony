"""
File: test_cursor_host_paths.py
Path: tests/modules/canvas_artifacts/test_cursor_host_paths.py
Role: Tests for Cursor managed path resolution.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/cursor_host_paths.py
Notes:
 - Uses temporary fake ~/.cursor/projects layout; direct import for coverage.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import cursor_host_paths as mod  # noqa: E402


def test_cursor_project_dir_exact_slug(tmp_path: Path, monkeypatch) -> None:
    projects = tmp_path / "projects"
    workspace = tmp_path / "home" / "user" / "Projects" / "my-app"
    workspace.mkdir(parents=True)
    slug_dir = projects / "home-user-Projects-my-app"
    slug_dir.mkdir(parents=True)
    (slug_dir / "canvases").mkdir()
    (slug_dir / "mcps").mkdir()
    monkeypatch.setattr(mod, "cursor_projects_home", lambda: projects)

    found = mod.cursor_project_dir(workspace)
    assert found == slug_dir
    assert mod.cursor_canvases_dir(workspace) == slug_dir / "canvases"
    assert mod.cursor_project_mcps_dir(workspace) == slug_dir / "mcps"


def test_cursor_project_dir_fuzzy_suffix(tmp_path: Path, monkeypatch) -> None:
    projects = tmp_path / "projects"
    workspace = tmp_path / "somewhere" / "my-app"
    workspace.mkdir(parents=True)
    slug_dir = projects / "weird-prefix-my-app"
    slug_dir.mkdir(parents=True)
    (slug_dir / "canvases").mkdir()
    monkeypatch.setattr(mod, "cursor_projects_home", lambda: projects)

    assert mod.cursor_project_dir(workspace) == slug_dir


def test_cursor_projects_home() -> None:
    assert mod.cursor_projects_home() == Path.home() / ".cursor" / "projects"


def test_cursor_plans_dir() -> None:
    assert mod.cursor_plans_dir() == Path.home() / ".cursor" / "plans"


def test_cursor_projects_home_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "cursor_projects_home", lambda: tmp_path / "no-projects")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    assert mod.cursor_project_dir(workspace) is None
    assert mod.cursor_canvases_dir(workspace) is None
    assert mod.cursor_project_mcps_dir(workspace) is None


def test_cursor_project_dir_no_fuzzy_match(tmp_path: Path, monkeypatch) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    (projects / "unrelated-other").mkdir()
    workspace = tmp_path / "nowhere" / "unique-app-xyz"
    workspace.mkdir(parents=True)
    monkeypatch.setattr(mod, "cursor_projects_home", lambda: projects)
    assert mod.cursor_project_dir(workspace) is None


def test_cursor_canvases_dir_no_canvases_subdir(tmp_path: Path, monkeypatch) -> None:
    projects = tmp_path / "projects"
    workspace = tmp_path / "home" / "user" / "Projects" / "app"
    workspace.mkdir(parents=True)
    slug_dir = projects / "home-user-Projects-app"
    slug_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "cursor_projects_home", lambda: projects)
    assert mod.cursor_project_dir(workspace) == slug_dir
    assert mod.cursor_canvases_dir(workspace) is None
    assert mod.cursor_project_mcps_dir(workspace) is None


def test_cursor_project_dir_non_home_prefix(tmp_path: Path, monkeypatch) -> None:
    projects = tmp_path / "projects"
    workspace = tmp_path / "opt" / "apps" / "kit"
    workspace.mkdir(parents=True)
    slug = "home-" + str(workspace).lstrip("/").replace("/", "-")
    slug_dir = projects / slug
    slug_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "cursor_projects_home", lambda: projects)
    assert mod.cursor_project_dir(workspace) == slug_dir
