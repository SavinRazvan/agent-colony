"""
File: test_doc_facts_full.py
Path: tests/modules/architecture_scripts/test_doc_facts_full.py
Role: Full-branch coverage for doc_facts_checks.py and check_doc_facts.py beyond
      the happy-path tests in test_check_doc_facts.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/doc_facts_checks.py
 - .ai_infra/scripts/architecture/check_doc_facts.py
"""

from __future__ import annotations

import json
import runpy
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ARCH_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "architecture"
if str(ARCH_DIR) not in sys.path:
    sys.path.insert(0, str(ARCH_DIR))

import check_doc_facts as cdf  # noqa: E402
import doc_facts_checks as dfc  # noqa: E402


def _copy_minimal_kit(target: Path) -> None:
    for rel in (
        ".cursor/agents",
        ".cursor/rules",
        "README.md",
        "AGENTS.md",
        ".ai_infra/docs/architecture/workflow-architecture.md",
        ".ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md",
        ".ai_infra/docs/operations/gate-matrix.md",
        ".ai_infra/scripts/pr/prepare.py",
        ".ai_infra/templates/local-workspace/exemplars",
        ".ai_infra/bootstrap.py",
        ".ai_infra/paths.py",
    ):
        src = REPO_ROOT / rel
        dst = target / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# doc_facts_checks.py
# ---------------------------------------------------------------------------


def test_read_missing_file_returns_empty(tmp_path: Path) -> None:
    assert dfc._read(tmp_path / "missing.md") == ""


def test_list_agent_ids_missing_dir_returns_empty(tmp_path: Path) -> None:
    paths = dfc.doc_facts_paths(tmp_path)
    assert dfc.list_agent_ids(paths) == []


def test_list_rule_count_missing_dir_returns_zero(tmp_path: Path) -> None:
    paths = dfc.doc_facts_paths(tmp_path)
    assert dfc.list_rule_count(paths) == 0


def test_ast_gate_list_length_syntax_error_returns_none() -> None:
    assert dfc._ast_gate_list_length("def f(:\n", "GATES") is None


def test_ast_gate_list_length_non_literal_returns_none() -> None:
    text = "GATES = some_function_call()\n"
    assert dfc._ast_gate_list_length(text, "GATES") is None


def test_ast_gate_list_length_assign_not_list_returns_none() -> None:
    text = "GATES = 'not-a-list'\n"
    assert dfc._ast_gate_list_length(text, "GATES") is None


def test_ast_gate_list_length_name_not_found_returns_none() -> None:
    text = "OTHER = [1, 2, 3]\n"
    assert dfc._ast_gate_list_length(text, "GATES") is None


def test_load_prepare_gate_count_missing_file(tmp_path: Path) -> None:
    paths = dfc.doc_facts_paths(tmp_path)
    assert dfc._load_prepare_gate_count(paths) is None


