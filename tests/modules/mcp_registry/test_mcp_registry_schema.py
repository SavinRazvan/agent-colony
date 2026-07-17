"""
File: test_mcp_registry_schema.py
Path: tests/modules/mcp_registry/test_mcp_registry_schema.py
Role: Validate example MCP registry against JSON schema.
Used By:
 - pytest
Depends On:
 - .ai_infra/schemas/mcp-registry.schema.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_example_registry_validates_against_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (REPO_ROOT / ".ai_infra" / "schemas" / "mcp-registry.schema.json").read_text(encoding="utf-8")
    )
    example_path = REPO_ROOT / ".cursor" / "mcp.registry.yaml.example"
    data = yaml.safe_load(example_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
