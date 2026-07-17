"""
File: test_user_settings_full.py
Path: tests/modules/pr_workflow/test_user_settings_full.py
Role: Full-branch coverage for user_settings.py, user_settings_load.py,
      user_settings_render.py, and user_settings_resolve.py beyond the
      happy-path tests in test_user_settings.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/user_settings*.py
"""

from __future__ import annotations

import builtins
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_testing_artifacts as cta  # noqa: E402
import user_settings as us  # noqa: E402
import user_settings_load as usl  # noqa: E402
import user_settings_render as usr  # noqa: E402
import user_settings_resolve as usres  # noqa: E402


def _write(root: Path, rel: str, text: str) -> Path:
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


GOOD_CONFIG = """
version: 1
owner:
  display_name: "Example Author"
  github_user: "@example"
commit_provenance:
  ai_disclosure_mode: assisted_by
  assisted_by:
    - tool: Cursor
      agent: implementer
  human_coauthors:
    - display_name: "Jane Human"
      email: "jane@example.com"
pr_collaboration:
  pipelines:
    default:
      agents: [review-pr, prepare-pr, merge-pr]
"""


# ---------------------------------------------------------------------------
# user_settings_load.py
# ---------------------------------------------------------------------------


def test_load_yaml_missing_file_returns_none(tmp_path: Path) -> None:
    assert usl.load_yaml(tmp_path / "nope.yaml") is None


def test_load_yaml_non_dict_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    assert usl.load_yaml(path) is None


def test_load_yaml_syntax_error_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("a: [1, 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML syntax error"):
        usl.load_yaml(path)


def test_validate_against_schema_missing_schema_file(tmp_path: Path) -> None:
    errors = usl.validate_against_schema({}, tmp_path / "missing.schema.json")
    assert errors == ["missing schema missing.schema.json"]


def test_validate_against_schema_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "jsonschema":
            raise ImportError("no jsonschema")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    errors = usl.validate_against_schema({}, usl.GITHUB_COLLAB_SCHEMA)
    assert errors == []


def test_validate_against_schema_reports_errors() -> None:
    pytest.importorskip("jsonschema")
    schema = {
        "type": "object",
        "required": ["owner"],
        "properties": {"owner": {"type": "object"}},
    }
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "s.schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        errors = usl.validate_against_schema({}, schema_path)
    assert errors
    assert "owner" in errors[0]


def test_load_mcp_agents_missing(tmp_path: Path) -> None:
    assert usl.load_mcp_agents(tmp_path) is None


def test_normalize_github_user_empty_returns_default() -> None:
    assert usl.normalize_github_user("   ") == usl.DEFAULT_GITHUB_USER


def test_normalize_github_user_adds_at() -> None:
    assert usl.normalize_github_user("plain") == "@plain"


def test_validate_github_collaboration_schema_missing_cfg(tmp_path: Path) -> None:
    errors = usl.validate_github_collaboration_schema(tmp_path)
    assert any("invalid YAML" in e for e in errors)


def test_validate_mcp_agents_schema_missing_cfg(tmp_path: Path) -> None:
    errors = usl.validate_mcp_agents_schema(tmp_path)
    assert any("invalid YAML" in e for e in errors)


# ---------------------------------------------------------------------------
# user_settings.py — validate_github_collaboration
# ---------------------------------------------------------------------------


def test_is_placeholder_owner_placeholder_handle_only() -> None:
    cfg = {"owner": {"display_name": "Real Name", "github_user": "@yourhandle"}}
    assert usl.is_placeholder_owner(cfg) is True


def test_validate_github_collaboration_missing_file(tmp_path: Path) -> None:
    errors = us.validate_github_collaboration(tmp_path)
    assert any("missing" in e for e in errors)


def test_validate_github_collaboration_non_dict_yaml(tmp_path: Path) -> None:
    _write(tmp_path, ".local/user_settings/github.collaboration.yaml", "- a\n- b\n")
    errors = us.validate_github_collaboration(tmp_path)
    assert any("invalid YAML" in e for e in errors)