def test_load_prepare_gate_count_fallback_to_gates_key(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    prepare = tmp_path / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    prepare.write_text("GATES = ['a', 'b', 'c']\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    assert dfc._load_prepare_gate_count(paths) == 3


def test_load_prepare_gate_count_unparseable_returns_none(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    prepare = tmp_path / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    prepare.write_text("SOMETHING_ELSE = 1\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    assert dfc._load_prepare_gate_count(paths) is None


def test_check_doc001_missing_agents_dir_fails(tmp_path: Path) -> None:
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc001_agent_roster(paths)
    assert not result.passed
    assert "missing .cursor/agents" in result.detail


def test_check_doc001_missing_doc_target_reports_file_missing(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    (tmp_path / "README.md").unlink()
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc001_agent_roster(paths)
    assert not result.passed
    assert "README.md: file missing" in result.detail


def test_check_doc001_reports_more_than_eight_missing(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    for name in ("README.md", "AGENTS.md"):
        (tmp_path / name).write_text("nothing here\n", encoding="utf-8")
    (
        tmp_path / ".ai_infra" / "docs" / "architecture" / "workflow-architecture.md"
    ).write_text("nothing here\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc001_agent_roster(paths)
    assert not result.passed
    assert "more" in result.detail


def test_check_doc002_missing_status_row_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    (tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md").write_text(
        "no agents row here\n", encoding="utf-8"
    )
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc002_status_agent_count(paths)
    assert not result.passed
    assert "missing Agents" in result.detail


def test_check_doc003_missing_exemplars_dir_passes(tmp_path: Path) -> None:
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc003_kit_exemplar_tokens(paths)
    assert result.passed
    assert "skipped" in result.detail


def test_check_doc004_missing_rules_dir_fails(tmp_path: Path) -> None:
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc004_rules_count(paths)
    assert not result.passed
    assert "missing .cursor/rules" in result.detail


def test_check_doc004_status_missing_row_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    (tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md").write_text(
        "no rules row\n", encoding="utf-8"
    )
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc004_rules_count(paths)
    assert not result.passed
    assert "Universal rules row" in result.detail


def test_check_doc004_readme_missing_count_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    actual = dfc.list_rule_count(dfc.doc_facts_paths(tmp_path))
    readme = tmp_path / "README.md"
    readme.write_text("no rule count mention here at all\n", encoding="utf-8")
    status = tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md"
    status.write_text(f"| Universal rules | {actual} |\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc004_rules_count(paths)
    assert not result.passed
    assert "README missing" in result.detail


def test_check_doc004_status_count_mismatch_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    actual = dfc.list_rule_count(dfc.doc_facts_paths(tmp_path))
    readme = tmp_path / "README.md"
    readme.write_text(f"{actual} universal rules ship in this kit\n", encoding="utf-8")
    status = tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md"
    status.write_text(f"| Universal rules | {actual + 1} |\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc004_rules_count(paths)
    assert not result.passed
    assert f"doc={actual + 1} actual={actual}" in result.detail


def test_check_doc005_unparseable_gates_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    prepare = tmp_path / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    prepare.write_text("SOMETHING = 1\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc005_prepare_gate_facts(paths)
    assert not result.passed
    assert "unable to parse GATES" in result.detail


def test_check_doc005_missing_docs_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    (tmp_path / "AGENTS.md").write_text("no gate hints\n", encoding="utf-8")
    (tmp_path / ".ai_infra" / "docs" / "operations" / "gate-matrix.md").write_text(
        "no gate mention\n", encoding="utf-8"
    )
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc005_prepare_gate_facts(paths)
    assert not result.passed
    assert "AGENTS.md missing gate count hint" in result.detail


def test_check_doc006_missing_test_count_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    status = tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md"
    status.write_text("no test count here\n", encoding="utf-8")
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc006_implementation_test_count(paths)
    assert not result.passed
    assert "missing **Tests:**" in result.detail


def test_check_doc006_mismatch_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _copy_minimal_kit(tmp_path)
    status = tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md"
    status.write_text("**Tests:** 1\n", encoding="utf-8")
    monkeypatch.setattr(dfc, "_collect_pytest_count", lambda _root: 578)
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc006_implementation_test_count(paths)
    assert not result.passed
    assert "doc=1 pytest=578" in result.detail


def test_check_doc006_passes_when_counts_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _copy_minimal_kit(tmp_path)
    status = tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md"
    status.write_text("**Tests:** 583\n", encoding="utf-8")
    monkeypatch.setattr(dfc, "_collect_pytest_count", lambda _root: 583)
    paths = dfc.doc_facts_paths(tmp_path)
    result = dfc.check_doc006_implementation_test_count(paths)
    assert result.passed
    assert "583" in result.detail


# ---------------------------------------------------------------------------
# check_doc_facts.py
# ---------------------------------------------------------------------------


def test_format_report_counts_all_severities() -> None:
    results = [
        dfc.CheckResult(check_id="X-P0", severity=dfc.Severity.P0, passed=False, detail="p0 fail"),
        dfc.CheckResult(check_id="X-P1", severity=dfc.Severity.P1, passed=False, detail="p1 fail"),
        dfc.CheckResult(check_id="X-P2", severity=dfc.Severity.P2, passed=False, detail="p2 fail"),
    ]
    report = cdf.format_report(results)
    assert "summary: p0_fail=1 p1_fail=1 p2_fail=1 total=3" in report


def test_main_text_output_pass(capsys: pytest.CaptureFixture[str]) -> None:
    code = cdf.main(["--directory", str(REPO_ROOT)])
    captured = capsys.readouterr()
    assert code == 0
    assert "summary:" in captured.out


def test_main_json_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    code = cdf.main(["--directory", str(REPO_ROOT), "--json"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert "results" in payload
    assert "exit_code" in payload


def test_main_writes_preflight_json(tmp_path: Path) -> None:
    out = tmp_path / "preflight" / "doc-facts.json"
    code = cdf.main(["--directory", str(REPO_ROOT), "--preflight-out", str(out)])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["command"] == "python -m cursor_workflow doc validate"
    assert "results" in payload


def test_main_fails_on_missing_agent(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("workflow-drift-guard", ""), encoding="utf-8"
    )
    code = cdf.main(["--directory", str(tmp_path)])
    assert code == 1


def test_main_guard_via_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["check_doc_facts.py", "--directory", str(REPO_ROOT)])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(ARCH_DIR / "check_doc_facts.py"), run_name="__main__")
    assert exc_info.value.code == 0
