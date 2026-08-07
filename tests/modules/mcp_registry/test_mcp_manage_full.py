"""
File: test_mcp_manage_full.py
Path: tests/modules/mcp_registry/test_mcp_manage_full.py
Role: Full-branch coverage for mcp_manage.py (merge, registry validate, link, gitignore).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/mcp_manage.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"

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


def test_validate_registry_missing_kit_fragment(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(yaml.safe_dump({"servers": {"a": {}}}), encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("missing kit MCP fragment" in e for e in errors)


def test_validate_registry_kit_servers_not_dict(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(yaml.safe_dump({"servers": {"a": {}}}), encoding="utf-8")
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": []}), encoding="utf-8"
    )
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("mcpServers must be an object" in e for e in errors)


def test_validate_registry_spec_not_dict_and_agents_not_list(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"good-name": {}}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"bad-spec": [], "good-name": {"agents": "not-a-list"}}}),
        encoding="utf-8",
    )
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("bad-spec' must be a mapping" in e for e in errors)
    assert any("good-name' agents must be a list" in e for e in errors)


def test_validate_registry_name_not_in_mcp_servers(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"ghost": {"agents": []}}}), encoding="utf-8"
    )
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("ghost' not in merged kit+user" in e for e in errors)


def test_validate_registry_all_pass(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"a": {}}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"a": {"agents": ["implementer"]}}}), encoding="utf-8"
    )
    assert mcp_manage.validate_registry(tmp_path) == []


def test_validate_registry_url_based_server_passes(tmp_path: Path) -> None:
    """URL-based (remote) servers like DeepWiki have no `command`/`args` — must still validate."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {}}), encoding="utf-8"
    )
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}),
        encoding="utf-8",
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"deepwiki": {"agents": ["researcher"], "tier": "external"}}}),
        encoding="utf-8",
    )
    assert mcp_manage.validate_registry(tmp_path) == []


