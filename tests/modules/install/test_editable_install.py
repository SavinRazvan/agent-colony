"""
File: test_editable_install.py
Path: tests/modules/install/test_editable_install.py
Role: Smoke tests that kit packages import after editable install.
Used By:
 - pytest
Depends On:
 - agent_colony package
 - agent_colony_mcp package
Notes:
 - CI runs pip install -e ".[dev,mcp]" before pytest.
"""

from __future__ import annotations


def test_import_agent_colony_package() -> None:
    import agent_colony

    assert agent_colony.__version__ == "0.6.5"


def test_import_agent_colony_mcp_package() -> None:
    import agent_colony_mcp

    assert agent_colony_mcp.__name__ == "agent_colony_mcp"
