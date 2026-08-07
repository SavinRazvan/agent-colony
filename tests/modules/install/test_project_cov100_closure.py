"""
File: test_project_cov100_closure.py
Path: tests/modules/install/test_project_cov100_closure.py
Role: Closure tests for remaining scoped kit coverage gaps (board shell, bootstrap, atomics).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/project_handlers.py
 - .ai_infra/install/agent_colony/board_shell.py
 - .ai_infra/install/agent_colony/project_atomics.py
 - .ai_infra/scripts/workflow/check_drift.py
Notes:
 - Monkeypatches gh/GraphQL; no live network.
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
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))
if str(WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_DIR))

import board_shell as bs  # noqa: E402
import check_drift as cd  # noqa: E402
import project_atomics as pa  # noqa: E402
import project_cli  # noqa: E402
import project_handlers  # noqa: E402
import project_outbox  # noqa: E402
from test_project_board_bootstrap import (  # noqa: E402
    _bootstrap_args,
    _full_playground_views,
    _patch_common,
    _ssot,
    _template_root,
)
from test_project_cli import SAMPLE_SSOT, VALID_PVTI, _write_collab  # noqa: E402


def _gh_ok(stdout: str = "{}") -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def _views_graphql_nodes(views: list[dict] | None = None) -> list[dict]:
    """Shape for gh api graphql project views probe (Playground six-view default)."""
    src = views if views is not None else _full_playground_views()
    nodes: list[dict] = []
    for view in src:
        field_names = view.get("fields") or []
        nodes.append(
            {
                "name": view["name"],
                "layout": view.get("layout") or "TABLE_LAYOUT",
                "fields": {"nodes": [{"name": n} for n in field_names]},
            }
        )
    return nodes


def _gh_fail(msg: str = "gh failed") -> SimpleNamespace:
    return SimpleNamespace(returncode=1, stdout="", stderr=msg)


# --- board_shell.py ---


def test_resolve_board_shell_schema_overlay(tmp_path: Path) -> None:
    overlay_dir = tmp_path / ".local" / "user_settings"
    overlay_dir.mkdir(parents=True)
    overlay = overlay_dir / "board-shell.schema.yaml"
    overlay.write_text("version: 1\nfields:\n  required: []\n", encoding="utf-8")
    assert bs.resolve_board_shell_schema_path(tmp_path) == overlay


def test_load_board_shell_schema_missing_and_invalid(tmp_path: Path) -> None:
    schema, err = bs.load_board_shell_schema(tmp_path)
    assert schema is None and err and "missing" in err

    bad = tmp_path / ".ai_infra" / "templates" / "project-board"
    bad.mkdir(parents=True)
    (bad / "board-shell.schema.yaml").write_text("not: [valid", encoding="utf-8")
    schema2, err2 = bs.load_board_shell_schema(tmp_path)
    assert schema2 is None and err2 and "invalid" in err2

    (bad / "board-shell.schema.yaml").write_text("- list\n", encoding="utf-8")
    schema3, err3 = bs.load_board_shell_schema(tmp_path)
    assert schema3 is None and err3 and "mapping" in err3


def test_board_shell_helpers_and_compare_edges() -> None:
    schema = {
        "fields": {"required": [{"name": "Priority"}, "Size"]},
        "views": {
            "visible_columns": "not-a-list",
            "minimum": "bad",
            "recommended": None,
        },
    }
    assert bs.required_field_names(schema) == ["Priority", "Size"]
    assert "Priority" in bs.visible_columns(schema)
    assert bs.minimum_views(schema) == []
    assert bs.recommended_views(schema) == []

    schema_with_min = json.loads(json.dumps(schema))
    schema_with_min["views"] = {
        "minimum": [{"name": "Status board", "layout": "BOARD_LAYOUT"}],
        "recommended": [{"name": "Roadmap"}],
    }
    live = [
        {"name": "View 1", "layout": "BOARD", "fields": ["Title"]},
        {
            "name": "Status board",
            "layout": "TABLE_LAYOUT",
            "fields": ["Priority", "Size", "Estimate", "Start date"],
        },
        {
            "name": "statusboard",
            "layout": "BOARD_LAYOUT",
            "fields": ["Priority", "Size", "Estimate", "Start date"],
        },
    ]
    problems, warnings = bs.compare_views_to_schema(schema_with_min, live)
    assert any("View 1" in w for w in warnings)
    assert any("layout=" in w for w in warnings)

    schema2 = json.loads(json.dumps(schema_with_min))
    schema2["views"] = {
        "minimum": [{"name": "Status board", "layout": "BOARD_LAYOUT"}],
        "recommended": [{"name": "Roadmap"}],
    }
    problems2, warnings2 = bs.compare_views_to_schema(schema2, live[1:])
    assert any("recommended view missing" in w for w in warnings2)
    assert bs.schema_must_match_prose_names(schema2)


def test_board_shell_import_error_and_empty_names(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tpl = tmp_path / ".ai_infra" / "templates" / "project-board"
    tpl.mkdir(parents=True)
    (tpl / "board-shell.schema.yaml").write_text("version: 1\n", encoding="utf-8")

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    schema, err = bs.load_board_shell_schema(tmp_path)
    assert schema is None and err and "PyYAML required" in err

    schema_bad = {
        "views": {
            "minimum": [{"name": ""}, {"name": "Status board", "layout": "BOARD_LAYOUT"}],
            "recommended": [{"name": ""}, {"name": "Roadmap"}],
        }
    }
    live = [{"name": "Roadmap", "layout": "ROADMAP_LAYOUT", "fields": []}]
    problems, warnings = bs.compare_views_to_schema(schema_bad, live)
    assert not any("missing minimum view ''" in p for p in problems)
    assert not any("recommended view missing: ''" in w for w in warnings)


# --- project_cli read_project_* / list_project_fields / ensure / apply ---


def test_read_project_readme_all_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("view failed"))
    text, err = project_cli.read_project_readme(ssot)
    assert text is None and "view failed" in (err or "")

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("not-json"))
    text2, err2 = project_cli.read_project_readme(ssot)
    assert text2 is None and "invalid JSON" in (err2 or "")

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("[]"))
    text3, err3 = project_cli.read_project_readme(ssot)
    assert text3 is None and "object" in (err3 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"readme": 123})),
    )
    text4, err4 = project_cli.read_project_readme(ssot)
    assert text4 is None and "not a string" in (err4 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"readme": None})),
    )
    text_null, err_null = project_cli.read_project_readme(ssot)
    assert text_null == "" and err_null is None

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"readme": "# ok\n"})),
    )
    text5, err5 = project_cli.read_project_readme(ssot)
    assert text5 == "# ok\n" and err5 is None


def test_read_project_views_all_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    base = {
        "data": {
            "node": {
                "views": {
                    "nodes": [
                        {
                            "name": "Status board",
                            "layout": "BOARD_LAYOUT",
                            "fields": {
                                "nodes": [{"name": "Status"}, "bad", {"name": ""}]
                            },
                        },
                        "skip-me",
                    ]
                }
            }
        }
    }

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("views failed"))
    views, err = project_cli.read_project_views(ssot)
    assert views is None and "views failed" in (err or "")

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("bad"))
    views2, err2 = project_cli.read_project_views(ssot)
    assert views2 is None and "invalid graphql JSON" in (err2 or "")

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("[]"))
    views3, err3 = project_cli.read_project_views(ssot)
    assert views3 is None and "not an object" in (err3 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"errors": [{"message": "denied"}]})),
    )
    views4, err4 = project_cli.read_project_views(ssot)
    assert views4 is None and err4 == "denied"

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"errors": {"message": "dict err"}})),
    )
    views5, err5 = project_cli.read_project_views(ssot)
    assert views5 is None and "dict err" in (err5 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"errors": ["plain"]})),
    )
    views6, err6 = project_cli.read_project_views(ssot)
    assert views6 is None and err6 == "plain"

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"data": {}})),
    )
    views7, err7 = project_cli.read_project_views(ssot)
    assert views7 is None and "metadata unavailable" in (err7 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"data": {"node": {"views": {}}}})),
    )
    views8, err8 = project_cli.read_project_views(ssot)
    assert views8 is None and "metadata unavailable" in (err8 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps(base)),
    )
    views9, err9 = project_cli.read_project_views(ssot)
    assert err9 is None and views9 and views9[0]["fields"] == ["Status"]


def test_list_project_fields_all_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    payload = {
        "data": {
            "node": {
                "fields": {
                    "nodes": [
                        {
                            "id": "PVTF_pri",
                            "name": "Priority",
                            "dataType": "SINGLE_SELECT",
                            "options": [{"id": "o1", "name": "p1"}, "skip"],
                        },
                        {"id": "PVTF_x", "name": ""},
                        "skip",
                    ]
                }
            }
        }
    }

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("fields failed"))
    fields, err = project_cli.list_project_fields(ssot)
    assert fields is None and "fields failed" in (err or "")

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("bad"))
    fields2, err2 = project_cli.list_project_fields(ssot)
    assert fields2 is None and "invalid graphql JSON" in (err2 or "")

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("null"))
    fields3, err3 = project_cli.list_project_fields(ssot)
    assert fields3 is None and "not an object" in (err3 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"errors": [{"message": "nope"}]})),
    )
    fields4, err4 = project_cli.list_project_fields(ssot)
    assert fields4 is None and err4 == "nope"

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"data": {"node": {}}})),
    )
    fields5, err5 = project_cli.list_project_fields(ssot)
    assert fields5 is None and "metadata unavailable" in (err5 or "")

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"errors": ["plain"]})),
    )
    fields_plain, err_plain = project_cli.list_project_fields(ssot)
    assert fields_plain is None and err_plain == "plain"

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps(payload)),
    )
    fields6, err6 = project_cli.list_project_fields(ssot)
    assert err6 is None and fields6 and fields6[0]["options"] == [{"id": "o1", "name": "p1"}]


def test_ensure_board_shell_fields_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _template_root(tmp_path)
    ssot = _ssot()
    schema, _ = bs.load_board_shell_schema(REPO_ROOT)
    assert schema is not None

    monkeypatch.setattr(
        project_cli,
        "list_project_fields",
        lambda s: (None, "list failed"),
    )
    assert project_cli.ensure_board_shell_fields(tmp_path, ssot, schema) == project_cli.EXIT_GH
    capsys.readouterr()

    status_field = {
        "id": "PVTF_status",
        "name": "Status",
        "dataType": "SINGLE_SELECT",
        "options": [
            {"id": "o_ready", "name": "Ready"},
            {"id": "o_ip", "name": "In progress"},
            {"id": "o_ir", "name": "In review"},
            {"id": "o_done", "name": "Done"},
        ],
    }
    live = [
        {"name": "Priority", "id": "PVTF_pri", "dataType": "SINGLE_SELECT", "options": []},
        status_field,
    ]
    calls: list[str] = []

    def fake_list(s):
        calls.append("list")
        if calls.count("list") == 1:
            return ([], None)
        if calls.count("list") == 2:
            return (None, "relist failed")
        return (live, None)

    def fake_gh(args: list[str], *, timeout_s: float = 60.0, input_text: str | None = None):
        if input_text and "createProjectV2Field" in input_text:
            if "Size" in input_text:
                return _gh_ok("not-json")
            if "Start date" in input_text:
                return _gh_ok(json.dumps({"data": {"createProjectV2Field": {"projectV2Field": {"id": "PVTF_start"}}}}))
            return _gh_fail("create failed")
        return _gh_fail("unexpected")

    schema_local = {
        "fields": {
            "required": [
                "not-a-dict",
                {"name": ""},
                {"name": "Status", "data_type": "single_select"},
                {"name": "Priority", "data_type": "single_select", "options": ["p1"]},
                {"name": "Size", "data_type": "single_select", "options": ["s"]},
                {"name": "Start date", "data_type": "date"},
                {"name": "Estimate", "data_type": "number"},
            ]
        }
    }

    monkeypatch.setattr(project_cli, "list_project_fields", fake_list)
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    assert project_cli.ensure_board_shell_fields(tmp_path, ssot, schema_local) == project_cli.EXIT_OK
    out_err = capsys.readouterr()
    err = out_err.err
    out = out_err.out
    assert "re-list fields failed" in err
    assert "create field 'Priority'" in err or "Priority" in err


def test_ensure_board_shell_fields_prints_status_options(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    status_field = {
        "id": "PVTF_status",
        "name": "Status",
        "dataType": "SINGLE_SELECT",
        "options": [
            {"id": "o_ready", "name": "Ready"},
            {"id": "o_ip", "name": "In progress"},
        ],
    }
    live_full = [
        {"name": "Priority", "id": "PVTF_pri", "dataType": "SINGLE_SELECT"},
        status_field,
        {"name": "Unknown", "id": "PVTF_x", "dataType": "TEXT"},
    ]
    list_calls = {"n": 0}

    def fake_list(s):
        list_calls["n"] += 1
        if list_calls["n"] == 1:
            return ([], None)
        return (live_full, None)

    def fake_gh(args: list[str], *, timeout_s: float = 60.0, input_text: str | None = None):
        if input_text and "createProjectV2Field" in input_text and "Estimate" in input_text:
            return _gh_ok(json.dumps({"data": {"createProjectV2Field": {"projectV2Field": {"id": "PVTF_est"}}}}))
        return _gh_fail("unexpected")

    schema_local = {
        "fields": {
            "required": [{"name": "Estimate", "data_type": "number"}],
        }
    }

    monkeypatch.setattr(project_cli, "list_project_fields", fake_list)
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    assert project_cli.ensure_board_shell_fields(tmp_path, ssot, schema_local) == project_cli.EXIT_OK
    captured = capsys.readouterr().out
    assert "suggested fields" in captured
    assert "options:" in captured
    assert "in_progress:" in captured
    assert "ensure-fields created=Estimate" in captured

    schema_non_list = {"fields": {"required": "bad-type"}}
    list_calls["n"] = 0
    assert project_cli.ensure_board_shell_fields(tmp_path, ssot, schema_non_list) == project_cli.EXIT_OK


def test_apply_board_shell_readme_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    schema, _ = bs.load_board_shell_schema(REPO_ROOT)
    assert schema is not None

    monkeypatch.setattr(
        project_cli,
        "project_templates_dir",
        lambda root: tmp_path / "missing",
    )
    assert (
        project_cli.apply_board_shell_readme(tmp_path, ssot, schema) == project_cli.EXIT_USAGE
    )

    tpl = tmp_path / "tpl"
    tpl.mkdir()
    (tpl / "project-readme.md").write_text("Your Board Name (board SSOT)\n`owner/repo`\n", encoding="utf-8")
    monkeypatch.setattr(project_cli, "project_templates_dir", lambda root: tpl)

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("update failed"))
    assert project_cli.apply_board_shell_readme(tmp_path, ssot, schema) == project_cli.EXIT_GH

    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("not-json"))
    assert project_cli.apply_board_shell_readme(tmp_path, ssot, schema) == project_cli.EXIT_GH

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"errors": ["readme denied"]})),
    )
    assert project_cli.apply_board_shell_readme(tmp_path, ssot, schema) == project_cli.EXIT_GH

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"data": {"updateProjectV2": {"projectV2": {"id": "P"}}}})),
    )
    assert project_cli.apply_board_shell_readme(tmp_path, ssot, schema) == project_cli.EXIT_OK


# --- create-from-template assignee paths ---


def test_create_from_template_assignee_branches(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "create_board_item",
        lambda *a, **k: ("PVTI_x", "", None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_field_option_id",
        lambda *a, **k: ("fid", "oid"),
    )
    monkeypatch.setattr(project_cli, "set_item_number", lambda *a, **k: (True, "ok"))

    args_skip = argparse.Namespace(
        directory=REPO_ROOT,
        title="T",
        template="slice",
        acceptance="a",
        rollback="r",
        notes="",
        status="",
        priority="p1",
        size=None,
        estimate=None,
        agent="",
        no_assignee=True,
    )
    assert project_cli.cmd_create_from_template(args_skip) == project_cli.EXIT_OK
    assert "assignee=skipped:--no-assignee" in capsys.readouterr().out

    ssot_draft = json.loads(json.dumps(_ssot()))
    ssot_draft.setdefault("conventions", {})["item_kind_default"] = "draft"
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot_draft, []))
    args_draft = argparse.Namespace(**{**vars(args_skip), "no_assignee": False})
    assert project_cli.cmd_create_from_template(args_draft) == project_cli.EXIT_OK
    assert "assignee=skipped:draft" in capsys.readouterr().out

    def raise_user(root):
        raise RuntimeError("no user yaml")

    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", raise_user)
    assert project_cli.cmd_create_from_template(args_draft) == project_cli.EXIT_OK
    assert "assignee skipped" in capsys.readouterr().err

    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@alice")
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "alice"))
    assert project_cli.cmd_create_from_template(args_draft) == project_cli.EXIT_OK
    assert "assignee=@alice" in capsys.readouterr().out

    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "DraftIssue cannot assign"),
    )
    assert project_cli.cmd_create_from_template(args_draft) == project_cli.EXIT_OK
    assert "assignee=skipped:draft" in capsys.readouterr().out

    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "rate limited"),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED)
    assert project_cli.cmd_create_from_template(args_draft) == project_cli.EXIT_OK
    assert "assignee QUEUED" in capsys.readouterr().err


# --- project_atomics gaps ---


def test_project_atomics_edge_helpers() -> None:
    assert pa.section_body_content("## A\n\nx", "") == ""
    assert pa.section_body_content("## A\n\nx", "Missing") == ""
    assert pa.item_field_value(None, "x") == ""
    assert not pa.item_has_assignee({"priority": "p1"})
    assert pa.item_has_assignee({"assignees": [{"login": ""}, {"login": "bob"}]})
    assert pa.item_has_assignee({"assignees": ["charlie"]})
    assert not pa.item_has_assignee({"assignees": []})
    assert pa.item_has_assignee({"Assignees": "alice"})
    assert pa.item_content_kind({"content": {"type": "DraftIssue"}}) == "draft"
    assert pa.item_content_kind({"content": {"type": "Issue", "number": 1}}) == "issue"
    assert pa.item_content_kind({"title": "My draft item"}) == "draft"

    problems, warnings = pa.collect_validate_item_problems(SAMPLE_SSOT, None)
    assert "not a mapping" in problems[0]

    ssot = json.loads(json.dumps(SAMPLE_SSOT))
    ssot["conventions"] = {
        **ssot.get("conventions", {}),
        "item_kind_default": "draft",
        "require_attribution_on_exit": True,
        "body_sections": ["Acceptance", "Rollback", "Notes"],
    }
    item = {
        "id": VALID_PVTI,
        "status": "Ready",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "content": {
            "body": "## Acceptance\n\nok\n\n## Rollback\n\nok\n\n## Notes\n\n- plain\n",
        },
    }
    p2, w2 = pa.collect_validate_item_problems(ssot, item)
    assert any("assignee N/A until promote" in w for w in w2)

    ssot2 = json.loads(json.dumps(SAMPLE_SSOT))
    ssot2["fields"] = {**ssot2.get("fields", {}), "start_date": {}}
    ssot2["conventions"] = {
        **ssot2.get("conventions", {}),
        "require_attribution_on_exit": True,
        "body_sections": ["Acceptance", "Rollback", "Notes"],
    }
    item3 = {
        "id": VALID_PVTI,
        "status": "Ready",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "assignees": [],
        "content": {
            "body": "## Acceptance\n\n(TBD)\n\n## Rollback\n\nok\n\n## Notes\n\n- plain bullet\n",
        },
    }
    p3, w3 = pa.collect_validate_item_problems(ssot2, item3)
    assert any("placeholder (TBD)" in w for w in w3)
    assert any("not attributed" in p for p in p3)

    ssot4 = json.loads(json.dumps(SAMPLE_SSOT))
    ssot4["fields"] = {**ssot4.get("fields", {}), "start_date": {}}
    ssot4["conventions"] = {
        **ssot4.get("conventions", {}),
        "require_attribution_on_exit": True,
        "body_sections": ["Acceptance", "Rollback", "Notes"],
    }
    item4 = {
        "id": VALID_PVTI,
        "status": "In Progress",
        "priority": "p1",
        "size": "s",
        "estimate": "1",
        "content": {
            "body": "## Acceptance\n\nok\n\n## Rollback\n\nok\n\n## Notes\n\n- no attribution here\n",
        },
    }
    p4, w4 = pa.collect_validate_item_problems(ssot4, item4)
    assert any("not attributed" in p for p in p4)
    assert any("start_date.field_id missing" in w for w in w4)


# --- project_handlers run_board_bootstrap error paths ---


def test_run_board_bootstrap_handler_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    schema_fixture, _ = bs.load_board_shell_schema(REPO_ROOT)
    assert schema_fixture is not None

    assert (
        project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path, check=False))
        == project_cli.EXIT_USAGE
    )

    monkeypatch.setattr(
        project_cli,
        "_load_enabled_ssot",
        lambda root, cmd: (None, project_cli.EXIT_USAGE),
    )
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_USAGE

    ssot = _ssot()
    ssot_bad = json.loads(json.dumps(ssot))
    ssot_bad["fields"]["status"] = {}
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot_bad, 0))
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_USAGE

    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, 0))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_USAGE

    _template_root(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "project_templates_dir",
        lambda root: tmp_path / ".ai_infra" / "templates" / "project-board",
    )
    missing = tmp_path / ".ai_infra" / "templates" / "project-board" / "views-setup.md"
    missing.unlink()
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_USAGE

    _template_root(tmp_path)
    monkeypatch.setattr(bs, "load_board_shell_schema", lambda root: (None, "schema boom"))
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_USAGE

    _template_root(tmp_path)
    monkeypatch.setattr(bs, "load_board_shell_schema", lambda root: (schema_fixture, None))
    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": "many", "error": None},
    )
    monkeypatch.setattr(
        project_cli,
        "ensure_board_shell_fields",
        lambda *a, **k: project_cli.EXIT_GH,
    )
    assert (
        project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path, ensure_fields=True))
        == project_cli.EXIT_GH
    )

    monkeypatch.setattr(
        project_cli,
        "ensure_board_shell_fields",
        lambda *a, **k: project_cli.EXIT_OK,
    )
    monkeypatch.setattr(
        project_cli,
        "apply_board_shell_readme",
        lambda *a, **k: project_cli.EXIT_GH,
    )
    assert (
        project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path, apply_readme=True))
        == project_cli.EXIT_GH
    )

    _patch_common(monkeypatch, tmp_path, ssot)
    monkeypatch.setattr(project_cli, "read_project_readme", lambda s: (None, "readme gh fail"))
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_GH

    monkeypatch.setattr(project_cli, "read_project_readme", lambda s: ("# ok\n", None))
    monkeypatch.setattr(project_cli, "list_project_fields", lambda s: (None, "fields fail"))
    monkeypatch.setattr(
        project_cli,
        "read_project_views",
        lambda s: (_full_playground_views(), None),
    )
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "fields probe failed" in err

    monkeypatch.setattr(
        project_cli,
        "list_project_fields",
        lambda s: ([{"name": "Status"}], None),
    )
    monkeypatch.setattr(project_cli, "read_project_views", lambda s: (None, "views fail"))
    assert project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path)) == project_cli.EXIT_OK
    assert "view layout metadata opaque" in capsys.readouterr().err

    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 1, "limit": 5000, "reset_epoch": 0, "error": None},
    )
    assert (
        project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path, ensure_fields=True))
        == project_cli.EXIT_GH
    )


def test_run_board_bootstrap_live_with_real_probes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exercise read_project_* / list_project_fields via handler without mocks on those."""
    _template_root(tmp_path)
    ssot = _ssot()
    _patch_common(monkeypatch, tmp_path, ssot)

    def fake_gh(args: list[str], *, timeout_s: float = 60.0, input_text: str | None = None):
        if args[:2] == ["project", "view"]:
            return _gh_ok(json.dumps({"readme": "# README\n"}))
        if args[:2] == ["api", "graphql"] and "views(first" in " ".join(args):
            nodes = []
            for view in _full_playground_views():
                nodes.append(
                    {
                        "name": view["name"],
                        "layout": view["layout"],
                        "fields": {
                            "nodes": [{"name": n} for n in view["fields"]],
                        },
                    }
                )
            return _gh_ok(
                json.dumps({"data": {"node": {"views": {"nodes": nodes}}}})
            )
        if args[:2] == ["api", "graphql"] and "fields(first" in " ".join(args):
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "fields": {
                                    "nodes": [
                                        {"id": "PVTF_pri", "name": "Priority", "dataType": "SINGLE_SELECT"},
                                        {"id": "PVTF_size", "name": "Size", "dataType": "SINGLE_SELECT"},
                                    ]
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected gh")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    code = project_handlers.run_board_bootstrap(_bootstrap_args(tmp_path))
    assert code == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "missing field" in err or "recommended view" in err or err == ""


def test_cmd_board_bootstrap_delegates(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        project_handlers,
        "run_board_bootstrap",
        lambda args: project_cli.EXIT_OK,
    )
    args = _bootstrap_args(tmp_path)
    assert project_cli.cmd_board_bootstrap(args) == project_cli.EXIT_OK


# --- check_drift consumer profile ---


def test_run_checks_consumer_profile_not_board_only(tmp_path: Path) -> None:
    planning = tmp_path / ".local/index-and-planning/current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text(
        "# Tracker\n\nSTARTER-001\n\n## Active\n\n(none)\n",
        encoding="utf-8",
    )
    settings = tmp_path / ".local" / "user_settings"
    settings.mkdir(parents=True)
    (settings / "github.collaboration.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "owner": {"display_name": "T", "github_user": "@t"},
                "project_ssot": {
                    "enabled": True,
                    "sync_policy": "local_trackers",
                    "default_repo": "o/r",
                },
                "commit_provenance": {"ai_disclosure_mode": "none"},
            }
        ),
        encoding="utf-8",
    )
    assert cd.detect_profile(
        (tmp_path / ".local/index-and-planning/current/work-tracker.md").read_text(encoding="utf-8"),
        None,
        board_only=False,
    ) == "consumer"
    results = cd.run_checks(tmp_path)
    assert [r.check_id for r in results] == ["DRIFT-005", "DRIFT-008"]


