"""
File: test_mcp_manage_full.py
Path: tests/modules/mcp_registry/test_mcp_manage_full.py
Role: Full-branch coverage for mcp_manage.py (merge, registry validate, link, gitignore).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/mcp_manage.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import mcp_manage  # noqa: E402


# ---------------------------------------------------------------------------
# _read_json / _strip_private_keys
# ---------------------------------------------------------------------------


def test_read_json_not_object_raises(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="expected JSON object"):
        mcp_manage._read_json(path)


def test_strip_private_keys_nested() -> None:
    obj = {"_secret": 1, "keep": {"_hidden": 2, "visible": 3}}
    cleaned = mcp_manage._strip_private_keys(obj)
    assert cleaned == {"keep": {"visible": 3}}


# ---------------------------------------------------------------------------
# merge_mcp_configs
# ---------------------------------------------------------------------------


def test_merge_kit_servers_not_dict_raises() -> None:
    with pytest.raises(ValueError, match="kit mcpServers must be an object"):
        mcp_manage.merge_mcp_configs({"mcpServers": []})


def test_merge_user_servers_not_dict_raises() -> None:
    with pytest.raises(ValueError, match="user mcpServers must be an object"):
        mcp_manage.merge_mcp_configs({"mcpServers": {}}, {"mcpServers": []})


def test_merge_user_private_key_skipped() -> None:
    kit = {"mcpServers": {"kit-server": {}}}
    user = {"mcpServers": {"_hidden": {}, "user-server": {}}}
    merged = mcp_manage.merge_mcp_configs(kit, user)
    assert "_hidden" not in merged["mcpServers"]
    assert "user-server" in merged["mcpServers"]


def test_merge_no_user() -> None:
    merged = mcp_manage.merge_mcp_configs({"mcpServers": {"a": {}}})
    assert merged == {"mcpServers": {"a": {}}}


# ---------------------------------------------------------------------------
# write_merged_mcp
# ---------------------------------------------------------------------------


def test_write_merged_mcp_missing_kit_fragment_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing kit MCP fragment"):
        mcp_manage.write_merged_mcp(tmp_path)


def test_write_merged_mcp_dry_run(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {"a": {}}}), encoding="utf-8")
    dest = mcp_manage.write_merged_mcp(tmp_path, dry_run=True)
    assert not dest.is_file()


def test_write_merged_mcp_with_user_fragment(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {"a": {}}}), encoding="utf-8")
    (cursor / "mcp.user.json").write_text(json.dumps({"mcpServers": {"b": {}}}), encoding="utf-8")
    dest = mcp_manage.write_merged_mcp(tmp_path)
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert set(data["mcpServers"]) == {"a", "b"}


# ---------------------------------------------------------------------------
# load_registry / validate_registry
# ---------------------------------------------------------------------------


def test_load_registry_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing registry"):
        mcp_manage.load_registry(tmp_path)


def test_load_registry_falls_back_to_example(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml.example").write_text(yaml.safe_dump({"servers": {}}), encoding="utf-8")
    data = mcp_manage.load_registry(tmp_path)
    assert data == {"servers": {}}


def test_load_registry_invalid_yaml_raises(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid registry YAML"):
        mcp_manage.load_registry(tmp_path)


def test_validate_registry_no_registry_file(tmp_path: Path) -> None:
    assert mcp_manage.validate_registry(tmp_path) == []


def test_validate_registry_load_error(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text("- not\n- a\n- dict\n", encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert len(errors) == 1
    assert "invalid registry YAML" in errors[0]


def test_validate_registry_servers_not_dict(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(yaml.safe_dump({"servers": []}), encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert errors == ["registry servers must be a mapping"]


def test_validate_registry_missing_mcp_json(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(yaml.safe_dump({"servers": {"a": {}}}), encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("missing merged MCP config" in e for e in errors)


def test_validate_registry_mcp_servers_not_dict(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(yaml.safe_dump({"servers": {"a": {}}}), encoding="utf-8")
    (cursor / "mcp.json").write_text(json.dumps({"mcpServers": []}), encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert errors == ["mcp.json mcpServers must be an object"]


def test_validate_registry_spec_not_dict_and_agents_not_list(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"bad-spec": [], "good-name": {"agents": "not-a-list"}}}),
        encoding="utf-8",
    )
    (cursor / "mcp.json").write_text(json.dumps({"mcpServers": {"good-name": {}}}), encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("bad-spec' must be a mapping" in e for e in errors)
    assert any("good-name' agents must be a list" in e for e in errors)


def test_validate_registry_name_not_in_mcp_servers(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"ghost": {"agents": []}}}), encoding="utf-8"
    )
    (cursor / "mcp.json").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("ghost' not in .cursor/mcp.json" in e for e in errors)


def test_validate_registry_all_pass(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"a": {"agents": ["implementer"]}}}), encoding="utf-8"
    )
    (cursor / "mcp.json").write_text(json.dumps({"mcpServers": {"a": {}}}), encoding="utf-8")
    assert mcp_manage.validate_registry(tmp_path) == []


def test_validate_registry_url_based_server_passes(tmp_path: Path) -> None:
    """URL-based (remote) servers like DeepWiki have no `command`/`args` — must still validate."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"deepwiki": {"agents": ["researcher"]}}}), encoding="utf-8"
    )
    (cursor / "mcp.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}), encoding="utf-8"
    )
    assert mcp_manage.validate_registry(tmp_path) == []


