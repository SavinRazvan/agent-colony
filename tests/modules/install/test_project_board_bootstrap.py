"""
File: test_project_board_bootstrap.py
Path: tests/modules/install/test_project_board_bootstrap.py
Role: Focused unit tests for board-bootstrap checks and shipped template text.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_handlers.py
 - .ai_infra/templates/AGENTS.stub.md
 - .ai_infra/templates/project-board/README.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_cli  # noqa: E402
import project_handlers  # noqa: E402
import project_outbox  # noqa: E402
from test_project_cli import SAMPLE_SSOT  # noqa: E402


def _ssot() -> dict:
    return json.loads(json.dumps(SAMPLE_SSOT))


def _template_root(tmp_path: Path) -> Path:
    root = tmp_path / ".ai_infra" / "templates" / "project-board"
    root.mkdir(parents=True, exist_ok=True)
    for name in ("slice", "bug", "research"):
        (root / f"card-body-{name}.md").write_text("ok\n", encoding="utf-8")
    (root / "project-readme.md").write_text("ok\n", encoding="utf-8")
    (root / "views-setup.md").write_text("ok\n", encoding="utf-8")
    (root / "views-checklist.md").write_text("ok\n", encoding="utf-8")
    return root


def _bootstrap_args(tmp_path: Path, *, check: bool = True) -> SimpleNamespace:
    return SimpleNamespace(directory=tmp_path, check=check)


def test_board_bootstrap_empty_readme_exits_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "project_templates_dir", lambda root: tmp_path / ".ai_infra" / "templates" / "project-board")
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("   ", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (_ for _ in ()).throw(AssertionError("views should not be read after empty README")),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_VALIDATION
    err = capsys.readouterr().err
    assert "project-readme.md" in err


def test_board_bootstrap_ok_readme_reports_next_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "project_templates_dir", lambda root: tmp_path / ".ai_infra" / "templates" / "project-board")
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {
                    "name": "Status board",
                    "layout": "BOARD_LAYOUT",
                    "fields": ["Title", "Status", "Size"],
                },
                {
                    "name": "Prioritized backlog",
                    "layout": "TABLE_LAYOUT",
                    "fields": ["Title", "Assignees", "Status", "Linked pull requests", "Size", "Estimate", "Start date"],
                },
            ],
            None,
        ),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    captured = capsys.readouterr()
    out = captured.out
    err = captured.err
    assert "views-setup.md" in out
    assert "views-checklist.md" in out
    assert "Status board" in err
    assert "missing columns" in err


def test_board_bootstrap_low_quota_skips_live_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "project_templates_dir", lambda root: tmp_path / ".ai_infra" / "templates" / "project-board")
    monkeypatch.setattr(
        project_cli,
        "read_project_readme",
        lambda ssot_arg: (_ for _ in ()).throw(AssertionError("README probe should be skipped")),
    )
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (_ for _ in ()).throw(AssertionError("view probe should be skipped")),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 1, "limit": 5000, "reset_epoch": 0, "error": None},
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "low GraphQL quota" in err


def test_board_bootstrap_warns_on_default_view_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "project_templates_dir", lambda root: tmp_path / ".ai_infra" / "templates" / "project-board")
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {
                    "name": "View 1",
                    "layout": "BOARD_LAYOUT",
                    "fields": ["Title", "Status", "Priority", "Size", "Estimate", "Start date"],
                },
            ],
            None,
        ),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "View 1" in err
    assert "rename default view" in err


def test_agents_stub_and_view_pack_text() -> None:
    agents = (REPO_ROOT / ".ai_infra" / "templates" / "AGENTS.stub.md").read_text(encoding="utf-8")
    project_board_readme = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "README.md"
    ).read_text(encoding="utf-8")
    views_setup = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "views-setup.md"
    ).read_text(encoding="utf-8")
    assert "/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot" in agents
    assert "/add-plugin https://github.com/SavinRazvan/mas-workflow-kit\n" not in agents
    assert "project board-bootstrap --check" in project_board_readme
    assert "views-setup.md" in project_board_readme
    assert "views-checklist.md" in project_board_readme
    assert "Minimum (required)" in views_setup
    assert "Recommended (Playground parity)" in views_setup
    assert "My items" in views_setup
    readme = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "project-readme.md"
    ).read_text(encoding="utf-8")
    assert "PROJECT_TITLE" in readme
    assert "AI Project Playground" not in readme.split("\n", 5)[0]
