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


def test_deepwiki_exemplar_has_no_secrets_checklist() -> None:
    """DeepWiki is the kit's zero-auth worked example — must stay auth-free in the exemplar."""
    path = REPO_ROOT / ".ai_infra" / "templates" / "user-settings" / "exemplars" / "mcp.agents.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    servers = {s["id"]: s for s in data.get("external_servers", []) if isinstance(s, dict)}
    assert "deepwiki" in servers
    deepwiki = servers["deepwiki"]
    assert deepwiki.get("enabled") is True
    assert deepwiki.get("secrets_checklist") == []
    assert deepwiki.get("transport", {}).get("url") == "https://mcp.deepwiki.com/mcp"