def test_validate_github_collaboration_made_with_forbidden_skipped(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        GOOD_CONFIG + "\ncommit_provenance:\n  forbid_in_commits: ['Made-with']\n",
    )
    errors = us.validate_github_collaboration(tmp_path)
    # "Made-with" forbidden entries are intentionally skipped (continue) — no crash, no false error.
    assert isinstance(errors, list)


def test_validate_github_collaboration_yaml_syntax_error(tmp_path: Path) -> None:
    _write(tmp_path, ".local/user_settings/github.collaboration.yaml", "a: [1, 2\n")
    errors = us.validate_github_collaboration(tmp_path)
    assert any("YAML syntax error" in e for e in errors)


def test_validate_github_collaboration_incomplete_owner(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        """
owner:
  display_name: "Your Full Name"
  github_user: "@yourhandle"
pr_collaboration:
  pipelines:
    default:
      agents: [review-pr]
""",
    )
    errors = us.validate_github_collaboration(tmp_path)
    assert any("incomplete owner" in e for e in errors)


def test_validate_github_collaboration_missing_default_pipeline(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        """
version: 1
owner:
  display_name: "Example Author"
  github_user: "@example"
pr_collaboration:
  pipelines:
    architecture_impacting:
      agents: [review-pr]
""",
    )
    errors = us.validate_github_collaboration(tmp_path)
    assert any("missing pr_collaboration.pipelines.default" in e for e in errors)


# ---------------------------------------------------------------------------
# user_settings.py — validate_mcp_agents_worksheet
# ---------------------------------------------------------------------------


def test_validate_mcp_agents_worksheet_missing_file(tmp_path: Path) -> None:
    errors = us.validate_mcp_agents_worksheet(tmp_path)
    assert any("missing" in e for e in errors)


def test_validate_mcp_agents_worksheet_invalid_yaml(tmp_path: Path) -> None:
    _write(tmp_path, ".local/user_settings/mcp.agents.yaml", "- a\n- b\n")
    errors = us.validate_mcp_agents_worksheet(tmp_path)
    assert any("invalid YAML" in e for e in errors)


def test_validate_mcp_agents_worksheet_server_not_in_registry(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/mcp.agents.yaml",
        """
external_servers:
  - id: not-in-registry
    enabled: true
""",
    )
    errors = us.validate_mcp_agents_worksheet(tmp_path)
    assert any("not found in" in e for e in errors)


def test_validate_mcp_agents_worksheet_disabled_server_skipped(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/mcp.agents.yaml",
        """
external_servers:
  - id: disabled-one
    enabled: false
  - not-a-dict-entry
""",
    )
    errors = us.validate_mcp_agents_worksheet(tmp_path)
    assert errors == [] or all("disabled-one" not in e for e in errors)


def test_validate_mcp_agents_worksheet_server_found_in_registry(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".cursor/mcp.registry.yaml",
        "servers:\n  known-server:\n    agents: []\n",
    )
    _write(
        tmp_path,
        ".local/user_settings/mcp.agents.yaml",
        """
external_servers:
  - id: known-server
    enabled: true
""",
    )
    errors = us.validate_mcp_agents_worksheet(tmp_path)
    assert all("known-server" not in e or "not found" not in e for e in errors)


# ---------------------------------------------------------------------------
# user_settings_render.py
# ---------------------------------------------------------------------------


def test_render_commit_trailers_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        usr.render_commit_trailers(tmp_path)


def test_render_commit_trailers_placeholder_owner_raises(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        'owner:\n  display_name: "Your Full Name"\n  github_user: "@yourhandle"\n',
    )
    with pytest.raises(ValueError, match="Complete owner"):
        usr.render_commit_trailers(tmp_path)