def test_board_shell_view_alnum_match() -> None:
    live = [{"name": "StatusBoard", "layout": "BOARD_LAYOUT", "fields": ["Priority", "Size", "Estimate", "Start date"]}]
    schema = {"views": {"minimum": [{"name": "Status board", "layout": "BOARD_LAYOUT"}]}}
    problems, _ = bs.compare_views_to_schema(schema, live)
    assert not problems


def test_project_cli_remaining_gaps(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    ssot = _ssot()

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"data": {"node": []}})),
    )
    fields, err = project_cli.list_project_fields(ssot)
    assert fields is None and "metadata unavailable" in (err or "")

    schema_local = {
        "fields": {
            "required": [
                {"name": "Priority", "data_type": "single_select", "options": ["p1"]},
            ]
        }
    }
    monkeypatch.setattr(
        project_cli,
        "list_project_fields",
        lambda s: (
            [{"name": "Priority", "id": "PVTF_pri", "dataType": "SINGLE_SELECT"}],
            None,
        ),
    )
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("unexpected"))
    assert project_cli.ensure_board_shell_fields(REPO_ROOT, ssot, schema_local) == project_cli.EXIT_OK

    list_calls = {"n": 0}

    def fake_list(s):
        list_calls["n"] += 1
        return ([], None)

    def fake_gh_err(args: list[str], *, timeout_s: float = 60.0, input_text: str | None = None):
        if input_text and "createProjectV2Field" in input_text:
            return _gh_ok(json.dumps({"errors": [{"message": "field denied"}]}))
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "list_project_fields", fake_list)
    monkeypatch.setattr(project_cli, "run_gh", fake_gh_err)
    schema_one = {"fields": {"required": [{"name": "Estimate", "data_type": "number"}]}}
    assert project_cli.ensure_board_shell_fields(REPO_ROOT, ssot, schema_one) == project_cli.EXIT_OK
    assert "graphql errors" in capsys.readouterr().err


