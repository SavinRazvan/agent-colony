"""
File: test_validate_full.py
Path: tests/modules/integration/test_validate_full.py
Role: Full-branch coverage for validate.py (integrate validate) beyond the
      happy-path tests in test_integrate_validate.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/integration/validate.py
"""

from __future__ import annotations

import json
import runpy
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "integration"
if str(INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_DIR))

import validate  # noqa: E402


def _copy_minimal_kit(target: Path) -> None:
    for rel in (
        ".cursor/agents",
        ".cursor/rules",
        ".cursor/skills/implementation-execution-loop",
        ".cursor/mcp.registry.yaml.example",
        ".ai_infra/scripts/pr",
        ".ai_infra/scripts/integration",
        ".ai_infra/scripts/workflow",
        ".ai_infra/scripts/architecture",
        ".ai_infra/schemas",
        ".ai_infra/templates/user-settings/exemplars",
        ".ai_infra/templates/agent-integration",
        ".ai_infra/docs/operations/mas-infrastructure-integration.md",
        ".ai_infra/manifest.yaml",
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

    settings_dir = target / ".local" / "user_settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / ".ai_infra/templates/user-settings/exemplars/github.collaboration.yaml",
        settings_dir / "github.collaboration.yaml",
    )
    content = (settings_dir / "github.collaboration.yaml").read_text(encoding="utf-8")
    content = content.replace("Your Full Name", "Test User").replace("@yourhandle", "@testuser")
    (settings_dir / "github.collaboration.yaml").write_text(content, encoding="utf-8")


def test_check_int004_reports_both_missing_directions(tmp_path: Path) -> None:
    us_module = SimpleNamespace(PIPELINE_NAMES=("default", "code-only-pipeline"))
    exemplar = tmp_path / "github.collaboration.yaml"
    exemplar.write_text(
        "pr_collaboration:\n"
        "  pipelines:\n"
        "    default: {}\n"
        "    exemplar-only-pipeline: {}\n",
        encoding="utf-8",
    )
    paths = {"github_exemplar": exemplar}
    result = validate._check_int004(us_module, paths)
    assert not result.passed
    assert "PIPELINE_NAMES not in exemplar" in result.detail
    assert "exemplar pipelines not in PIPELINE_NAMES" in result.detail


def test_check_int005_skips_when_no_local_config(tmp_path: Path) -> None:
    us_module = SimpleNamespace(load_github_collaboration=lambda root: None)
    result = validate._check_int005(us_module, tmp_path, {"agents_dir": tmp_path})
    assert result.passed
    assert "skipped" in result.detail


def test_check_int006_skips_when_no_local_config(tmp_path: Path) -> None:
    us_module = SimpleNamespace(
        github_collaboration_path=lambda root: tmp_path / "missing.yaml"
    )
    result = validate._check_int006(us_module, tmp_path)
    assert result.passed
    assert "skipped" in result.detail


def test_check_int008_missing_manifest(tmp_path: Path) -> None:
    result = validate._check_int008({"manifest": tmp_path / "no-manifest.yaml"})
    assert not result.passed
    assert "missing manifest.yaml" in result.detail


def test_check_int008_missing_agent_integration_and_cursor(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "profiles:\n"
        "  default:\n"
        "    copy_ai_infra: []\n"
        "    copy_dirs: []\n",
        encoding="utf-8",
    )
    result = validate._check_int008({"manifest": manifest})
    assert not result.passed
    assert "templates/agent-integration" in result.detail
    assert ".cursor in copy_dirs" in result.detail


def test_check_int011_missing_agent_source(tmp_path: Path) -> None:
    paths = {
        "agents_dir": tmp_path / "agents",
        "plugin_drift_guard": tmp_path / "plugin-drift-guard.md",
    }
    result = validate._check_int011(tmp_path, paths)
    assert not result.passed
    assert "missing .cursor/agents/workflow-drift-guard.md" in result.detail


def test_check_int012_import_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workflow_dir = tmp_path / ".ai_infra" / "scripts" / "workflow"
    workflow_dir.mkdir(parents=True)

    def _raise(_root: Path):
        raise ImportError("boom")

    monkeypatch.setattr(validate, "_import_check_drift", _raise)
    result = validate._check_int012(tmp_path)
    assert not result.passed
    assert "check_drift import failed" in result.detail


def test_check_int013_consumer_profile_skip(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    result = validate._check_int013(tmp_path)
    assert result.passed
    assert "consumer profile" in result.detail


def test_check_int014_missing_alwaysapply_and_missing_references(tmp_path: Path) -> None:
    rules = tmp_path / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "file-docstring-header-relations.mdc").write_text(
        "no alwaysApply directive here\n", encoding="utf-8"
    )
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    (agents / "implementer.md").write_text("no header rule mention\n", encoding="utf-8")
    skills = tmp_path / ".cursor" / "skills" / "implementation-execution-loop"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("no header rule mention\n", encoding="utf-8")

    result = validate._check_int014(tmp_path)
    assert not result.passed
    assert "missing alwaysApply: true" in result.detail
    assert "implementer.md missing file-docstring-header-relations reference" in result.detail
    assert "implementation-execution-loop/SKILL.md missing file-docstring-header reference" in result.detail


def test_format_report_counts_all_severities() -> None:
    results = [
        validate.CheckResult(check_id="X-P0", severity=validate.Severity.P0, passed=False, detail="p0"),
        validate.CheckResult(check_id="X-P1", severity=validate.Severity.P1, passed=False, detail="p1"),
        validate.CheckResult(check_id="X-P2", severity=validate.Severity.P2, passed=False, detail="p2"),
    ]
    report = validate.format_report(results)
    assert "summary: p0_fail=1 p1_fail=1 p2_fail=1 total=3" in report


def test_main_text_output(capsys: pytest.CaptureFixture[str]) -> None:
    code = validate.main(["--directory", str(REPO_ROOT)])
    captured = capsys.readouterr()
    assert code == 0
    assert "summary:" in captured.out


def test_main_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    code = validate.main(["--directory", str(REPO_ROOT), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["exit_code"] == code
    assert "results" in payload


def test_main_guard_via_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["validate.py", "--directory", str(REPO_ROOT)])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(INTEGRATION_DIR / "validate.py"), run_name="__main__")
    assert exc_info.value.code == 0