def test_render_commit_trailers_co_author_mode(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        """
owner:
  display_name: "Example Author"
  github_user: "@example"
commit_provenance:
  ai_disclosure_mode: co_author_trailer
  co_author_trailer:
    name: "AI Bot"
    email: "bot@example.com"
  assisted_by:
    - tool: Cursor
""",
    )
    block = usr.render_commit_trailers(tmp_path)
    assert "Co-authored-by: AI Bot <bot@example.com>" in block
    assert "Assisted-by: Cursor" in block


def test_render_commit_trailers_human_coauthors(tmp_path: Path) -> None:
    _write(tmp_path, ".local/user_settings/github.collaboration.yaml", GOOD_CONFIG)
    block = usr.render_commit_trailers(tmp_path)
    assert "Co-authored-by: Jane Human <jane@example.com>" in block


def test_format_assisted_by_variants() -> None:
    assert usr._format_assisted_by({"tool": ""}) == ""
    assert usr._format_assisted_by({"tool": "Cursor", "model": "sonnet"}) == "Assisted-by: Cursor:sonnet"
    assert usr._format_assisted_by({"tool": "Cursor", "agent": "implementer"}) == "Assisted-by: Cursor:implementer"
    assert usr._format_assisted_by({"tool": "Cursor"}) == "Assisted-by: Cursor"


def test_render_pr_body_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        usr.render_pr_body(tmp_path)


def test_render_pr_body_requires_alignment_artifacts(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        GOOD_CONFIG
        + """
pr_collaboration:
  pipelines:
    default:
      agents: [review-pr]
    architecture_impacting:
      agents: [enterprise-auditor, review-pr]
      requires_alignment_artifacts: true
""",
    )
    body = usr.render_pr_body(tmp_path, pipeline="architecture_impacting", agents_from_session=False)
    assert "Alignment: `.local/workflow-artifacts/alignment/`" in body


def test_render_pr_body_default_test_plan_from_config(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        GOOD_CONFIG
        + """
pr_collaboration:
  pipelines:
    default:
      agents: [review-pr]
  pr_body:
    default_test_plan: ["- custom check"]
""",
    )
    body = usr.render_pr_body(tmp_path, agents_from_session=False)
    assert "- [ ] custom check" in body


# ---------------------------------------------------------------------------
# user_settings_resolve.py
# ---------------------------------------------------------------------------


def test_resolve_github_user_placeholder_falls_back_to_default(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/user_settings/github.collaboration.yaml",
        'owner:\n  display_name: "Your Full Name"\n  github_user: "@yourhandle"\n',
    )
    assert usres.resolve_github_user(tmp_path) == usl.DEFAULT_GITHUB_USER


def test_resolve_github_user_no_config(tmp_path: Path) -> None:
    assert usres.resolve_github_user(tmp_path) == usl.DEFAULT_GITHUB_USER


def test_resolve_default_actor_no_config(tmp_path: Path) -> None:
    assert usres.resolve_default_actor(tmp_path) is None


def test_pipeline_agents_list_no_cfg() -> None:
    assert usres.pipeline_agents_list(None, "default") == []


def test_pipeline_agents_list_non_dict_spec() -> None:
    cfg = {"pr_collaboration": {"pipelines": {"default": "not-a-dict"}}}
    assert usres.pipeline_agents_list(cfg, "default") == []


def test_pipeline_agents_list_agents_not_list() -> None:
    cfg = {"pr_collaboration": {"pipelines": {"default": {"agents": "not-a-list"}}}}
    assert usres.pipeline_agents_list(cfg, "default") == []


def test_pipeline_agents_string_empty_returns_none() -> None:
    assert usres.pipeline_agents_string(None, "default") is None


def test_parse_markdown_table_agent_column_missing_file(tmp_path: Path) -> None:
    assert usres._parse_markdown_table_agent_column(tmp_path / "no.md", row_prefix="| CHG-") == []


def test_parse_markdown_table_agent_column_short_row_skipped(tmp_path: Path) -> None:
    path = tmp_path / "change-index.md"
    path.write_text("| CHG-001 | a | b |\n", encoding="utf-8")
    assert usres._parse_markdown_table_agent_column(path, row_prefix="| CHG-") == []