def test_write_merged_mcp_with_url_based_user_server(tmp_path: Path) -> None:
    """merge_mcp_configs/write_merged_mcp treat server specs generically — no `command` required."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}), encoding="utf-8"
    )
    dest = mcp_manage.write_merged_mcp(tmp_path)
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["mcpServers"]["deepwiki"] == {"url": "https://mcp.deepwiki.com/mcp"}


# ---------------------------------------------------------------------------
# link_user_server
# ---------------------------------------------------------------------------


def test_link_user_server_empty_fragment_raises(tmp_path: Path) -> None:
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="fragment must contain mcpServers"):
        mcp_manage.link_user_server(tmp_path, "x", fragment)


def test_link_user_server_from_example_when_no_user_file(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.user.example.json").write_text(json.dumps({"mcpServers": {"example": {}}}), encoding="utf-8")
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {"new-one": {"command": "x"}}}), encoding="utf-8")
    mcp_manage.link_user_server(tmp_path, "new-one", fragment)
    saved = json.loads((cursor / "mcp.user.json").read_text(encoding="utf-8"))
    assert "example" in saved["mcpServers"]
    assert "new-one" in saved["mcpServers"]


def test_link_user_server_existing_user_servers_not_dict_raises(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.user.json").write_text(json.dumps({"mcpServers": []}), encoding="utf-8")
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {"a": {}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="mcpServers must be an object"):
        mcp_manage.link_user_server(tmp_path, "a", fragment)


def test_link_user_server_name_not_found_multiple_entries_raises(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {"a": {}, "b": {}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="fragment has multiple servers"):
        mcp_manage.link_user_server(tmp_path, "not-a-or-b", fragment)


def test_link_user_server_name_not_found_single_entry_renamed(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {"original-name": {"command": "x"}}}), encoding="utf-8")
    mcp_manage.link_user_server(tmp_path, "renamed", fragment)
    saved = json.loads((cursor / "mcp.user.json").read_text(encoding="utf-8"))
    assert saved["mcpServers"]["renamed"] == {"command": "x"}


# ---------------------------------------------------------------------------
# ensure_mcp_gitignore
# ---------------------------------------------------------------------------


def test_ensure_mcp_gitignore_creates_new(tmp_path: Path) -> None:
    mcp_manage.ensure_mcp_gitignore(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".cursor/mcp.user.json" in text


def test_ensure_mcp_gitignore_appends_when_missing(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    mcp_manage.ensure_mcp_gitignore(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in text
    assert ".cursor/mcp.user.json" in text
    assert ".local/user_settings/mcp.secrets.yaml" in text


def test_ensure_mcp_gitignore_noop_when_present(tmp_path: Path) -> None:
    existing = (
        "node_modules/\n"
        ".cursor/mcp.user.json\n"
        ".local/user_settings/mcp.secrets.yaml\n"
    )
    (tmp_path / ".gitignore").write_text(existing, encoding="utf-8")
    mcp_manage.ensure_mcp_gitignore(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == existing


def test_ensure_mcp_gitignore_adds_secrets_line(tmp_path: Path) -> None:
    existing = "node_modules/\n.cursor/mcp.user.json\n"
    (tmp_path / ".gitignore").write_text(existing, encoding="utf-8")
    mcp_manage.ensure_mcp_gitignore(tmp_path)
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".local/user_settings/mcp.secrets.yaml" in text
    assert ".cursor/mcp.user.json" in text
