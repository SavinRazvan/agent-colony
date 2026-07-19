"""
File: test_project_cli_coverage.py
Path: tests/modules/install/test_project_cli_coverage.py
Role: Bulk unit tests for project_cli.py helpers and command edge paths toward 100% coverage.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - tests/modules/install/test_project_cli.py (SAMPLE_SSOT)
Notes:
 - Monkeypatches run_gh, load_project_ssot, GraphQL helpers — no live board.
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
from test_project_cli import SAMPLE_SSOT, VALID_PVTI, _write_collab  # noqa: E402

VALID_ITEM = VALID_PVTI
VALID_ITEM_B = "PVTI_lAHOBl46-84A9KZxcli02"
VALID_ITEM_C = "PVTI_lAHOBl46-84A9KZxcli03"


def _ensure_pr_scripts(tmp_path: Path) -> None:
    """Copy user_settings package so load_project_ssot can import it."""
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr"
    dst = tmp_path / ".ai_infra" / "scripts" / "pr"
    dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "user_settings.py",
        "user_settings_load.py",
        "user_settings_resolve.py",
        "user_settings_render.py",
        "local_workflow_paths.py",
    ):
        file_src = src / name
        if file_src.is_file():
            (dst / name).write_text(file_src.read_text(encoding="utf-8"), encoding="utf-8")


def _ssot(**overrides: object) -> dict:
    data = json.loads(json.dumps(SAMPLE_SSOT))
    data["conventions"] = {
        **data.get("conventions", {}),
        "body_sections": ["Acceptance", "Rollback", "Notes"],
        "require_attribution_on_exit": True,
        "one_in_progress_per_assignee": True,
        "claim": "set_assignee",
    }
    data.update(overrides)
    if "conventions" in overrides:
        data["conventions"] = {**data["conventions"], **overrides["conventions"]}  # type: ignore[arg-type]
    return data


def _board_item(
    item_id: str = VALID_ITEM,
    *,
    status: str = "Ready",
    body: str | None = None,
    title: str = "Slice",
) -> dict:
    default_body = (
        "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n- @test/implementer · claimed\n"
    )
    return {
        "id": item_id,
        "title": title,
        "status": status,
        "content": {"body": body if body is not None else default_body},
    }


def _patch_ssot(monkeypatch: pytest.MonkeyPatch, ssot: dict | None = None) -> dict:
    cfg = ssot or _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (cfg, []))
    return cfg


# --- helpers / low-level ---


def test_validate_card_body_skips_blank_section() -> None:
    assert project_cli.validate_card_body("## Acceptance\n", ["", "Acceptance"]) == []


def test_load_card_template_unknown_and_missing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown template"):
        project_cli.load_card_template(REPO_ROOT, "nope")
    missing_dir = tmp_path / ".ai_infra" / "templates" / "project-board"
    missing_dir.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        project_cli.load_card_template(tmp_path, "slice")


def test_load_last_item_id_corrupt_and_empty(tmp_path: Path) -> None:
    path = project_cli.session_last_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("not-json", encoding="utf-8")
    assert project_cli.load_last_item_id(tmp_path) is None
    path.write_text('["not", "dict"]', encoding="utf-8")
    assert project_cli.load_last_item_id(tmp_path) is None
    path.write_text('{"item_id": "  "}', encoding="utf-8")
    assert project_cli.load_last_item_id(tmp_path) is None


def test_is_placeholder_item_id_edges() -> None:
    assert project_cli.is_placeholder_item_id("")
    assert project_cli.is_placeholder_item_id("PVTI_")
    assert project_cli.is_placeholder_item_id("DI_short")
    assert project_cli.is_placeholder_item_id("PVTI_short")


def test_resolve_item_id_arg_edges(tmp_path: Path) -> None:
    project_cli.save_last_item_id(tmp_path, VALID_ITEM)
    ns = argparse.Namespace(id=VALID_ITEM, last=True)
    iid, code = project_cli.resolve_item_id_arg(tmp_path, ns, "test")
    assert iid is None and code == project_cli.EXIT_USAGE
    ns2 = argparse.Namespace(id="", last=True)
    iid2, code2 = project_cli.resolve_item_id_arg(tmp_path / "empty", ns2, "test")
    assert iid2 is None and code2 == project_cli.EXIT_USAGE
    ns3 = argparse.Namespace(id="", last=False)
    iid3, code3 = project_cli.resolve_item_id_arg(tmp_path, ns3, "test")
    assert iid3 is None and code3 == project_cli.EXIT_USAGE


def test_load_project_ssot_paths(tmp_path: Path) -> None:
    ssot, errs = project_cli.load_project_ssot(tmp_path)
    assert ssot is None
    assert errs and "missing" in errs[0]
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, _ssot())
    ssot2, errs2 = project_cli.load_project_ssot(tmp_path)
    assert errs2 == []
    assert ssot2 is not None and ssot2.get("enabled") is True


def test_load_project_ssot_missing_block(tmp_path: Path) -> None:
    path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"version": 1, "owner": {"github_user": "@x"}}), encoding="utf-8")
    ssot, errs = project_cli.load_project_ssot(tmp_path)
    assert ssot is None
    assert any("project_ssot" in e for e in errs)


def test_require_enabled_missing_keys_and_no_fallback_msg() -> None:
    ssot = {**SAMPLE_SSOT, "enabled": True, "owner": ""}
    assert project_cli.require_enabled(ssot)
    ssot2 = {**SAMPLE_SSOT, "enabled": False, "fallback": "none"}
    msg = project_cli.require_enabled(ssot2)[0]
    assert "fallback" not in msg


def test_normalize_github_handle_empty() -> None:
    assert project_cli.normalize_github_handle("") == ""
    assert project_cli.normalize_github_handle("alice") == "@alice"


def test_resolve_human_github_user(tmp_path: Path) -> None:
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, _ssot())
    assert project_cli.resolve_human_github_user(tmp_path) == "@test"


def test_format_agent_attribution_errors(tmp_path: Path) -> None:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    with pytest.raises(ValueError, match="github_user missing"):
        project_cli.format_agent_attribution(tmp_path, "implementer")
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    with pytest.raises(ValueError, match="agent name required"):
        project_cli.format_agent_attribution(tmp_path, "")
    monkeypatch.undo()


def test_set_item_assignee_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: (None, None, None, "resolve failed"),
    )
    ok, detail = project_cli.set_item_assignee(_ssot(), VALID_ITEM, "alice")
    assert not ok and "resolve failed" in detail
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "1", {"repo": "o/r"}, None),
    )
    ok2, detail2 = project_cli.set_item_assignee(_ssot(), VALID_ITEM, "")
    assert not ok2 and "login empty" in detail2
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="assignee fail"),
    )
    ok3, detail3 = project_cli.set_item_assignee(_ssot(), VALID_ITEM, "alice")
    assert not ok3 and "assignee fail" in detail3
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("other", "x", {}, None),
    )
    ok4, detail4 = project_cli.set_item_assignee(_ssot(), VALID_ITEM, "alice")
    assert not ok4 and "unsupported content kind" in detail4


def test_resolve_field_option_id_and_status_field_id_errors() -> None:
    ssot_no_field = json.loads(json.dumps(_ssot()))
    del ssot_no_field["fields"]["priority"]
    with pytest.raises(KeyError, match="fields.priority missing"):
        project_cli.resolve_field_option_id(ssot_no_field, "priority", "p1")
    ssot = json.loads(json.dumps(_ssot()))
    ssot["fields"]["priority"] = {"options": {"p0": "x"}}
    with pytest.raises(KeyError, match="field_id missing"):
        project_cli.resolve_field_option_id(ssot, "priority", "p0")
    with pytest.raises(KeyError, match="unknown size"):
        project_cli.resolve_field_option_id(_ssot(), "size", "xxl")
    ssot2 = json.loads(json.dumps(_ssot()))
    del ssot2["fields"]["status"]["field_id"]
    with pytest.raises(KeyError, match="status.field_id missing"):
        project_cli.status_field_id(ssot2)


def test_create_draft_item_regex_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=f"created {VALID_ITEM_B}", stderr=""
        ),
    )
    item_id, raw, err = project_cli.create_draft_item(_ssot(), "T", "")
    assert err is None
    assert item_id == VALID_ITEM_B
    assert raw is not None


def test_create_draft_item_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="create failed"),
    )
    item_id, raw, err = project_cli.create_draft_item(_ssot(), "T", "body")
    assert item_id is None and raw is None and "create failed" in (err or "")


def test_in_progress_conflicts_assignee_shapes() -> None:
    items = [
        "not-a-dict",
        {
            "id": VALID_ITEM_B,
            "status": "In Progress",
            "title": "Other",
            "content": {"body": ""},
            "assignees": [{"login": "test"}, "bob"],
        },
        {
            "id": VALID_ITEM_C,
            "status": "In Progress",
            "title": "@test/implementer work",
            "content": {"body": ""},
            "assignees": "single-string",
        },
    ]
    conflicts = project_cli.in_progress_conflicts_for_user(
        items, user_handle="@test", exclude_id=VALID_ITEM
    )
    assert len(conflicts) == 2


def test_append_notes_helper_edges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    ssot_off = {**ssot, "conventions": {**ssot["conventions"], "require_attribution_on_exit": False}}
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "list failed"),
    )
    ok, detail, code = project_cli.append_notes_helper(
        tmp_path, ssot_off, VALID_ITEM, agent="", text="plain", limit=10
    )
    assert not ok and code == project_cli.EXIT_GH
    monkeypatch.setattr(project_cli, "fetch_project_items", lambda *a, **k: ([], None))
    ok2, detail2, code2 = project_cli.append_notes_helper(
        tmp_path, ssot, VALID_ITEM, agent="", text="x", limit=10
    )
    assert not ok2 and code2 == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: "",
    )
    ok3, detail3, code3 = project_cli.append_notes_helper(
        tmp_path, ssot, VALID_ITEM, agent="implementer", text="x", limit=10
    )
    assert not ok3 and code3 == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    ok4, detail4, code4 = project_cli.append_notes_helper(
        tmp_path, ssot, "PVTI_lAHOBl46-84A9KZxmissing", agent="implementer", text="x", limit=10
    )
    assert not ok4 and code4 == project_cli.EXIT_NOT_FOUND
    monkeypatch.setattr(
        project_cli,
        "edit_item_body",
        lambda *a, **k: (False, "edit boom"),
    )
    ok5, detail5, code5 = project_cli.append_notes_helper(
        tmp_path, ssot, VALID_ITEM, agent="implementer", text="new note", limit=10
    )
    assert not ok5 and code5 == project_cli.EXIT_GH


def test_latest_notes_line_and_attributed() -> None:
    assert project_cli.latest_notes_line("no notes section") is None
    body = "## Notes\n\nhello\n\n## Other\n\n- bullet"
    assert project_cli.latest_notes_line(body) is None
    assert not project_cli.notes_line_attributed(None)
    assert not project_cli.notes_line_attributed("plain text")


def test_normalize_status_and_item_helpers() -> None:
    assert project_cli._normalize_status("in progress") == "in_progress"
    assert project_cli._normalize_status("review") == "in_review"
    assert project_cli._item_body({"body": "flat"}) == "flat"
    assert project_cli._item_body({"content": {"body": 123}}) == ""
    assert project_cli._item_title({"content": {"title": "nested"}}) == "nested"
    assert project_cli._item_title({}) == ""


def test_append_notes_to_body_empty_and_before_heading() -> None:
    body, changed = project_cli.append_notes_to_body("x", "  ")
    assert not changed
    src = "## Notes\n\n- first\n\n## Acceptance\n\nrest"
    new_body, changed2 = project_cli.append_notes_to_body(src, "second")
    assert changed2
    assert "- second" in new_body
    assert new_body.index("- second") < new_body.index("## Acceptance")


def test_find_items_mentioning_pr_no_match() -> None:
    items = [_board_item(body="unrelated")]
    assert project_cli.find_items_mentioning_pr(items, pr_number="999", pr_url="") == []


def test_fetch_project_items_edges(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="list err"),
    )
    items, err = project_cli.fetch_project_items(_ssot(), limit=5)
    assert items == [] and "list err" in (err or "")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="not-json", stderr=""),
    )
    items2, err2 = project_cli.fetch_project_items(_ssot(), limit=5)
    assert items2 == [] and "invalid JSON" in (err2 or "")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items": "bad"}', stderr=""),
    )
    items3, err3 = project_cli.fetch_project_items(_ssot(), limit=5)
    assert items3 == [] and err3 is None


def test_resolve_item_content_di_direct(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"data": {"node": {"id": "DI_x", "title": "Draft T"}}}),
            stderr="",
        ),
    )
    kind, cid, meta, err = project_cli.resolve_item_content(_ssot(), "DI_lAHOBl46-84A9KZx01")
    assert kind == "draft" and cid == "DI_lAHOBl46-84A9KZx01" and err is None


def test_resolve_item_content_graphql_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="gql down"),
    )
    kind, cid, meta, err = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind is None and "gql down" in (err or "")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="bad", stderr=""),
    )
    kind2, _, _, err2 = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind2 is None and "invalid graphql JSON" in (err2 or "")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"errors": [{"message": "not found"}]}),
            stderr="",
        ),
    )
    kind3, _, _, err3 = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind3 is None and err3 == "not found"
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=json.dumps({"data": {"node": None}}), stderr=""
        ),
    )
    kind4, _, _, err4 = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind4 is None and "not found" in (err4 or "")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"data": {"node": {"content": None}}}),
            stderr="",
        ),
    )
    kind5, _, _, err5 = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind5 is None and "no content" in (err5 or "")


def test_resolve_item_content_draft_bad_id_and_issue_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gql_draft = {
        "data": {
            "node": {
                "content": {
                    "__typename": "DraftIssue",
                    "id": "NOT_DI",
                    "title": "T",
                }
            }
        }
    }
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(gql_draft), stderr=""),
    )
    kind, _, _, err = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind is None and "unexpected draft id" in (err or "")
    gql_issue = {
        "data": {
            "node": {
                "content": {
                    "__typename": "Issue",
                    "number": None,
                    "title": "I",
                    "repository": {},
                }
            }
        }
    }
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(gql_issue), stderr=""),
    )
    kind2, _, _, err2 = project_cli.resolve_item_content(_ssot(), VALID_ITEM)
    assert kind2 is None and "missing number" in (err2 or "")


def test_resolve_draft_content_not_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "1", {}, None),
    )
    cid, title, err = project_cli.resolve_draft_content(_ssot(), VALID_ITEM)
    assert cid is None and "not a DraftIssue" in (err or "")


def test_edit_item_body_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="draft edit fail"),
    )
    ok, detail = project_cli.edit_item_body(_ssot(), VALID_ITEM, "body")
    assert not ok and "draft edit fail" in detail
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "9", {"repo": "o/r"}, None),
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="issue edit fail"),
    )
    ok2, detail2 = project_cli.edit_item_body(_ssot(), VALID_ITEM, "body")
    assert not ok2 and "issue edit fail" in detail2
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("weird", "x", {}, None),
    )
    ok3, detail3 = project_cli.edit_item_body(_ssot(), VALID_ITEM, "body")
    assert not ok3 and "unsupported content kind" in detail3


def test_set_item_status_key_error_and_gh_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    ok, detail = project_cli.set_item_status(_ssot(), VALID_ITEM, "nope")
    assert not ok and "unknown status" in detail
    monkeypatch.setattr(project_cli, "resolve_status_option_id", lambda *a, **k: "oid")
    monkeypatch.setattr(project_cli, "status_field_id", lambda *a, **k: "fid")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="status fail"),
    )
    ok2, detail2 = project_cli.set_item_status(_ssot(), VALID_ITEM, "ready")
    assert not ok2 and "status fail" in detail2


def test_build_export_snapshot_long_body() -> None:
    long_body = "x" * 600
    snap = project_cli.build_export_snapshot(_ssot(), [_board_item(body=long_body)])
    assert snap["totalCount"] == 1
    assert snap["items"][0]["body_excerpt"].endswith("...")


def test_resolve_item_id_for_pr_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="pr view fail"),
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "fetch fail"),
    )
    iid, cands, err = project_cli.resolve_item_id_for_pr(_ssot(), pr="7")
    assert iid is None and "fetch fail" in (err or "")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"body": "", "url": "https://github.com/o/r/pull/7", "number": 7}),
            stderr="",
        ),
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [
                _board_item(item_id=VALID_ITEM_B, body="pull/7"),
                _board_item(item_id=VALID_ITEM_C, body="also /pull/7"),
            ],
            None,
        ),
    )
    iid2, cands2, err2 = project_cli.resolve_item_id_for_pr(_ssot(), pr="7")
    assert iid2 is None and len(cands2) == 2 and "ambiguous" in (err2 or "")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], None),
    )
    iid3, cands3, err3 = project_cli.resolve_item_id_for_pr(_ssot(), pr="7")
    assert iid3 is None and "no project item found" in (err3 or "")


# --- commands ---


def test_cmd_status_text_and_enabled_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = {**SAMPLE_SSOT, "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(directory=tmp_path, json=False)
    assert project_cli.cmd_status(args) == project_cli.EXIT_USAGE
    out = capsys.readouterr()
    assert "enabled:" in out.out
    assert "note:" in out.err


def test_cmd_status_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_ssot(monkeypatch)
    args = argparse.Namespace(directory=tmp_path, json=True)
    assert project_cli.cmd_status(args) == project_cli.EXIT_OK


def test_cmd_list_text_filters_and_edges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {
        "items": [
            {"id": "a", "title": "A", "status": "In Progress"},
            "bad-item",
            {"id": "b", "title": "B", "status": "In Review"},
        ]
    }
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (_ssot(), []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )
    args = argparse.Namespace(directory=tmp_path, status="inprogress", limit=10, json=False)
    assert project_cli.cmd_list(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "a\t" in out
    args2 = argparse.Namespace(directory=tmp_path, status="review", limit=10, json=False)
    project_cli.cmd_list(args2)
    args3 = argparse.Namespace(directory=tmp_path, status="done", limit=10, json=False)
    project_cli.cmd_list(args3)
    out3 = capsys.readouterr().out
    assert "(no items)" in out3


def test_cmd_list_invalid_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="bad", stderr=""),
    )
    args = argparse.Namespace(directory=tmp_path, status="", limit=10, json=True)
    assert project_cli.cmd_list(args) == project_cli.EXIT_GH


def test_cmd_create_and_template_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    routed: list[str] = []

    def fake_template(args: argparse.Namespace) -> int:
        routed.append("template")
        return 0

    monkeypatch.setattr(project_cli, "cmd_create_from_template", fake_template)
    args = argparse.Namespace(directory=tmp_path, template="slice", title="T", body="")
    assert project_cli.cmd_create(args) == 0
    assert routed == ["template"]


def test_cmd_create_plain(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(
        project_cli,
        "create_draft_item",
        lambda *a, **k: (VALID_ITEM, '{"id":"x"}', None),
    )
    args = argparse.Namespace(directory=tmp_path, template=None, title="T", body="")
    assert project_cli.cmd_create(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert f"item_id={VALID_ITEM}" in out
    assert project_cli.load_last_item_id(tmp_path) == VALID_ITEM


def test_cmd_create_from_template_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "load_card_template",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("bad tmpl")),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        template="slice",
        title="T",
        acceptance="a",
        rollback="r",
        notes="",
        status="",
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_USAGE


def test_cmd_create_from_template_gh_and_status_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(project_cli, "load_card_template", lambda *a, **k: "## Acceptance\n\n{{acceptance}}\n\n## Rollback\n\n{{rollback}}\n\n## Notes\n\n{{notes}}\n")
    monkeypatch.setattr(
        project_cli,
        "create_draft_item",
        lambda *a, **k: (None, None, "create err"),
    )
    args = argparse.Namespace(
        directory=REPO_ROOT,
        template="slice",
        title="T",
        acceptance="a",
        rollback="r",
        notes="",
        status="ready",
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli,
        "create_draft_item",
        lambda *a, **k: (VALID_ITEM, "", None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (False, "status err"),
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_GH


def test_cmd_set_status_resolve_id_and_print(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    args = argparse.Namespace(
        directory=tmp_path, id="", last=False, to="ready", agent="implementer"
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    args2 = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, to="ready", agent="implementer"
    )
    assert project_cli.cmd_set_status(args2) == project_cli.EXIT_OK
    assert "set-status:" in capsys.readouterr().out


def test_cmd_set_field(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    args_bad = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, field="nope", to="p1"
    )
    assert project_cli.cmd_set_field(args_bad) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="field fail"),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, field="priority", to="p1"
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_OK
    assert "set-field:" in capsys.readouterr().out


def test_cmd_get_text_and_fetch_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    args = argparse.Namespace(directory=tmp_path, id="", last=True, limit=10, json=False)
    assert project_cli.cmd_get(args) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "get list fail"),
    )
    args2 = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, limit=10, json=False
    )
    assert project_cli.cmd_get(args2) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    assert project_cli.cmd_get(args2) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "--- body ---" in out


def test_cmd_append_notes_idempotent_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "idempotent", project_cli.EXIT_OK),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, text="x", agent="implementer", limit=50
    )
    assert project_cli.cmd_append_notes(args) == project_cli.EXIT_OK
    assert "idempotent skip" in capsys.readouterr().out


def test_cmd_set_assignee_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    pr_dir = tmp_path / ".ai_infra" / "scripts" / "pr"
    pr_dir.mkdir(parents=True)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        login="alice",
        agent="implementer",
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (True, "alice"),
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_OK
    assert "set-assignee:" in capsys.readouterr().out
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "DraftIssue has no GitHub Assignees"),
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_VALIDATION
    ssot_outbox = {**ssot, "outbox": {"enabled": True, "path": "outbox/q.jsonl"}}
    _patch_ssot(monkeypatch, ssot_outbox)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "rate limit exceeded"),
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_QUEUED


def test_cmd_set_assignee_no_login_no_user(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, login="", agent="implementer"
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_USAGE


def test_cmd_claim_edges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="",
        text="claimed",
        limit=50,
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    args2 = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="claimed",
        limit=50,
    )
    assert project_cli.cmd_claim(args2) == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "claim fetch fail"),
    )
    assert project_cli.cmd_claim(args2) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (False, "unknown status 'nope'"),
    )
    assert project_cli.cmd_claim(args2) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (True, "oid"),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (True, "test"),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes fail", project_cli.EXIT_GH),
    )
    assert project_cli.cmd_claim(args2) == project_cli.EXIT_GH


def test_cmd_claim_notes_queued_after_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "API rate limit exceeded", project_cli.EXIT_GH),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="claimed",
        limit=50,
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_QUEUED
    assert "Notes QUEUED" in capsys.readouterr().err


def test_cmd_handoff_edges(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="note",
        limit=50,
    )
    assert (
        project_cli.cmd_handoff(
            argparse.Namespace(**{**base, "agent": "", "next": "verifier"})
        )
        == project_cli.EXIT_USAGE
    )
    assert (
        project_cli.cmd_handoff(
            argparse.Namespace(**{**base, "agent": "implementer", "next": ""})
        )
        == project_cli.EXIT_USAGE
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "handoff fetch fail"),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item(status="In Progress")], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (False, "unknown status 'bad'"),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (True, "oid"),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes err", project_cli.EXIT_VALIDATION),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_VALIDATION


def test_cmd_validate_item_extra_problems(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = _ssot()
    _patch_ssot(monkeypatch, ssot)
    bad_body = "## Acceptance\n\n## Rollback\n\n## Notes\n\n- plain un attributed line\n"
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: (
            [_board_item(body=bad_body, status="WeirdStatus")],
            None,
        ),
    )
    args = argparse.Namespace(directory=REPO_ROOT, id=VALID_ITEM, last=False, limit=50)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_VALIDATION


def test_cmd_last_and_load_enabled_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = argparse.Namespace(directory=tmp_path)
    assert project_cli.cmd_last(args) == project_cli.EXIT_USAGE
    project_cli.save_last_item_id(tmp_path, VALID_ITEM)
    assert project_cli.cmd_last(args) == project_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == VALID_ITEM
    monkeypatch.setattr(
        project_cli,
        "load_project_ssot",
        lambda root: (None, ["missing ssot"]),
    )
    args2 = argparse.Namespace(directory=tmp_path, status="", limit=10, json=False)
    assert project_cli.cmd_list(args2) == project_cli.EXIT_USAGE


def test_cmd_queue_all_ops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="x",
        to="ready",
        next="verifier",
        login="alice",
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "set-status", "to": ""})
        )
        == project_cli.EXIT_USAGE
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "handoff", "next": ""})
        )
        == project_cli.EXIT_USAGE
    )
    assert (
        project_cli.cmd_queue(argparse.Namespace(**{**base, "op": "claim"}))
        == project_cli.EXIT_QUEUED
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "set-assignee", "login": ""})
        )
        == project_cli.EXIT_QUEUED
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "set-status", "to": "ready"})
        )
        == project_cli.EXIT_QUEUED
    )


def test_cmd_outbox_status_graphql_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import project_outbox  # noqa: E402

    ssot = _ssot()
    ssot["outbox"] = {"enabled": True, "path": "outbox/t.jsonl"}
    _patch_ssot(monkeypatch, ssot)

    def _rl_err() -> dict:
        return {"remaining": None, "limit": None, "reset_epoch": None, "error": "timeout"}

    monkeypatch.setattr(project_outbox, "graphql_rate_limit", _rl_err)
    args = argparse.Namespace(directory=tmp_path)
    assert project_cli.cmd_outbox_status(args) == project_cli.EXIT_OK
    assert "graphql: error" in capsys.readouterr().out


def test_cmd_doctor_edges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import project_outbox  # noqa: E402

    ssot = _ssot()
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    ssot_bad = json.loads(json.dumps(ssot))
    del ssot_bad["fields"]["status"]["options"]["ready"]
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot_bad, []))
    args = argparse.Namespace(directory=REPO_ROOT)
    assert project_cli.cmd_doctor(args) == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))

    def _rl_low() -> dict:
        return {"remaining": 10, "limit": 5000, "reset_epoch": 1700000000, "error": None}

    monkeypatch.setattr(project_outbox, "graphql_rate_limit", _rl_low)
    assert project_cli.cmd_doctor(args) == project_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "skipping live gh" in err or "low GraphQL quota" in err

    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": 5000, "limit": 5000, "reset_epoch": 1700000000, "error": None},
    )
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(
            returncode=1, stdout="", stderr="API rate limit exceeded"
        ),
    )
    assert project_cli.cmd_doctor(args) == project_cli.EXIT_OK
    assert "rate-limited" in capsys.readouterr().err

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="network down"),
    )
    assert project_cli.cmd_doctor(args) == project_cli.EXIT_GH

    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items":[]}', stderr=""),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": "bad", "limit": 5000, "reset_epoch": 1700000000, "error": None},
    )
    assert project_cli.cmd_doctor(args) == project_cli.EXIT_OK


def test_cmd_find_by_pr_and_export_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: (None, ["a", "b"], "ambiguous"),
    )
    args = argparse.Namespace(
        directory=tmp_path, pr="7", repo="", limit=50, json=False
    )
    assert project_cli.cmd_find_by_pr(args) == project_cli.EXIT_NOT_FOUND
    err = capsys.readouterr().err
    assert "candidates:" in err
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: (VALID_ITEM, [VALID_ITEM], None),
    )
    args_json = argparse.Namespace(
        directory=tmp_path, pr="7", repo="", limit=50, json=True
    )
    assert project_cli.cmd_find_by_pr(args_json) == project_cli.EXIT_OK
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    out_file = tmp_path / "snap.json"
    args_export = argparse.Namespace(
        directory=tmp_path,
        output=str(out_file),
        limit=50,
        json=True,
        stdout=False,
    )
    assert project_cli.cmd_export(args_export) == project_cli.EXIT_OK
    assert out_file.is_file()
    out = capsys.readouterr().out
    assert "Wrote" in out
    assert '"schema"' in out


# --- residual coverage toward 100% ---


def test_is_placeholder_pvti_punctuation_only() -> None:
    assert project_cli.is_placeholder_item_id("PVTI_---")


def test_load_project_ssot_empty_cfg_and_bad_block(tmp_path: Path) -> None:
    _ensure_pr_scripts(tmp_path)
    path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"version": 1}), encoding="utf-8")
    ssot, errs = project_cli.load_project_ssot(tmp_path)
    assert ssot is None and any("empty" in e or "missing" in e for e in errs)
    path.write_text(
        yaml.safe_dump({"version": 1, "project_ssot": "not-a-dict"}),
        encoding="utf-8",
    )
    ssot2, errs2 = project_cli.load_project_ssot(tmp_path)
    assert ssot2 is None and any("missing block" in e for e in errs2)


def test_format_note_line_attr_with_dot_prefix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixed_ts = "2026-07-18T10:14:40Z"
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "utc_note_timestamp", lambda: fixed_ts)
    line = project_cli.format_note_line(
        tmp_path, "implementer", "@test/implementer · extra tail"
    )
    assert line == f"@test/implementer · {fixed_ts} · extra tail"
    line2 = project_cli.format_note_line(tmp_path, "implementer", "@test/implementer · ")
    assert line2 == f"@test/implementer · {fixed_ts}"


def test_normalize_status_inprogress_alias() -> None:
    assert project_cli._normalize_status("inprogress") == "in_progress"


def test_load_project_ssot_cfg_none(tmp_path: Path) -> None:
    _ensure_pr_scripts(tmp_path)
    path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("", encoding="utf-8")
    ssot, errs = project_cli.load_project_ssot(tmp_path)
    assert ssot is None and errs


def test_cmd_create_from_template_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path,
        template="slice",
        title="T",
        acceptance="a",
        rollback="r",
        notes="",
        status="",
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_USAGE


def test_cmd_set_assignee_ssot_and_id_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, login="alice", agent="implementer"
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    args2 = argparse.Namespace(
        directory=tmp_path, id="", last=False, login="alice", agent="implementer"
    )
    assert project_cli.cmd_set_assignee(args2) == project_cli.EXIT_USAGE


def test_cmd_claim_ssot_none_and_user_resolve_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="claimed",
        limit=50,
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: (_ for _ in ()).throw(RuntimeError("no user")),
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_USAGE


def test_cmd_claim_fetch_queued_and_status_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    ssot_out = {**ssot, "outbox": {"enabled": True, "path": "outbox/c.jsonl"}}
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot_out)
    _patch_ssot(monkeypatch, ssot_out)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="claimed",
        limit=50,
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "API rate limit exceeded"),
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_QUEUED
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (False, "network down"),
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_GH


def test_cmd_handoff_ssot_id_and_fetch_queue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="note",
        limit=50,
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_USAGE
    ssot_out = {**_ssot(), "outbox": {"enabled": True, "path": "outbox/h2.jsonl"}}
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot_out)
    _patch_ssot(monkeypatch, ssot_out)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    assert (
        project_cli.cmd_handoff(
            argparse.Namespace(**{**base, "id": "", "last": False})
        )
        == project_cli.EXIT_USAGE
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "API rate limit exceeded"),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_QUEUED


def test_cmd_handoff_status_gh_fail_non_rate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item(status="In Progress")], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (False, "network down"),
    )
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="note",
        limit=50,
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_GH


def test_cmd_validate_item_id_resolve_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_ssot(monkeypatch)
    args = argparse.Namespace(directory=tmp_path, id="", last=False, limit=50)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_USAGE


def test_cmd_queue_ssot_id_handoff_and_enqueue_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="note",
        to="in_review",
        next="verifier",
        login="alice",
    )
    assert (
        project_cli.cmd_queue(argparse.Namespace(**{**base, "op": "append-notes"}))
        == project_cli.EXIT_USAGE
    )
    _patch_ssot(monkeypatch)
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "id": "", "op": "append-notes", "text": "x"})
        )
        == project_cli.EXIT_USAGE
    )
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(
                **{
                    **base,
                    "op": "handoff",
                    "next": "verifier",
                    "text": "handoff note",
                    "to": "in_review",
                }
            )
        )
        == project_cli.EXIT_QUEUED
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: (_ for _ in ()).throw(ValueError("bad user")),
    )
    import project_outbox  # noqa: E402

    monkeypatch.setattr(
        project_outbox,
        "enqueue_op",
        lambda *a, **k: (None, "validation failed"),
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "append-notes", "text": "x"})
        )
        == project_cli.EXIT_VALIDATION
    )


def test_cmd_doctor_require_enabled_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    assert project_cli.cmd_doctor(argparse.Namespace(directory=tmp_path)) == project_cli.EXIT_USAGE


def test_run_gh_invokes_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    captured: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> SimpleNamespace:
        captured.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    proc = project_cli.run_gh(["version"])
    assert proc.returncode == 0
    assert captured[0][:2] == ["gh", "version"]


def test_load_enabled_ssot_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**SAMPLE_SSOT, "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    out, code = project_cli._load_enabled_ssot(tmp_path, "list")
    assert out is None and code == project_cli.EXIT_USAGE


def test_in_progress_conflicts_skips_non_in_progress() -> None:
    items = [
        {
            "id": VALID_ITEM_B,
            "status": "Ready",
            "title": "@test/implementer todo",
            "content": {"body": ""},
        },
        {
            "id": VALID_ITEM_C,
            "status": "In Progress",
            "title": "@test/implementer active",
            "content": {"body": ""},
        },
    ]
    conflicts = project_cli.in_progress_conflicts_for_user(
        items, user_handle="@test", exclude_id=VALID_ITEM
    )
    assert len(conflicts) == 1
    assert conflicts[0]["id"] == VALID_ITEM_C


def test_cmd_handoff_bad_agent_attribution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)

    def _bad_attr(root: Path, agent: str) -> str:
        if agent == "bad-next":
            raise ValueError("bad agent name")
        return "@test/implementer"

    monkeypatch.setattr(project_cli, "format_agent_attribution", _bad_attr)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        next="bad-next",
        to="in_review",
        text="note",
        limit=50,
    )
    assert project_cli.cmd_handoff(args) == project_cli.EXIT_USAGE


def test_in_progress_conflicts_excludes_target() -> None:
    items = [
        {
            "id": VALID_ITEM,
            "status": "In Progress",
            "title": "@test/implementer",
            "content": {"body": ""},
        }
    ]
    assert (
        project_cli.in_progress_conflicts_for_user(
            items, user_handle="@test", exclude_id=VALID_ITEM
        )
        == []
    )


def test_cmd_status_load_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        project_cli, "load_project_ssot", lambda root: (None, ["boom"])
    )
    assert project_cli.cmd_status(argparse.Namespace(directory=tmp_path, json=False)) == 2


def test_cmd_list_non_list_items(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items": 1}', stderr=""),
    )
    assert (
        project_cli.cmd_list(
            argparse.Namespace(directory=tmp_path, status="", limit=5, json=True)
        )
        == 0
    )


def test_cmd_create_disabled_and_gh_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(directory=tmp_path, template=None, title="T", body="")
    assert project_cli.cmd_create(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "create_draft_item",
        lambda *a, **k: (None, None, "create failed"),
    )
    assert project_cli.cmd_create(args) == project_cli.EXIT_GH


def test_cmd_create_from_template_missing_sections(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    ssot["conventions"]["body_sections"] = ["ExtraSection"]
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(
        project_cli,
        "load_card_template",
        lambda *a, **k: "## Acceptance\n\nonly\n",
    )
    args = argparse.Namespace(
        directory=tmp_path,
        template="slice",
        title="T",
        acceptance="a",
        rollback="r",
        notes="",
        status="",
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_VALIDATION


def test_cmd_set_status_disabled_and_non_rate_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, to="ready", agent="implementer"
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="network down"),
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_GH


def test_cmd_set_field_resolve_and_key_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, field="priority", to="p1"
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    args2 = argparse.Namespace(
        directory=tmp_path, id="", last=False, field="priority", to="p1"
    )
    assert project_cli.cmd_set_field(args2) == project_cli.EXIT_USAGE
    ssot_bad = json.loads(json.dumps(_ssot()))
    ssot_bad["fields"]["priority"]["options"] = {}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot_bad, []))
    args3 = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, field="priority", to="p1"
    )
    assert project_cli.cmd_set_field(args3) == project_cli.EXIT_USAGE


def test_resolve_item_id_for_pr_single_match_and_bad_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="not-json", stderr=""),
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item(item_id=VALID_ITEM_B, body="pull/42")], None),
    )
    iid, cands, err = project_cli.resolve_item_id_for_pr(_ssot(), pr="42", repo="o/r")
    assert iid == VALID_ITEM_B and err is None


def test_resolve_item_content_di_json_decode_and_issue_default_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="bad-json", stderr=""),
    )
    kind, _, _, err = project_cli.resolve_item_content(_ssot(), "DI_lAHOBl46-84A9KZx01")
    assert kind == "draft" and err is None
    gql_issue = {
        "data": {
            "node": {
                "content": {
                    "__typename": "Issue",
                    "number": 1,
                    "title": "I",
                    "body": "b",
                    "repository": {},
                }
            }
        }
    }
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(gql_issue), stderr=""),
    )
    kind2, cid2, meta2, err2 = project_cli.resolve_item_content(
        {**_ssot(), "default_repo": "SavinRazvan/repo"}, VALID_ITEM
    )
    assert kind2 == "issue" and cid2 == "1" and err2 is None
    assert meta2 is not None
    assert meta2.get("title") == "I"
    assert meta2.get("repo") == "SavinRazvan/repo"


def test_resolve_draft_content_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: (None, None, None, "boom"),
    )
    cid, title, err = project_cli.resolve_draft_content(_ssot(), VALID_ITEM)
    assert cid is None and err == "boom"


def test_cmd_get_and_append_notes_load_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    assert (
        project_cli.cmd_get(
            argparse.Namespace(
                directory=tmp_path, id=VALID_ITEM, last=False, limit=10, json=True
            )
        )
        == project_cli.EXIT_USAGE
    )
    assert (
        project_cli.cmd_append_notes(
            argparse.Namespace(
                directory=tmp_path,
                id=VALID_ITEM,
                last=False,
                text="x",
                agent="implementer",
                limit=10,
            )
        )
        == project_cli.EXIT_USAGE
    )
    _patch_ssot(monkeypatch)
    assert (
        project_cli.cmd_append_notes(
            argparse.Namespace(
                directory=tmp_path, id="", last=False, text="x", agent="implementer", limit=10
            )
        )
        == project_cli.EXIT_USAGE
    )


def test_cmd_set_assignee_resolve_login_and_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: (_ for _ in ()).throw(RuntimeError("no user")),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, login="", agent="implementer"
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda *a, **k: (False, "network down"),
    )
    assert project_cli.cmd_set_assignee(
        argparse.Namespace(
            directory=tmp_path, id=VALID_ITEM, last=False, login="alice", agent="implementer"
        )
    ) == project_cli.EXIT_GH


def test_cmd_claim_not_found_and_assignee_ok(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], None),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="claimed",
        limit=50,
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_NOT_FOUND
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(project_cli, "set_item_assignee", lambda *a, **k: (True, "test"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_OK
    assert "assignee=@test" in capsys.readouterr().out


def test_cmd_handoff_not_found_and_queued_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    ssot_out = {**ssot, "outbox": {"enabled": True, "path": "outbox/h.jsonl"}}
    _write_collab(tmp_path, ssot_out)
    _patch_ssot(monkeypatch, ssot_out)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="note",
        limit=50,
    )
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], None),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_NOT_FOUND
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item(status="In Progress")], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda *a, **k: (False, "API rate limit exceeded"),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_QUEUED
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "oid"))
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "API rate limit exceeded", project_cli.EXIT_GH),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_QUEUED


def test_cmd_validate_item_load_and_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(directory=tmp_path, id=VALID_ITEM, last=False, limit=50)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "validate list fail"),
    )
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], None),
    )
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_NOT_FOUND


def test_cmd_queue_append_notes_and_resolve_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _ensure_pr_scripts(tmp_path)
    _write_collab(tmp_path, ssot)
    _patch_ssot(monkeypatch, ssot)
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="",
        to="ready",
        next="verifier",
        login="",
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "append-notes", "text": ""})
        )
        == project_cli.EXIT_USAGE
    )
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: (_ for _ in ()).throw(RuntimeError("no login")),
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**{**base, "op": "set-assignee", "login": ""})
        )
        == project_cli.EXIT_USAGE
    )


def test_cmd_outbox_and_doctor_load_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    assert (
        project_cli.cmd_outbox_status(argparse.Namespace(directory=tmp_path))
        == project_cli.EXIT_USAGE
    )
    assert (
        project_cli.cmd_outbox_flush(
            argparse.Namespace(directory=tmp_path, max=None, limit=100)
        )
        == project_cli.EXIT_USAGE
    )
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (None, ["missing"]))
    assert project_cli.cmd_doctor(argparse.Namespace(directory=tmp_path)) == project_cli.EXIT_USAGE


def test_cmd_doctor_missing_user_and_template(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    _patch_ssot(monkeypatch, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "")
    assert project_cli.cmd_doctor(argparse.Namespace(directory=REPO_ROOT)) == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "project_templates_dir",
        lambda root: tmp_path / "missing-templates",
    )
    assert project_cli.cmd_doctor(argparse.Namespace(directory=REPO_ROOT)) == project_cli.EXIT_USAGE


def test_cmd_doctor_graphql_error_in_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import project_outbox  # noqa: E402

    ssot = _ssot()
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='{"items":[]}', stderr=""),
    )
    monkeypatch.setattr(
        project_outbox,
        "graphql_rate_limit",
        lambda: {"remaining": None, "limit": None, "reset_epoch": None, "error": "timeout"},
    )
    assert project_cli.cmd_doctor(argparse.Namespace(directory=REPO_ROOT)) == project_cli.EXIT_OK
    assert "rate_limit: timeout" in capsys.readouterr().err


def test_cmd_find_by_pr_disabled_and_export_fetch_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    assert (
        project_cli.cmd_find_by_pr(
            argparse.Namespace(directory=tmp_path, pr="1", repo="", limit=50, json=True)
        )
        == project_cli.EXIT_USAGE
    )
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: (VALID_ITEM, [VALID_ITEM], None),
    )
    args_text = argparse.Namespace(
        directory=tmp_path, pr="1", repo="", limit=50, json=False
    )
    assert project_cli.cmd_find_by_pr(args_text) == project_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == VALID_ITEM
    ssot_off = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot_off, []))
    assert (
        project_cli.cmd_export(
            argparse.Namespace(
                directory=tmp_path, output=None, limit=50, json=False, stdout=True
            )
        )
        == project_cli.EXIT_USAGE
    )
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([], "export fail"),
    )
    assert (
        project_cli.cmd_export(
            argparse.Namespace(
                directory=tmp_path, output=None, limit=50, json=False, stdout=True
            )
        )
        == project_cli.EXIT_GH
    )


# --- residual lines toward 100% ---


def test_load_project_ssot_empty_collab_file(tmp_path: Path) -> None:
    _ensure_pr_scripts(tmp_path)
    path = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("", encoding="utf-8")
    ssot, errs = project_cli.load_project_ssot(tmp_path)
    assert ssot is None
    assert errs and "missing or empty" in errs[0]


def test_format_note_line_attr_prefix_empty_rest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(project_cli, "utc_note_timestamp", lambda: "2026-01-01T00:00:00Z")
    out = project_cli.format_note_line(tmp_path, "implementer", "@test/implementer")
    assert out == "@test/implementer · 2026-01-01T00:00:00Z"


def test_normalize_status_inprogress_alias() -> None:
    assert project_cli._normalize_status("inprogress") == "in_progress"
    assert project_cli._normalize_status("review") == "in_review"


def test_in_progress_conflicts_skips_non_in_progress() -> None:
    items = [
        {"id": VALID_ITEM_B, "status": "Ready", "title": "@test/x", "content": {"body": ""}},
        {
            "id": VALID_ITEM,
            "status": "In Progress",
            "title": "keep",
            "content": {"body": "@test/implementer"},
        },
    ]
    conflicts = project_cli.in_progress_conflicts_for_user(
        items, user_handle="@test", exclude_id=VALID_ITEM
    )
    assert conflicts == []


def test_cmd_create_from_template_ssot_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path,
        title="T",
        template="slice",
        acceptance="a",
        rollback="r",
        notes="",
        status="ready",
    )
    assert project_cli.cmd_create_from_template(args) == project_cli.EXIT_USAGE


def test_cmd_set_assignee_early_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, login="alice", agent="x"
    )
    assert project_cli.cmd_set_assignee(args) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    args2 = argparse.Namespace(
        directory=tmp_path, id="", last=False, login="alice", agent="x"
    )
    assert project_cli.cmd_set_assignee(args2) == project_cli.EXIT_USAGE


def test_cmd_claim_resolve_user_exception_and_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "resolve_human_github_user",
        lambda root: (_ for _ in ()).throw(RuntimeError("no user")),
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, agent="implementer", text="x", limit=10
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_USAGE
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(project_cli, "in_progress_conflicts_for_user", lambda *a, **k: [])
    monkeypatch.setattr(
        project_cli, "set_item_status", lambda *a, **k: (False, "board down")
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: None)
    assert project_cli.cmd_claim(args) == project_cli.EXIT_GH


def test_cmd_claim_rate_limit_queues(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(project_cli, "in_progress_conflicts_for_user", lambda *a, **k: [])
    monkeypatch.setattr(
        project_cli, "set_item_status", lambda *a, **k: (False, "rate limit")
    )
    monkeypatch.setattr(
        project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED
    )
    args = argparse.Namespace(
        directory=tmp_path, id=VALID_ITEM, last=False, agent="implementer", text="x", limit=10
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_QUEUED


def test_cmd_handoff_early_and_format_and_gh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="",
        limit=10,
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_USAGE
    _patch_ssot(monkeypatch)
    args_bad_id = argparse.Namespace(**{**base, "id": ""})
    assert project_cli.cmd_handoff(args_bad_id) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli,
        "format_agent_attribution",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("bad attr")),
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_cli, "format_agent_attribution", lambda *a, **k: "@test/verifier"
    )
    monkeypatch.setattr(project_cli, "format_note_line", lambda *a, **k: "note")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda *a, **k: ([_board_item()], None),
    )
    monkeypatch.setattr(
        project_cli, "set_item_status", lambda *a, **k: (False, "fail status")
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: None)
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_GH
    monkeypatch.setattr(
        project_cli, "_try_queue_rate_limit", lambda *a, **k: project_cli.EXIT_QUEUED
    )
    assert project_cli.cmd_handoff(argparse.Namespace(**base)) == project_cli.EXIT_QUEUED


def test_cmd_validate_item_bad_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_ssot(monkeypatch)
    args = argparse.Namespace(directory=tmp_path, id="", last=False, limit=10)
    assert project_cli.cmd_validate_item(args) == project_cli.EXIT_USAGE


def test_cmd_queue_early_and_validation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import project_outbox  # noqa: E402

    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        agent="implementer",
        text="x",
        to="ready",
        next="verifier",
        login="alice",
        op="claim",
    )
    assert project_cli.cmd_queue(argparse.Namespace(**base)) == project_cli.EXIT_USAGE
    ssot2 = _ssot()
    ssot2["outbox"] = {"enabled": True, "path": "outbox/t.jsonl"}
    _patch_ssot(monkeypatch, ssot2)
    args_bad = argparse.Namespace(**{**base, "id": ""})
    assert project_cli.cmd_queue(args_bad) == project_cli.EXIT_USAGE
    monkeypatch.setattr(
        project_outbox, "enqueue_op", lambda *a, **k: (None, "enqueue boom")
    )
    assert (
        project_cli.cmd_queue(argparse.Namespace(**{**base, "op": "handoff"}))
        == project_cli.EXIT_VALIDATION
    )


def test_cmd_doctor_enabled_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    assert (
        project_cli.cmd_doctor(argparse.Namespace(directory=tmp_path))
        == project_cli.EXIT_USAGE
    )


def test_cmd_find_by_pr_prints_plain_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_ssot(monkeypatch)
    monkeypatch.setattr(
        project_cli,
        "resolve_item_id_for_pr",
        lambda *a, **k: (VALID_ITEM, [], None),
    )
    args = argparse.Namespace(directory=tmp_path, pr="9", repo="", limit=20, json=False)
    assert project_cli.cmd_find_by_pr(args) == project_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == VALID_ITEM


def test_cmd_export_ssot_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ssot = {**_ssot(), "enabled": False}
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    assert (
        project_cli.cmd_export(
            argparse.Namespace(
                directory=tmp_path, output=None, limit=10, json=False, stdout=True
            )
        )
        == project_cli.EXIT_USAGE
    )


def test_cmd_set_field_estimate_queues_on_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    ssot["fields"]["estimate"] = {"field_id": "PVTF_estimate"}
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "set_item_number",
        lambda *a, **k: (False, "API rate limit exceeded"),
    )
    monkeypatch.setattr(
        project_cli,
        "_try_queue_rate_limit",
        lambda *a, **k: project_cli.EXIT_QUEUED,
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        field="estimate",
        to="3",
        agent="implementer",
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_QUEUED


def test_cmd_set_field_priority_queues_on_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _patch_ssot(monkeypatch)
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="API rate limit exceeded"),
    )
    monkeypatch.setattr(
        project_cli,
        "_try_queue_rate_limit",
        lambda *a, **k: project_cli.EXIT_QUEUED,
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        field="priority",
        to="p1",
        agent="implementer",
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_QUEUED


def test_cmd_set_field_estimate_fails_without_queue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _ssot()
    ssot["fields"]["estimate"] = {"field_id": "PVTF_estimate"}
    monkeypatch.setattr(project_cli, "_load_enabled_ssot", lambda root, cmd: (ssot, []))
    monkeypatch.setattr(
        project_cli,
        "set_item_number",
        lambda *a, **k: (False, "estimate edit failed"),
    )
    monkeypatch.setattr(project_cli, "_try_queue_rate_limit", lambda *a, **k: None)
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM,
        last=False,
        field="estimate",
        to="3",
        agent="implementer",
    )
    assert project_cli.cmd_set_field(args) == project_cli.EXIT_GH