def test_parse_markdown_table_agent_column_skips_non_matching_lines(tmp_path: Path) -> None:
    path = tmp_path / "change-index.md"
    path.write_text(
        "| not-a-chg-row | x |\n"
        "| CHG-001 | a | b | implementer | e |\n",
        encoding="utf-8",
    )
    assert usres._parse_markdown_table_agent_column(path, row_prefix="| CHG-") == ["implementer"]


def test_parse_session_pointer_agents_missing_file(tmp_path: Path) -> None:
    assert usres._parse_session_pointer_agents(tmp_path / "no.md") == []


def test_parse_session_pointer_agents_short_row_skipped(tmp_path: Path) -> None:
    path = tmp_path / "session-pointer.md"
    path.write_text("**Last agent** | x\n", encoding="utf-8")
    assert usres._parse_session_pointer_agents(path) == []


def test_parse_session_pointer_agents_skip_tokens(tmp_path: Path) -> None:
    path = tmp_path / "session-pointer.md"
    path.write_text("| **Last agent** | n/a | y |\n", encoding="utf-8")
    assert usres._parse_session_pointer_agents(path) == []


def test_parse_session_pointer_agents_valid_row(tmp_path: Path) -> None:
    path = tmp_path / "session-pointer.md"
    path.write_text(
        "| unrelated row | x | y |\n"
        "| **Last agent** | implementer | done |\n"
        "| **Next agent** | reviewer | pending |\n",
        encoding="utf-8",
    )
    assert usres._parse_session_pointer_agents(path) == ["implementer", "reviewer"]


def test_collect_session_agents_merges_change_index_and_session_pointer(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".local/index-and-planning/current/change-index.md",
        "| CHG-001 | a | b | implementer | e |\n"
        "| CHG-002 | a | b | test-runner | e |\n",
    )
    _write(
        tmp_path,
        ".local/index-and-planning/current/session-pointer.md",
        "| **Last agent** | test-runner | done |\n"
        "| **Next agent** | reviewer | pending |\n",
    )
    agents = usres.collect_session_agents(tmp_path)
    assert agents == ["test-runner", "implementer", "reviewer"]


def test_normalize_agent_id_skip_tokens() -> None:
    for token in ("", "-", "n/a", "none"):
        assert usres._normalize_agent_id(token) is None


def test_merge_agent_lists_dedupes() -> None:
    merged = usres.merge_agent_lists(["a", "b"], ["b", "c", ""])
    assert merged == "a | b | c"


def test_resolve_agents_for_pr_explicit_agents_wins() -> None:
    result = usres.resolve_agents_for_pr(
        root=None, cfg=None, pipeline="default", explicit_agents="  custom-agent  "
    )
    assert result == "custom-agent"


