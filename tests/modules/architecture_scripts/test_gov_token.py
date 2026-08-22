"""
File: test_gov_token.py
Path: tests/modules/architecture_scripts/test_gov_token.py
Role: Fixtures for GOV-TOKEN-001/002 governance checks.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_governance_consistency.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_governance_consistency.py"


def _load_gov_module():
    spec = importlib.util.spec_from_file_location("check_governance_consistency", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_governance_consistency"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_gov_token_001_detects_missing_anchor(tmp_path: Path, monkeypatch) -> None:
    mod = _load_gov_module()
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    (agents / "implementer.md").write_text("# implementer\n", encoding="utf-8")
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    violations = mod._collect_gov_token_001_violations()
    assert any("GOV-TOKEN-001" in v and "implementer" in v for v in violations)


def test_gov_token_002_detects_gate_duplication(tmp_path: Path, monkeypatch) -> None:
    mod = _load_gov_module()
    skill = tmp_path / ".cursor" / "skills" / "bad-skill"
    skill.mkdir(parents=True)
    header = "\n".join(f"# line {i}" for i in range(21))
    (skill / "SKILL.md").write_text(
        f"{header}\nRun check_testing_artifacts.py before merge.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    violations = mod._collect_gov_token_002_violations()
    assert any("GOV-TOKEN-002" in v for v in violations)
