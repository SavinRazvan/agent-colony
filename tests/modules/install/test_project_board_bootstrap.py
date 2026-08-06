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


def _tier1_fields() -> list[str]:
    return [
        "Title",
        "Assignees",
        "Status",
        "Priority",
        "Size",
        "Estimate",
        "Start date",
        "Linked pull requests",
    ]


def _full_playground_views(*, backlog_fields: list[str] | None = None) -> list[dict]:
    tier = _tier1_fields()
    backlog = backlog_fields if backlog_fields is not None else tier
    return [
        {"name": "Status board", "layout": "BOARD_LAYOUT", "fields": tier},
        {"name": "Prioritized backlog", "layout": "TABLE_LAYOUT", "fields": backlog},
        {"name": "Roadmap", "layout": "ROADMAP_LAYOUT", "fields": ["Title", "Status"]},
        {"name": "Bugs 🐛", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
        {"name": "In review", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
        {"name": "My items", "layout": "TABLE_LAYOUT", "fields": ["Title", "Priority"]},
    ]


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
    # Full Playground views, but Prioritized backlog missing Priority (live regression).
    incomplete_backlog = [
        "Title",
        "Assignees",
        "Status",
        "Linked pull requests",
        "Size",
        "Estimate",
        "Start date",
    ]
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (_full_playground_views(backlog_fields=incomplete_backlog), None),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_VALIDATION
    captured = capsys.readouterr()
    err = captured.err
    assert "board-bootstrap: FAIL" in err
    assert "missing columns" in err
    assert "Priority" in err


def test_board_bootstrap_fails_when_status_board_missing_priority_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    tier_no_priority = [
        "Title",
        "Assignees",
        "Status",
        "Size",
        "Estimate",
        "Start date",
        "Linked pull requests",
    ]
    tier_full = [
        "Title",
        "Assignees",
        "Status",
        "Priority",
        "Size",
        "Estimate",
        "Start date",
        "Linked pull requests",
    ]
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {"name": "Status board", "layout": "BOARD_LAYOUT", "fields": tier_no_priority},
                {"name": "Prioritized backlog", "layout": "TABLE_LAYOUT", "fields": tier_full},
                {"name": "Roadmap", "layout": "ROADMAP_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "Bugs", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "In review", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "My items", "layout": "TABLE_LAYOUT", "fields": ["Title", "Priority"]},
            ],
            None,
        ),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_VALIDATION
    err = capsys.readouterr().err
    assert "Status board" in err
    assert "Priority" in err
    assert "board-bootstrap: FAIL" in err


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
    assert code == project_cli.EXIT_GH
    err = capsys.readouterr().err
    assert "low GraphQL quota" in err
    assert "INCOMPLETE" in err
    assert "do not treat as shell green" in err.lower() or "INCOMPLETE" in err


def test_board_bootstrap_fails_when_default_playground_views_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Only Status board + Prioritized backlog is not enough — Playground set is default minimum."""
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
    assert code == project_cli.EXIT_VALIDATION
    err = capsys.readouterr().err
    assert "missing minimum view" in err
    assert "Roadmap" in err
    assert "board-shell init --minimal" in err


def test_board_bootstrap_warns_when_prioritized_backlog_missing_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    tier = ["Title", "Assignees", "Status", "Size", "Estimate", "Start date", "Linked pull requests"]
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
                    # Live Playground regression: Size/Estimate without Priority
                    "fields": tier,
                },
                {"name": "Roadmap", "layout": "ROADMAP_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "Bugs", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "In review", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "My items", "layout": "TABLE_LAYOUT", "fields": ["Title", "Priority"]},
            ],
            None,
        ),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_VALIDATION
    err = capsys.readouterr().err
    assert "Prioritized backlog" in err
    assert "Priority" in err
    assert "missing columns" in err
    assert "board-bootstrap: FAIL" in err


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


def test_board_bootstrap_ok_with_full_playground_views(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    tier = ["Title", "Assignees", "Status", "Priority", "Size", "Estimate", "Start date", "Linked pull requests"]
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {"name": "Status board", "layout": "BOARD_LAYOUT", "fields": tier},
                {"name": "Prioritized backlog", "layout": "TABLE_LAYOUT", "fields": tier},
                {"name": "Roadmap", "layout": "ROADMAP_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "Bugs 🐛", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "In review", "layout": "TABLE_LAYOUT", "fields": ["Title", "Status"]},
                {"name": "My items", "layout": "TABLE_LAYOUT", "fields": ["Title", "Priority"]},
            ],
            None,
        ),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "missing minimum view" not in err
    assert "recommended view missing" not in err
    assert "missing columns" not in err


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
        lambda ssot_arg: (_full_playground_views(), None),
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
        lambda ssot_arg: (_full_playground_views(), None),
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


def test_tier1_column_blocking_warnings_unit() -> None:
    warnings = [
        "rename default view 'View 1'",
        "Status board (BOARD_LAYOUT) missing columns: Priority, Size",
        "recommended view missing: 'Extra'",
    ]
    blockers = board_shell.tier1_column_blocking_warnings(warnings)
    assert blockers == ["Status board (BOARD_LAYOUT) missing columns: Priority, Size"]


def test_compare_views_to_schema_unit() -> None:
    schema, err = board_shell.load_board_shell_schema(REPO_ROOT)
    assert err is None and schema is not None
    problems, warnings = board_shell.compare_views_to_schema(
        schema,
        [{"name": "View 1", "layout": "BOARD_LAYOUT", "fields": []}],
    )
    assert any("Status board" in p for p in problems)
    assert any("View 1" in w for w in warnings)


def _load_minimal_overlay_schema() -> dict:
    import yaml

    path = (
        REPO_ROOT
        / ".ai_infra"
        / "templates"
        / "user-settings"
        / "exemplars"
        / "board-shell.schema.minimal.yaml"
    )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_minimal_overlay_schema_two_views_pass() -> None:
    schema = _load_minimal_overlay_schema()
    tier = _tier1_fields()
    live = [
        {"name": "Status board", "layout": "BOARD_LAYOUT", "fields": tier},
        {"name": "Prioritized backlog", "layout": "TABLE_LAYOUT", "fields": tier},
    ]
    problems, warnings = board_shell.compare_views_to_schema(schema, live)
    assert problems == []
    assert board_shell.tier1_column_blocking_warnings(warnings) == []


def test_minimal_overlay_missing_prioritized_backlog_fails() -> None:
    schema = _load_minimal_overlay_schema()
    tier = _tier1_fields()
    live = [{"name": "Status board", "layout": "BOARD_LAYOUT", "fields": tier}]
    problems, warnings = board_shell.compare_views_to_schema(schema, live)
    assert any("Prioritized backlog" in p for p in problems)


def test_resolve_board_shell_schema_prefers_overlay(tmp_path: Path) -> None:
    overlay_dir = tmp_path / ".local" / "user_settings"
    overlay_dir.mkdir(parents=True)
    minimal = (
        REPO_ROOT
        / ".ai_infra"
        / "templates"
        / "user-settings"
        / "exemplars"
        / "board-shell.schema.minimal.yaml"
    )
    shutil.copy(minimal, overlay_dir / "board-shell.schema.yaml")
    kit_templates = tmp_path / ".ai_infra" / "templates" / "project-board"
    kit_templates.mkdir(parents=True)
    shutil.copy(
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "board-shell.schema.yaml",
        kit_templates / "board-shell.schema.yaml",
    )
    resolved = board_shell.resolve_board_shell_schema_path(tmp_path)
    assert resolved == overlay_dir / "board-shell.schema.yaml"
    schema, err = board_shell.load_board_shell_schema(tmp_path)
    assert err is None and schema is not None
    assert schema.get("name") == "minimal-two-view"
    assert len(board_shell.minimum_views(schema)) == 2


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
    assert "/add-plugin https://github.com/SavinRazvan/agent-colony" in agents
    assert "/add-plugin https://github.com/SavinRazvan/" + "mas-" + "workflow" + "-" + "kit\n" not in agents
    assert "board-bootstrap --check" in agents
    assert "CONSENT GATE" in agents
    assert "TURN PROTOCOL" in agents
    assert "project board-bootstrap --check" in project_board_readme
    assert "views-setup.md" in project_board_readme
    assert "views-checklist.md" in project_board_readme
    assert "Default minimum (required)" in views_setup or "Default views (Playground)" in views_setup
    assert "Priority" in views_setup
    assert "My items" in views_setup
    assert "Minimal 2-view overlay" in views_setup
    assert "board-shell.schema.minimal.yaml" in views_setup
    assert "Browser assist map" in views_setup
    assert "Group by" in views_setup
    assert "Prioritized backlog" in schema_text
    assert "Roadmap" in schema_text
    assert "recommended: []" in schema_text or "recommended:\n  []" in schema_text
    assert "board-shell.schema.yaml" in views_setup or "board-shell" in views_setup
    readme = (
        REPO_ROOT / ".ai_infra" / "templates" / "project-board" / "project-readme.md"
    ).read_text(encoding="utf-8")
    assert "PROJECT_TITLE" in readme
    assert "AI Project Playground" not in readme.split("\n", 5)[0]
    skill = (
        REPO_ROOT / ".cursor" / "skills" / "board-shell" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "board-bootstrap --check" in skill
    assert "Browser assist map" in skill
    assert "Optional polish" in skill or "optional polish" in skill.lower()
    assert "Do not" in skill or "do not" in skill.lower()
    project_board_agent = (
        REPO_ROOT / ".cursor" / "agents" / "board.md"
    ).read_text(encoding="utf-8")
    assert "browser MCP" in project_board_agent
    assert "Browser assist map" in project_board_agent
    assert "asks" in project_board_agent.lower() or "explicit" in project_board_agent.lower()
    assert "api=complete" in project_board_agent


def test_board_shell_init_minimal_writes_overlay(tmp_path: Path) -> None:
    exemplars = tmp_path / ".ai_infra" / "templates" / "user-settings" / "exemplars"
    exemplars.mkdir(parents=True)
    minimal_src = (
        REPO_ROOT
        / ".ai_infra"
        / "templates"
        / "user-settings"
        / "exemplars"
        / "board-shell.schema.minimal.yaml"
    )
    shutil.copy(minimal_src, exemplars / "board-shell.schema.minimal.yaml")
    code, message = board_shell.init_minimal_overlay(tmp_path)
    assert code == 0
    overlay = tmp_path / ".local" / "user_settings" / "board-shell.schema.yaml"
    assert overlay.is_file()
    assert "minimal-two-view" in overlay.read_text(encoding="utf-8")
    assert "wrote minimal overlay" in message


def test_board_bootstrap_passes_with_minimal_overlay_and_two_views(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    overlay_dir = tmp_path / ".local" / "user_settings"
    overlay_dir.mkdir(parents=True)
    shutil.copy(
        REPO_ROOT
        / ".ai_infra"
        / "templates"
        / "user-settings"
        / "exemplars"
        / "board-shell.schema.minimal.yaml",
        overlay_dir / "board-shell.schema.yaml",
    )
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda ssot_arg: ("# README\n", None))
    tier = _tier1_fields()
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda ssot_arg: (
            [
                {"name": "Status board", "layout": "BOARD_LAYOUT", "fields": tier},
                {"name": "Prioritized backlog", "layout": "TABLE_LAYOUT", "fields": tier},
            ],
            None,
        ),
    )

    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    captured = capsys.readouterr()
    assert "missing minimum view" not in captured.err
    assert "board-bootstrap: ok" in captured.out or "board-bootstrap: ok" in captured.err
