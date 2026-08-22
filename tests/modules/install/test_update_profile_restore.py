"""
File: test_update_profile_restore.py
Path: tests/modules/install/test_update_profile_restore.py
Role: Lite → full profile restore via scaffold re-run (update --force --profile with_mcp).
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/scaffold.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLD = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"
if str(SCAFFOLD.parent) not in sys.path:
    sys.path.insert(0, str(SCAFFOLD.parent))

import scaffold  # noqa: E402


def test_lite_to_full_profile_restores_eight_agents(tmp_path: Path) -> None:
    target = tmp_path / "app"
    scaffold.scaffold(
        target,
        REPO_ROOT,
        profile="consumer_lite",
        dry_run=False,
        with_venv=False,
        with_mcp_json=False,
        verify=False,
    )
    lite_agents = {p.stem for p in (target / ".cursor" / "agents").glob("*.md")}
    assert len(lite_agents) == 6
    assert "auditor" not in lite_agents

    scaffold.scaffold(
        target,
        REPO_ROOT,
        profile="with_mcp",
        dry_run=False,
        with_venv=False,
        with_mcp_json=False,
        verify=False,
    )
    full_agents = {p.stem for p in (target / ".cursor" / "agents").glob("*.md")}
    assert len(full_agents) == 8
    assert "auditor" in full_agents
    assert "researcher" in full_agents
    marker = target / ".local" / "generated-data" / "install-profile.json"
    assert marker.is_file()
    assert '"profile": "with_mcp"' in marker.read_text(encoding="utf-8")
