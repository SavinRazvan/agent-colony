"""
File: test_user_settings.py
Path: tests/modules/pr_workflow/test_user_settings.py
Role: Tests user_settings loader and PR attribution resolution.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/user_settings.py
Notes:
 - Uses temporary github.collaboration.yaml under .local/user_settings/.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


def _load_user_settings():
    pr_str = str(SCRIPTS_DIR)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    spec = importlib.util.spec_from_file_location("user_settings", SCRIPTS_DIR / "user_settings.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_github_config(root: Path, text: str) -> None:
    dest = root / ".local" / "user_settings" / "github.collaboration.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


SAMPLE_CONFIG = """
version: 1
owner:
  display_name: "Example Author"
  github_user: "@example"
commit_provenance:
  ai_disclosure_mode: assisted_by
  assisted_by:
    - tool: Cursor
      agent: implementer
pr_collaboration:
  pipelines:
    default:
      agents: [review-pr, prepare-pr, merge-pr]
    architecture_impacting:
      agents: [enterprise-auditor, review-pr, prepare-pr, merge-pr]
      requires_alignment_artifacts: true
"""


def test_resolve_github_user_from_config(tmp_path: Path) -> None:
    us = _load_user_settings()
    _write_github_config(tmp_path, SAMPLE_CONFIG)
    assert us.resolve_github_user(tmp_path) == "@example"
    assert us.resolve_default_actor(tmp_path) == "Example Author"


def test_render_commit_trailers(tmp_path: Path) -> None:
    us = _load_user_settings()
    _write_github_config(tmp_path, SAMPLE_CONFIG)
    block = us.render_commit_trailers(tmp_path)
    assert "Author: Example Author" in block
    assert "GitHub-User: @example" in block
    assert "Assisted-by: Cursor:implementer" in block


def test_resolve_pr_attribution_from_pipeline(tmp_path: Path) -> None:
    us = _load_user_settings()
    _write_github_config(tmp_path, SAMPLE_CONFIG)
    actor, agents, handle = us.resolve_pr_attribution(
        root=tmp_path,
        actor=None,
        agents=None,
        pipeline="architecture_impacting",
    )
    assert actor == "Example Author"
    assert "enterprise-auditor" in agents
    assert handle == "@example"


def test_merge_session_and_pipeline_agents(tmp_path: Path) -> None:
    us = _load_user_settings()
    _write_github_config(tmp_path, SAMPLE_CONFIG)

    change_index = tmp_path / ".local" / "index-and-planning" / "current" / "change-index.md"
    change_index.parent.mkdir(parents=True, exist_ok=True)
    change_index.write_text(
        """# Change index

| ID | Area | Paths | Agent | Gates / checks | Status |
|----|------|-------|-------|----------------|--------|
| CHG-002 | tests | tests/ | test-runner | pytest | done |
| CHG-001 | impl | src/ | implementer | gates | done |
""",
        encoding="utf-8",
    )

    cfg = us.load_github_collaboration(tmp_path)
    merged = us.resolve_agents_for_pr(
        root=tmp_path,
        cfg=cfg,
        pipeline="default",
        agents_from_session=True,
    )
    assert merged == "implementer | test-runner | review-pr | prepare-pr | merge-pr"


def test_explicit_agents_skips_session_merge(tmp_path: Path) -> None:
    us = _load_user_settings()
    _write_github_config(tmp_path, SAMPLE_CONFIG)
    change_index = tmp_path / ".local" / "index-and-planning" / "current" / "change-index.md"
    change_index.parent.mkdir(parents=True, exist_ok=True)
    change_index.write_text(
        "| ID | Area | Paths | Agent | Gates | Status |\n"
        "| CHG-001 | x | y | implementer | z | done |\n",
        encoding="utf-8",
    )
    cfg = us.load_github_collaboration(tmp_path)
    merged = us.resolve_agents_for_pr(
        root=tmp_path,
        cfg=cfg,
        pipeline="default",
        explicit_agents="review-pr only",
        agents_from_session=True,
    )
    assert merged == "review-pr only"


def test_review_script_uses_user_settings(tmp_path: Path, monkeypatch) -> None:
    us = _load_user_settings()
    _write_github_config(tmp_path, SAMPLE_CONFIG)

    pr_str = str(SCRIPTS_DIR)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    spec = importlib.util.spec_from_file_location("review_script", SCRIPTS_DIR / "review.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["review.py", "--pr", "123", "--pipeline", "default"])
    assert module.main() == 0

    content = (tmp_path / ".local" / "workflow-artifacts" / "pr" / "review.md").read_text(
        encoding="utf-8"
    )
    assert "Action-By: Example Author" in content
    assert "GitHub-User: @example" in content
    assert "Agent/s: review-pr | prepare-pr | merge-pr" in content


def test_validate_flags_placeholder_owner(tmp_path: Path) -> None:
    us = _load_user_settings()
    _write_github_config(
        tmp_path,
        """
version: 1
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
    assert any("incomplete owner" in err for err in errors)


def test_validate_github_collaboration_reports_yaml_syntax_error(tmp_path: Path) -> None:
    us = _load_user_settings()
    dest = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "version: 1\nowner:\n  display_name: Test\n  github_user: '@t'\n"
        "commit_provenance:\n  human_coauthors: []\n"
        "  - display_name: Broken\n",
        encoding="utf-8",
    )
    errors = us.validate_github_collaboration(tmp_path)
    assert len(errors) == 1
    assert "YAML syntax error" in errors[0]
