"""
File: test_resources_full.py
Path: tests/modules/workflow_mcp/test_resources_full.py
Role: Full-branch coverage for workflow_mcp/resources.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/mcp_servers/workflow_mcp/resources.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_mcp import resources


def test_read_pr_artifact_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resources.read_pr_artifact(tmp_path, "review")


def test_read_tracker_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resources.read_tracker(tmp_path, "plan")


def test_list_agent_ids_no_dir(tmp_path: Path) -> None:
    assert resources._list_agent_ids(tmp_path) == []


def test_list_skill_ids_no_dirs(tmp_path: Path) -> None:
    assert resources._list_skill_ids(tmp_path) == []


def test_read_project_config_not_found(tmp_path: Path) -> None:
    text = resources.read_project_config(tmp_path)
    assert "not found" in text


def test_load_registry_yaml_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="mcp.registry.yaml not found"):
        resources._load_registry_yaml(tmp_path)


def test_read_mcp_connection_guide_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resources.read_mcp_connection_guide(tmp_path)
