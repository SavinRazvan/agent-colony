"""
File: test_user_settings_schemas.py
Path: tests/modules/pr_workflow/test_user_settings_schemas.py
Role: Validate user_settings exemplars against JSON schemas.
Used By:
 - pytest
Depends On:
 - .ai_infra/schemas/*.schema.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("exemplar_rel", "schema_name"),
    [
        (
            ".ai_infra/templates/user-settings/exemplars/github.collaboration.yaml",
            "github-collaboration.schema.json",
        ),
        (
            ".ai_infra/templates/user-settings/exemplars/mcp.agents.yaml",
            "mcp-agents.schema.json",
        ),
    ],
)
def test_exemplar_validates_against_schema(exemplar_rel: str, schema_name: str) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (REPO_ROOT / ".ai_infra" / "schemas" / schema_name).read_text(encoding="utf-8")
    )
    data = yaml.safe_load((REPO_ROOT / exemplar_rel).read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
