"""
File: test_local_workflow_paths.py
Path: tests/modules/pr_workflow/test_local_workflow_paths.py
Role: Tests for canonical workflow-artifacts path SSOT.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/local_workflow_paths.py
Notes:
 - Uses temporary directories; does not modify kit root.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PR_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


def _load_local_workflow_paths():
    if str(PR_DIR) not in sys.path:
        sys.path.insert(0, str(PR_DIR))
    spec = importlib.util.spec_from_file_location(
        "local_workflow_paths",
        PR_DIR / "local_workflow_paths.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ensure_workflow_artifacts_tree_creates_all_buckets(tmp_path: Path) -> None:
    mod = _load_local_workflow_paths()
    mod.ensure_workflow_artifacts_tree(root=tmp_path)
    for bucket in mod.WORKFLOW_ARTIFACT_BUCKETS:
        assert (tmp_path / bucket).is_dir(), f"missing bucket: {bucket}"


def test_workflow_artifact_buckets_count() -> None:
    mod = _load_local_workflow_paths()
    assert len(mod.WORKFLOW_ARTIFACT_BUCKETS) == 6
    assert len(mod.ARTIFACT_STUB_BUCKET_NAMES) == 6
    assert mod.ARTIFACT_STUB_BUCKET_NAMES == tuple(p.name for p in mod.WORKFLOW_ARTIFACT_BUCKETS)
