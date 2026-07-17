"""
File: test_check_doc_facts.py
Path: tests/modules/architecture_scripts/test_check_doc_facts.py
Role: Tests for canonical doc fact validation (DOC-001…006).
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_doc_facts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ARCH_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "architecture"
if str(ARCH_DIR) not in sys.path:
    sys.path.insert(0, str(ARCH_DIR))

from check_doc_facts import exit_code_for, run_checks  # noqa: E402


def test_doc_facts_passes_on_kit_repo() -> None:
    results = run_checks(REPO_ROOT)
    failures = [r for r in results if not r.passed and r.severity.value in ("P0", "P1")]
    assert not failures, "\n".join(f"{r.check_id}: {r.detail}" for r in failures)
    assert exit_code_for(results) == 0


def test_missing_agent_in_readme_fails(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace("workflow-drift-guard", ""), encoding="utf-8")
    results = run_checks(tmp_path)
    doc001 = next(r for r in results if r.check_id == "DOC-001")
    assert not doc001.passed
    assert exit_code_for(results) == 1


def test_starter_token_in_exemplar_fails_p0(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    exemplar = tmp_path / ".ai_infra" / "templates" / "local-workspace" / "exemplars" / "plan.md"
    exemplar.write_text(exemplar.read_text(encoding="utf-8") + "\nSTARTER-001\n", encoding="utf-8")
    results = run_checks(tmp_path)
    doc003 = next(r for r in results if r.check_id == "DOC-003")
    assert not doc003.passed
    assert doc003.severity.value == "P0"
    assert exit_code_for(results) == 1


def test_consumer_profile_skips_doc_facts(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    (tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md").unlink()
    results = run_checks(tmp_path)
    assert len(results) == 1
    assert results[0].check_id == "DOC-000"
    assert results[0].passed
    assert exit_code_for(results) == 0


def _copy_minimal_kit(target: Path) -> None:
    import shutil

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
