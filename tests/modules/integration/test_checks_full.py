"""
File: test_checks_full.py
Path: tests/modules/integration/test_checks_full.py
Role: Unit tests for shared integration parity check helpers in checks.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/integration/checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "integration"
if str(INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_DIR))

import checks  # noqa: E402


def test_agent_file_ids_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert checks.agent_file_ids(tmp_path / "no-agents") == set()


def test_registry_agent_ids_missing_file_returns_empty(tmp_path: Path) -> None:
    assert checks.registry_agent_ids(tmp_path / "no-registry.yaml") == set()


def test_registry_agent_ids_non_dict_yaml_returns_empty(tmp_path: Path) -> None:
    registry = tmp_path / "registry.yaml"
    registry.write_text("- a\n- b\n", encoding="utf-8")
    assert checks.registry_agent_ids(registry) == set()


def test_registry_agent_ids_skips_non_dict_specs_and_non_str_agents(tmp_path: Path) -> None:
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        "servers:\n"
        "  bad-spec: not-a-dict\n"
        "  good-spec:\n"
        "    agents: [123, '', 'valid-agent']\n",
        encoding="utf-8",
    )
    assert checks.registry_agent_ids(registry) == {"valid-agent"}


def test_check_all_agent_files_missing_dir_reports_violation(tmp_path: Path) -> None:
    violations = checks.check_all_agent_files(tmp_path / "no-agents")
    assert len(violations) == 1
    assert "no agent files in" in violations[0]


def test_pipeline_names_from_exemplar_missing_file_returns_empty(tmp_path: Path) -> None:
    assert checks.pipeline_names_from_exemplar(tmp_path / "no.yaml") == set()


def test_pipeline_names_from_exemplar_non_dict_yaml_returns_empty(tmp_path: Path) -> None:
    exemplar = tmp_path / "exemplar.yaml"
    exemplar.write_text("- a\n- b\n", encoding="utf-8")
    assert checks.pipeline_names_from_exemplar(exemplar) == set()


def test_pipeline_names_from_exemplar_non_dict_pipelines_returns_empty(tmp_path: Path) -> None:
    exemplar = tmp_path / "exemplar.yaml"
    exemplar.write_text("pr_collaboration:\n  pipelines: not-a-dict\n", encoding="utf-8")
    assert checks.pipeline_names_from_exemplar(exemplar) == set()


def test_check_pipeline_agent_ids_non_dict_pipelines_returns_empty() -> None:
    cfg = {"pr_collaboration": {"pipelines": "not-a-dict"}}
    assert checks.check_pipeline_agent_ids(cfg=cfg, agents_dir=Path("/nonexistent")) == []


def test_check_pipeline_agent_ids_skips_non_dict_spec_and_non_str_agent(tmp_path: Path) -> None:
    cfg = {
        "pr_collaboration": {
            "pipelines": {
                "weird": "not-a-dict",
                "default": {"agents": [123, "", "review-pr"]},
            }
        }
    }
    violations = checks.check_pipeline_agent_ids(cfg=cfg, agents_dir=tmp_path)
    assert violations == []


def test_check_pipeline_agent_ids_reports_unknown_agent(tmp_path: Path) -> None:
    cfg = {
        "pr_collaboration": {
            "pipelines": {"default": {"agents": ["unknown-agent-id"]}}
        }
    }
    violations = checks.check_pipeline_agent_ids(cfg=cfg, agents_dir=tmp_path)
    assert len(violations) == 1
    assert "unknown-agent-id" in violations[0]


def test_resolve_pipeline_agent_id_pr_alias_true(tmp_path: Path) -> None:
    assert checks.resolve_pipeline_agent_id("review-pr", agents_dir=tmp_path) is True


def test_resolve_pipeline_agent_id_file_exists(tmp_path: Path) -> None:
    (tmp_path / "implementer.md").write_text("x\n", encoding="utf-8")
    assert checks.resolve_pipeline_agent_id("implementer", agents_dir=tmp_path) is True


def test_resolve_pipeline_agent_id_missing_file(tmp_path: Path) -> None:
    assert checks.resolve_pipeline_agent_id("no-such-agent", agents_dir=tmp_path) is False
