"""
File: test_agent_mcp_blocks.py
Path: tests/modules/mcp_registry/test_agent_mcp_blocks.py
Role: All kit agents include standard MCP integration section.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/integration/checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CHECKS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "integration"
if str(CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECKS_DIR))

from checks import check_all_agent_files

AGENTS_DIR = REPO_ROOT / ".cursor" / "agents"


def test_all_agents_have_mcp_integration_block() -> None:
    violations = check_all_agent_files(AGENTS_DIR)
    assert not violations, "\n".join(violations)
