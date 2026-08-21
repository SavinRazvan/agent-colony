"""
File: test_prepare_summary.py
Path: tests/modules/scripts/test_prepare_summary.py
Role: Tests prepare.py --summary output path with --skip-gates.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/prepare.py
Notes:
 - Uses --skip-gates to avoid running full gate suite.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PREPARE_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "prepare.py"


def _load_prepare():
    spec = importlib.util.spec_from_file_location("prepare_mod", PREPARE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["prepare_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_prepare_summary_skip_gates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prepare = _load_prepare()
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".local" / "workflow-artifacts" / "pr").mkdir(parents=True)
    monkeypatch.setattr(prepare, "ensure_workflow_artifacts_dir", lambda: None)
    monkeypatch.setattr(
        prepare,
        "PREP_MD",
        tmp_path / ".local" / "workflow-artifacts" / "pr" / "prep.md",
    )
    monkeypatch.setattr(
        prepare,
        "resolve_pr_attribution",
        lambda **kwargs: ("Test User", "implementer", "@test"),
    )
    monkeypatch.setattr(prepare, "_current_branch", lambda: "feature/x")
    monkeypatch.setattr(prepare, "_head_sha", lambda: "abc123")
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare.py", "--pr", "1", "--skip-gates", "--summary", "--actor", "Test User"],
    )
    assert prepare.main() == 0
    out = capsys.readouterr().out
    assert "prepare: PASS" in out
    assert "externally verified" in out
    assert prepare.PREP_MD.is_file()