def test_write_merged_mcp_kit_dev_writes_kit_tier_only(tmp_path: Path) -> None:
    """Kit-dev marker: disk mcp.json stays kit-only even when user fragment has DeepWiki."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"agent-colony-mcp": {"command": "echo"}}}),
        encoding="utf-8",
    )
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}),
        encoding="utf-8",
    )
    marker = tmp_path / mcp_manage.KIT_DEV_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    dest = mcp_manage.write_merged_mcp(tmp_path)
    disk = json.loads(dest.read_text(encoding="utf-8"))["mcpServers"]
    assert list(disk.keys()) == ["agent-colony-mcp"]
    logical = mcp_manage.load_merged_servers(tmp_path)
    assert "deepwiki" in logical
    assert "agent-colony-mcp" in logical


def test_validate_registry_kit_dev_rejects_external_in_live(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"agent-colony-mcp": {}}}), encoding="utf-8"
    )
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}),
        encoding="utf-8",
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {
                "servers": {
                    "agent-colony-mcp": {"tier": "kit", "agents": []},
                    "deepwiki": {"tier": "external", "agents": ["researcher"]},
                }
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / mcp_manage.KIT_DEV_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("kit-dev: live registry must not list external" in e for e in errors)


def test_effective_registry_kit_dev_overlays_example_for_merged_user(
    tmp_path: Path,
) -> None:
    """Kit-dev: deepwiki in user + example allows smoke/call without live external entry."""
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"agent-colony-mcp": {"command": "echo"}}}),
        encoding="utf-8",
    )
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}),
        encoding="utf-8",
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "servers": {
                    "agent-colony-mcp": {
                        "tier": "kit",
                        "agents": ["implementer"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (cursor / "mcp.registry.yaml.example").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "servers": {
                    "agent-colony-mcp": {
                        "tier": "kit",
                        "agents": ["implementer"],
                    },
                    "deepwiki": {
                        "tier": "external",
                        "agents": ["researcher", "implementer"],
                        "tools_hint": ["ask_question"],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / mcp_manage.KIT_DEV_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")

    effective = mcp_manage.effective_registry_servers(tmp_path)
    assert "agent-colony-mcp" in effective
    assert "deepwiki" in effective
    assert mcp_manage.assert_server_allowed(tmp_path, "deepwiki") is None
    assert mcp_manage.assert_server_allowed(tmp_path, "deepwiki", agent="researcher") is None
    assert (
        mcp_manage.assert_server_allowed(tmp_path, "deepwiki", agent="auditor") is not None
    )
    # Live validate still green (no external in live).
    assert mcp_manage.validate_registry(tmp_path) == []


def test_effective_registry_kit_dev_rejects_deepwiki_without_user_fragment(
    tmp_path: Path,
) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"agent-colony-mcp": {}}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {"servers": {"agent-colony-mcp": {"tier": "kit", "agents": ["implementer"]}}}
        ),
        encoding="utf-8",
    )
    (cursor / "mcp.registry.yaml.example").write_text(
        yaml.safe_dump(
            {
                "servers": {
                    "agent-colony-mcp": {"tier": "kit", "agents": ["implementer"]},
                    "deepwiki": {"tier": "external", "agents": ["researcher"]},
                }
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / mcp_manage.KIT_DEV_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")

    effective = mcp_manage.effective_registry_servers(tmp_path)
    assert "deepwiki" not in effective
    err = mcp_manage.assert_server_allowed(tmp_path, "deepwiki")
    assert err is not None
    assert "deepwiki" in err


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


# ---------------------------------------------------------------------------
# DeepWiki consumer seed helpers
# ---------------------------------------------------------------------------


def test_ensure_deepwiki_user_fragment_creates_when_missing(tmp_path: Path) -> None:
    assert mcp_manage.ensure_deepwiki_user_fragment(tmp_path) is True
    user = json.loads((tmp_path / ".cursor" / "mcp.user.json").read_text(encoding="utf-8"))
    assert user["mcpServers"]["deepwiki"] == {"url": mcp_manage.DEEPWIKI_URL}
    assert "my-custom-server" not in user["mcpServers"]
    assert mcp_manage.ensure_deepwiki_user_fragment(tmp_path) is False


def test_ensure_deepwiki_user_fragment_adds_missing_key_only(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"other": {"command": "x"}}}),
        encoding="utf-8",
    )
    assert mcp_manage.ensure_deepwiki_user_fragment(tmp_path) is True
    user = json.loads((cursor / "mcp.user.json").read_text(encoding="utf-8"))
    assert "other" in user["mcpServers"]
    assert user["mcpServers"]["deepwiki"]["url"] == mcp_manage.DEEPWIKI_URL


def test_ensure_deepwiki_user_fragment_does_not_overwrite_existing(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    custom = {"url": "https://example.invalid/mcp"}
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": {"deepwiki": custom}}),
        encoding="utf-8",
    )
    assert mcp_manage.ensure_deepwiki_user_fragment(tmp_path) is False
    user = json.loads((cursor / "mcp.user.json").read_text(encoding="utf-8"))
    assert user["mcpServers"]["deepwiki"] == custom


def test_ensure_deepwiki_registry_creates_and_preserves_agents(tmp_path: Path) -> None:
    assert mcp_manage.ensure_deepwiki_registry(tmp_path) is True
    data = yaml.safe_load((tmp_path / ".cursor" / "mcp.registry.yaml").read_text(encoding="utf-8"))
    assert "agent-colony-mcp" in data["servers"]
    assert data["servers"]["deepwiki"]["agents"] == list(mcp_manage.DEEPWIKI_AGENTS)
    assert mcp_manage.ensure_deepwiki_registry(tmp_path) is False

    data["servers"]["deepwiki"]["agents"] = ["researcher"]
    (tmp_path / ".cursor" / "mcp.registry.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )
    assert mcp_manage.ensure_deepwiki_registry(tmp_path) is False
    again = yaml.safe_load((tmp_path / ".cursor" / "mcp.registry.yaml").read_text(encoding="utf-8"))
    assert again["servers"]["deepwiki"]["agents"] == ["researcher"]

    assert mcp_manage.ensure_deepwiki_registry(tmp_path, force_registry_agents=True) is True
    forced = yaml.safe_load((tmp_path / ".cursor" / "mcp.registry.yaml").read_text(encoding="utf-8"))
    assert forced["servers"]["deepwiki"]["agents"] == list(mcp_manage.DEEPWIKI_AGENTS)


def test_ensure_deepwiki_user_fragment_rejects_non_object_servers(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.user.json").write_text(
        json.dumps({"mcpServers": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="mcpServers must be an object"):
        mcp_manage.ensure_deepwiki_user_fragment(tmp_path)


def test_ensure_deepwiki_registry_invalid_root_and_servers(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid registry YAML"):
        mcp_manage.ensure_deepwiki_registry(tmp_path)

    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"version": 1, "servers": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="registry servers must be a mapping"):
        mcp_manage.ensure_deepwiki_registry(tmp_path)


def test_ensure_deepwiki_registry_force_non_dict_and_replace(
    tmp_path: Path,
) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "servers": {
                    "agent-colony-mcp": {"tier": "kit", "agents": []},
                    "deepwiki": "not-a-mapping",
                },
            }
        ),
        encoding="utf-8",
    )
    assert mcp_manage.ensure_deepwiki_registry(tmp_path, force_registry_agents=True) is True
    forced = yaml.safe_load((cursor / "mcp.registry.yaml").read_text(encoding="utf-8"))
    assert isinstance(forced["servers"]["deepwiki"], dict)
    assert forced["servers"]["deepwiki"]["agents"] == list(mcp_manage.DEEPWIKI_AGENTS)
    assert "tools_hint" in forced["servers"]["deepwiki"]
    assert forced["servers"]["deepwiki"]["tier"] == "external"

    # only_if_missing_server=False replaces existing deepwiki entry
    forced["servers"]["deepwiki"] = {"tier": "external", "agents": ["researcher"]}
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(forced, sort_keys=False),
        encoding="utf-8",
    )
    assert (
        mcp_manage.ensure_deepwiki_registry(
            tmp_path, only_if_missing_server=False, force_registry_agents=False
        )
        is True
    )
    replaced = yaml.safe_load((cursor / "mcp.registry.yaml").read_text(encoding="utf-8"))
    assert replaced["servers"]["deepwiki"]["agents"] == list(mcp_manage.DEEPWIKI_AGENTS)


def test_validate_registry_merged_servers_not_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"agent-colony-mcp": {}}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"agent-colony-mcp": {"tier": "kit", "agents": []}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mcp_manage,
        "compute_merged_mcp",
        lambda root: {"mcpServers": []},
    )
    errors = mcp_manage.validate_registry(tmp_path)
    assert any("merged mcpServers must be an object" in e for e in errors)


def test_validate_registry_kit_dev_skips_non_dict_spec(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"agent-colony-mcp": {}}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {
                "servers": {
                    "agent-colony-mcp": {"tier": "kit", "agents": []},
                    "weird": "not-a-dict",
                }
            }
        ),
        encoding="utf-8",
    )
    marker = tmp_path / mcp_manage.KIT_DEV_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    errors = mcp_manage.validate_registry(tmp_path)
    # non-dict skipped in kit-dev external loop; still flagged in general loop
    assert any("must be a mapping" in e for e in errors)


def test_load_merged_servers_rejects_non_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mcp_manage,
        "compute_merged_mcp",
        lambda root: {"mcpServers": "bad"},
    )
    with pytest.raises(ValueError, match="mcpServers must be an object"):
        mcp_manage.load_merged_servers(tmp_path)


def test_load_example_registry_servers_edges(tmp_path: Path) -> None:
    assert mcp_manage._load_example_registry_servers(tmp_path) == {}
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    example = cursor / "mcp.registry.yaml.example"
    example.write_text(":\n  bad yaml: [\n", encoding="utf-8")
    assert mcp_manage._load_example_registry_servers(tmp_path) == {}
    example.write_text("[]\n", encoding="utf-8")
    assert mcp_manage._load_example_registry_servers(tmp_path) == {}


def test_effective_registry_servers_error_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.registry.yaml").write_text(":\n  broken\n", encoding="utf-8")
    marker = tmp_path / mcp_manage.KIT_DEV_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    # YAML error on live → empty live, then merge failure returns live
    monkeypatch.setattr(
        mcp_manage,
        "compute_merged_mcp",
        lambda root: (_ for _ in ()).throw(ValueError("merge fail")),
    )
    assert mcp_manage.effective_registry_servers(tmp_path) == {}

    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"agent-colony-mcp": {"tier": "kit"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mcp_manage,
        "compute_merged_mcp",
        lambda root: {"mcpServers": ["not-an-object"]},
    )
    effective = mcp_manage.effective_registry_servers(tmp_path)
    assert "agent-colony-mcp" in effective
