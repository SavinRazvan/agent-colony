"""
File: test_local_workflow_paths_archive.py
Path: tests/modules/pr_workflow/test_local_workflow_paths_archive.py
Role: Cover archive_then_write Pattern A tip archival.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/local_workflow_paths.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


def _load():
    spec = importlib.util.spec_from_file_location(
        "local_workflow_paths_mod", SCRIPTS_DIR / "local_workflow_paths.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_archive_then_write_copies_prior_tip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load()
    monkeypatch.chdir(tmp_path)
    tip = tmp_path / ".local" / "workflow-artifacts" / "pr" / "prep.md"
    tip.parent.mkdir(parents=True)
    tip.write_text("first\n", encoding="utf-8")

    archived = mod.archive_then_write(tip, "second\n", pr="270", phase="prep")
    assert tip.read_text(encoding="utf-8") == "second\n"
    assert archived is not None
    assert archived.is_file()
    assert archived.read_text(encoding="utf-8") == "first\n"
    assert "pr-270-prep-" in archived.name
    assert archived.resolve().parent == (
        tmp_path / ".local" / "workflow-artifacts" / "pr" / "archive"
    ).resolve()


def test_archive_then_write_no_prior(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load()
    monkeypatch.chdir(tmp_path)
    tip = tmp_path / ".local" / "workflow-artifacts" / "pr" / "review.md"
    archived = mod.archive_then_write(tip, "only\n", pr="1", phase="review")
    assert archived is None
    assert tip.read_text(encoding="utf-8") == "only\n"
