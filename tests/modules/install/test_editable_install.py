"""
File: test_editable_install.py
Path: tests/modules/install/test_editable_install.py
Role: Smoke tests that kit packages import after editable install.
Used By:
 - pytest
Depends On:
 - agent_colony package
 - workflow_mcp package
Notes:
 - CI runs pip install -e ".[dev,mcp]" before pytest.
"""

from __future__ import annotations


def test_import_agent_colony_package() -> None:
    import agent_colony

    assert agent_colony.__version__ == "0.6.0"


def test_import_workflow_mcp_package() -> None:
    import workflow_mcp

    assert workflow_mcp.__name__ == "workflow_mcp"
