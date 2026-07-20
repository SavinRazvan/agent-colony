"""
File: test_project_board_bootstrap.py
Path: tests/modules/install/test_project_board_bootstrap.py
Role: Focused unit tests for board-bootstrap checks and shipped template text.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_handlers.py
 - .ai_infra/install/cursor_workflow/board_shell.py
 - .ai_infra/templates/AGENTS.stub.md
 - .ai_infra/templates/project-board/README.md
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import board_shell  # noqa: E402
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
    (root / "project-readme.md").write_text("# README\nok\n", encoding="utf-8")
    (root / "views-setup.md").write_text("ok\n", encoding="utf-8")
    (root / "views-checklist.md").write_text("ok\n", encoding="utf-8")
    src_schema = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "board-shell.schema.yaml"
    )
    shutil.copy(src_schema, root / "board-shell.schema.yaml")
    return root


def _bootstrap_args(
    tmp_path: Path,
    *,
    check: bool = True,
    ensure_fields: bool = False,
    apply_readme: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        directory=tmp_path,
        check=check,
        ensure_fields=ensure_fields,
        apply_readme=apply_readme,
    )


def _patch_common(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, ssot: dict) -> None:
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "project_templates_dir",
        lambda root: tmp_path / ".ai_infra" / "templates" / "project-board",
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 0, "error": None},
    )
    monkeypatch.setattr(
        project_cli,
        "list_project_fields",
        lambda ssot_arg: (
            [
                {"id": "PVTF_status", "name": "Status", "dataType": "SINGLE_SELECT"},
                {"id": "PVTF_pri", "name": "Priority", "dataType": "SINGLE_SELECT"},
                {"id": "PVTF_size", "name": "Size", "dataType": "SINGLE_SELECT"},
                {"id": "PVTF_est", "name": "Estimate", "dataType": "NUMBER"},
                {"id": "PVTF_start", "name": "Start date", "dataType": "DATE"},
            ],
            None,
        ),
    )


def test_board_bootstrap_empty_readme_exits_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("   ", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (_ for _ in ()).throw(AssertionError("views should not be read after empty README")),
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
    _patch_common(monkeypatch, tmp_path, ssot)
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
                    "fields": [
                        "Title",
                        "Assignees",
                        "Status",
                        "Linked pull requests",
                        "Size",
                        "Estimate",
                        "Start date",
                    ],
                },
            ],
            None,
        ),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    captured = capsys.readouterr()
    out = captured.out
    err = captured.err
    assert "views-setup.md" in out
    assert "views-checklist.md" in out
    assert "board-shell-onboard" in out
    assert "missing columns" in err


def test_board_bootstrap_low_quota_skips_live_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "project_templates_dir",
        lambda root: tmp_path / ".ai_infra" / "templates" / "project-board",
    )
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


def test_board_bootstrap_fails_when_minimum_views_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
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

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_VALIDATION
    err = capsys.readouterr().err
    assert "View 1" in err
    assert "missing minimum view" in err


def test_board_bootstrap_warns_recommended_views(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {
                    "name": "Status board",
                    "layout": "BOARD_LAYOUT",
                    "fields": ["Title", "Status", "Priority", "Size", "Estimate", "Start date"],
                },
                {
                    "name": "Prioritized backlog",
                    "layout": "TABLE_LAYOUT",
                    "fields": ["Title", "Status", "Priority", "Size", "Estimate", "Start date"],
                },
            ],
            None,
        ),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "recommended view missing" in err
    assert "Roadmap" in err


def test_board_bootstrap_ensure_fields_prints_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {
                    "name": "Status board",
                    "layout": "BOARD_LAYOUT",
                    "fields": ["Priority", "Size", "Estimate", "Start date"],
                },
                {
                    "name": "Prioritized backlog",
                    "layout": "TABLE_LAYOUT",
                    "fields": ["Priority", "Size", "Estimate", "Start date"],
                },
            ],
            None,
        ),
    )
    calls: list[str] = []

    def _ensure(root, ssot_arg, schema):
        calls.append("ensure")
        print("board-bootstrap: ensure-fields created=(none — already present)")
        print("board-bootstrap: suggested fields: (copy ids into github.collaboration.yaml)")
        print("  priority:")
        print("    field_id: PVTF_pri")
        return project_cli.EXIT_OK

    monkeypatch.setattr(project_cli, "ensure_board_shell_fields", _ensure)

    code = project_handlers.run_board_bootstrap(
        _bootstrap_args(tmp_path, ensure_fields=True)
    )
    assert code == project_cli.EXIT_OK
    assert calls == ["ensure"]
    out = capsys.readouterr().out
    assert "suggested fields" in out
    assert "PVTF_pri" in out


def test_board_bootstrap_apply_readme_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {
                    "name": "Status board",
                    "layout": "BOARD_LAYOUT",
                    "fields": ["Priority", "Size", "Estimate", "Start date"],
                },
                {
                    "name": "Prioritized backlog",
                    "layout": "TABLE_LAYOUT",
                    "fields": ["Priority", "Size", "Estimate", "Start date"],
                },
            ],
            None,
        ),
    )
    calls: list[str] = []

    def _apply(root, ssot_arg, schema):
        calls.append("apply")
        return project_cli.EXIT_OK

    monkeypatch.setattr(project_cli, "apply_board_shell_readme", _apply)

    code = project_handlers.run_board_bootstrap(
        _bootstrap_args(tmp_path, apply_readme=True)
    )
    assert code == project_cli.EXIT_OK
    assert calls == ["apply"]


def test_compare_views_to_schema_unit() -> None:
    schema, err = board_shell.load_board_shell_schema(REPO_ROOT)
    assert err is None and schema is not None
    problems, warnings = board_shell.compare_views_to_schema(
        schema,
        [{"name": "View 1", "layout": "BOARD_LAYOUT", "fields": []}],
    )
    assert any("Status board" in p for p in problems)
    assert any("View 1" in w for w in warnings)


def test_agents_stub_and_view_pack_text() -> None:
    agents = (REPO_ROOT / ".ai_infra" / "templates" / "AGENTS.stub.md").read_text(encoding="utf-8")
    project_board_readme = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "README.md"
    ).read_text(encoding="utf-8")
    views_setup = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "views-setup.md"
    ).read_text(encoding="utf-8")
    schema_text = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "board-shell.schema.yaml"
    ).read_text(encoding="utf-8")
    assert "/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot" in agents
    assert "/add-plugin https://github.com/SavinRazvan/mas-workflow-kit\n" not in agents
    assert "project board-bootstrap --check" in project_board_readme
    assert "views-setup.md" in project_board_readme
    assert "views-checklist.md" in project_board_readme
    assert "Minimum (required)" in views_setup
    assert "Recommended (Playground parity)" in views_setup
    assert "My items" in views_setup
    assert "Status board" in schema_text
    assert "Prioritized backlog" in schema_text
    assert "board-shell.schema.yaml" in views_setup or "board-shell" in views_setup
    readme = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "project-readme.md"
    ).read_text(encoding="utf-8")
    assert "PROJECT_TITLE" in readme
    assert "AI Project Playground" not in readme.split("\n", 5)[0]
    skill = (
        REPO_ROOT / ".cursor" / "skills" / "board-shell-onboard" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "board-bootstrap --check" in skill
    assert "Do not" in skill or "do not" in skill.lower()