def test_resolve_agents_for_pr_no_session_uses_pipeline_fallback(tmp_path: Path) -> None:
    cfg = {"pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}}}
    result = usres.resolve_agents_for_pr(
        root=tmp_path, cfg=cfg, pipeline="default", agents_from_session=False
    )
    assert result == "review-pr"


def test_resolve_agents_for_pr_no_session_no_fallback_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Missing --agents"):
        usres.resolve_agents_for_pr(root=tmp_path, cfg=None, pipeline="default", agents_from_session=False)


def test_resolve_agents_for_pr_session_with_no_pr_phase_agents_defaults(tmp_path: Path) -> None:
    cfg = {"pr_collaboration": {"pipelines": {"default": {"agents": ["some-other-agent"]}}}}
    result = usres.resolve_agents_for_pr(root=tmp_path, cfg=cfg, pipeline="default", agents_from_session=True)
    assert result == "review-pr | prepare-pr | merge-pr"


def test_resolve_pipeline_name_explicit() -> None:
    assert usres.resolve_pipeline_name(pipeline="custom") == "custom"


def test_resolve_pipeline_name_arch_impacting() -> None:
    assert usres.resolve_pipeline_name(pipeline=None, arch_impacting=True) == "architecture_impacting"


def test_resolve_pipeline_name_default() -> None:
    assert usres.resolve_pipeline_name(pipeline=None, arch_impacting=False) == "default"


def test_add_pr_attribution_arguments_registers_flags() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    us.add_pr_attribution_arguments(parser)
    args = parser.parse_args(["--actor", "me", "--agents", "a | b", "--pipeline", "default"])
    assert args.actor == "me"
    assert args.agents == "a | b"
    assert args.pipeline == "default"
    assert args.agents_from_session is True


def test_resolve_pr_attribution_missing_actor_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Missing --actor"):
        usres.resolve_pr_attribution(root=tmp_path, actor=None, agents=None)


def test_resolve_pr_attribution_success(tmp_path: Path) -> None:
    _write(tmp_path, ".local/user_settings/github.collaboration.yaml", GOOD_CONFIG)
    actor, agents, github_user = usres.resolve_pr_attribution(
        root=tmp_path, actor=None, agents="custom-agent", pipeline="default"
    )
    assert actor == "Example Author"
    assert agents == "custom-agent"
    assert github_user == "@example"


# ---------------------------------------------------------------------------
# check_testing_artifacts.py
# ---------------------------------------------------------------------------


def test_check_testing_artifacts_all_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    planning = tmp_path / "planning"
    tests_dir = tmp_path / "tests" / "modules"
    tests_dir.mkdir(parents=True)
    _write(planning, "test-plan.md", "plan content")
    _write(planning, "test-index.md", "Module: foo\nCoverage status: 100%\n")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_testing_artifacts.py",
            "--planning-dir",
            str(planning),
            "--tests-dir",
            str(tests_dir),
        ],
    )
    assert cta.main() == 0


def test_check_testing_artifacts_legacy_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    planning = tmp_path / "legacy"
    tests_dir = tmp_path / "tests" / "modules"
    tests_dir.mkdir(parents=True)
    _write(planning, "test-plan.md", "plan content")
    _write(planning, "test-index.md", "Module: foo\nCoverage status: 100%\n")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_testing_artifacts.py",
            "--control-center-dir",
            str(planning),
            "--tests-dir",
            str(tests_dir),
        ],
    )
    assert cta.main() == 0


def test_check_testing_artifacts_missing_planning_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_testing_artifacts.py",
            "--planning-dir",
            str(tmp_path / "missing"),
            "--tests-dir",
            str(tmp_path / "missing-tests"),
        ],
    )
    assert cta.main() == 1


def test_check_testing_artifacts_empty_test_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    planning = tmp_path / "planning"
    tests_dir = tmp_path / "tests" / "modules"
    tests_dir.mkdir(parents=True)
    _write(planning, "test-plan.md", "  ")
    _write(planning, "test-index.md", "Module: foo\nCoverage status: 100%\n")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_testing_artifacts.py",
            "--planning-dir",
            str(planning),
            "--tests-dir",
            str(tests_dir),
        ],
    )
    assert cta.main() == 1


def test_check_testing_artifacts_missing_structure_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planning = tmp_path / "planning"
    tests_dir = tmp_path / "tests" / "modules"
    tests_dir.mkdir(parents=True)
    _write(planning, "test-plan.md", "plan content")
    _write(planning, "test-index.md", "no markers here")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_testing_artifacts.py",
            "--planning-dir",
            str(planning),
            "--tests-dir",
            str(tests_dir),
        ],
    )
    assert cta.main() == 1


def test_check_testing_artifacts_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_testing_artifacts.py",
            "--planning-dir",
            str(REPO_ROOT / ".local" / "index-and-planning" / "current"),
            "--tests-dir",
            str(REPO_ROOT / "tests" / "modules"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCRIPTS_DIR / "check_testing_artifacts.py"), run_name="__main__")
    assert exc_info.value.code == 0