def test_section_body_content_empty_target_direct() -> None:
    assert pa.section_body_content("## A\n\nx", "   ") == ""


# --- board_shell.py: missing lines 228, 241, 244, 293 ---


def test_is_kit_dev_install_false_on_consumer_root(tmp_path: Path) -> None:
    """Line 228: is_kit_dev_install returns False when test_scaffold.py is absent."""
    assert bs.is_kit_dev_install(tmp_path) is False


def test_init_minimal_overlay_already_exists(tmp_path: Path) -> None:
    """Line 241: returns (1, ...) when overlay exists and force=False."""
    dest = bs.consumer_overlay_path(tmp_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("version: 1\n", encoding="utf-8")
    code, msg = bs.init_minimal_overlay(tmp_path, force=False)
    assert code == 1
    assert "already exists" in msg


def test_init_minimal_overlay_exemplar_missing(tmp_path: Path) -> None:
    """Line 244: returns (2, ...) when exemplar YAML is absent."""
    code, msg = bs.init_minimal_overlay(tmp_path, force=False)
    assert code == 2
    assert "missing" in msg


def test_bootstrap_view_fail_message_min_count_le_2() -> None:
    """Line 293: bootstrap_view_fail_message returns 2-view hint when min_count <= 2."""
    schema = {
        "views": {
            "minimum": [
                {"name": "Status board", "layout": "BOARD_LAYOUT"},
            ]
        }
    }
    problems = ["missing minimum view 'Prioritized backlog'"]
    live_views: list[dict] = []
    msg = bs.bootstrap_view_fail_message(schema, problems, live_views)
    assert "Turn A Status board" in msg or "2-view" in msg or "Minimal" in msg


# --- project_handlers.py: line 153 (handoff body gate + fetch fails) ---


def test_run_handoff_fetch_fails_no_body_gate_no_queue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Line 153: fetch fails, status_to is empty (not body-gate), _try_queue returns None → EXIT_GH."""
    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "some non-rate-limit gh error"),
    )
    # _try_queue_rate_limit returns None because error is not a rate-limit error
    args = argparse.Namespace(
        directory=tmp_path,
        id="PVTI_lAHOBl46-84A9KZxtest01",
        last=False,
        agent="implementer",
        next="verifier",
        to="",        # empty → no body gate → goes to _try_queue_rate_limit path
        text="",
        limit=100,
    )
    result = project_handlers.run_handoff(args)
    assert result == project_cli.EXIT_GH


# --- project_handlers.py: lines 340-342 (json.JSONDecodeError in close_linked_issue) ---


def test_run_close_linked_issue_invalid_json_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lines 340-342: gh issue view returns non-JSON → DEFERRED + EXIT_GH."""
    ssot = {**_ssot(), "conventions": {"close_linked_issue_on_cleanup": True, "body_sections": []}}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: ("PVTI_lAHOBl46-84A9KZxtest01", [], None),
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "42", {"repo": "o/r"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok("not-valid-json"),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        pr="12",
        repo="o/r",
        dry_run=False,
    )
    result = project_handlers.run_close_linked_issue(args)
    assert result == project_cli.EXIT_GH


# --- project_handlers.py: lines 518-544 (run_board_shell_init) ---


def test_run_board_shell_init_no_minimal_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """run_board_shell_init without --minimal → EXIT_USAGE."""
    args = argparse.Namespace(directory=tmp_path, minimal=False, force=False)
    result = project_handlers.run_board_shell_init(args)
    assert result == project_cli.EXIT_USAGE


def test_run_board_shell_init_exemplar_missing(tmp_path: Path) -> None:
    """run_board_shell_init --minimal but exemplar missing → EXIT_USAGE (code 2)."""
    args = argparse.Namespace(directory=tmp_path, minimal=True, force=False)
    result = project_handlers.run_board_shell_init(args)
    assert result == project_cli.EXIT_USAGE


def test_run_board_shell_init_overlay_exists_no_force(tmp_path: Path) -> None:
    """run_board_shell_init --minimal, overlay exists but no --force → EXIT_USAGE (code 1)."""
    dest = bs.consumer_overlay_path(tmp_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("version: 1\n", encoding="utf-8")
    args = argparse.Namespace(directory=tmp_path, minimal=True, force=False)
    result = project_handlers.run_board_shell_init(args)
    assert result == project_cli.EXIT_USAGE


def test_run_board_shell_init_writes_overlay(tmp_path: Path) -> None:
    """run_board_shell_init --minimal with exemplar present → EXIT_OK."""
    import shutil
    minimal_src = (
        REPO_ROOT / ".ai_infra" / "templates" / "user-settings" / "exemplars"
        / "board-shell.schema.minimal.yaml"
    )
    exemplar_dest_dir = (
        tmp_path / ".ai_infra" / "templates" / "user-settings" / "exemplars"
    )
    exemplar_dest_dir.mkdir(parents=True)
    if minimal_src.is_file():
        shutil.copy(minimal_src, exemplar_dest_dir / "board-shell.schema.minimal.yaml")
    else:
        (exemplar_dest_dir / "board-shell.schema.minimal.yaml").write_text(
            "version: 1\nviews:\n  minimum: []\n", encoding="utf-8"
        )
    args = argparse.Namespace(directory=tmp_path, minimal=True, force=False)
    result = project_handlers.run_board_shell_init(args)
    assert result == project_cli.EXIT_OK
