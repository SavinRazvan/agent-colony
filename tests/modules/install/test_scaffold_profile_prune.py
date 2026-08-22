"""
File: test_scaffold_profile_prune.py
Path: tests/modules/install/test_scaffold_profile_prune.py
Role: Tests consumer_lite profile prune and install-profile marker.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/scaffold.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLD = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"
if str(SCAFFOLD.parent) not in sys.path:
    sys.path.insert(0, str(SCAFFOLD.parent))

import scaffold  # noqa: E402


def test_consumer_lite_prune_and_marker(tmp_path: Path) -> None:
    scaffold.scaffold(
        tmp_path,
        REPO_ROOT,
        profile="consumer_lite",
        dry_run=False,
        with_venv=False,
        with_mcp_json=False,
        verify=False,
    )
    skills = {p.name for p in (tmp_path / ".cursor" / "skills").iterdir() if p.is_dir()}
    assert skills == {
        "board-ssot",
        "implementer-loop",
        "evidence-first",
        "test-coverage",
        "workflow-activate",
        "mcp-connect",
    }
    agents = {p.stem for p in (tmp_path / ".cursor" / "agents").glob("*.md")}
    assert "auditor" not in agents
    assert "researcher" not in agents
    assert len(agents) == 6
    marker = tmp_path / ".local" / "generated-data" / "install-profile.json"
    assert marker.is_file()
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["profile"] == "consumer_lite"
    assert data["kit_version"] == "0.7.0"
