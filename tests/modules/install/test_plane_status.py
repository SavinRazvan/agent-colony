"""
File: test_plane_status.py
Path: tests/modules/install/test_plane_status.py
Role: Tests for three-plane readiness assessment.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/plane_status.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLANE_STATUS_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "plane_status.py"


def _load_plane_status():
    spec = importlib.util.spec_from_file_location("plane_status", PLANE_STATUS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["plane_status"] = module
    spec.loader.exec_module(module)
    return module


def test_kit_repo_planes_ready() -> None:
    plane_status = _load_plane_status()
    status = plane_status.assess_planes(REPO_ROOT, profile="with_mcp")
    assert status.all_ready
    assert not status.missing


def test_empty_dir_planes_missing(tmp_path: Path) -> None:
    plane_status = _load_plane_status()
    status = plane_status.assess_planes(tmp_path)
    assert not status.all_ready
    assert not status.cursor_contract
    assert not status.infrastructure
    assert not status.runtime
