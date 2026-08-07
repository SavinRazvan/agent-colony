"""
File: test_mcp_doctor.py
Path: tests/modules/mcp_client/test_mcp_doctor.py
Role: Unit tests for mcp doctor report builders and validate --strict.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/mcp_cli.py
 - .ai_infra/install/agent_colony/mcp_manage.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CW = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    # Ensure sibling imports resolve
    if str(CW) not in sys.path:
        sys.path.insert(0, str(CW))
    spec.loader.exec_module(mod)
    return mod


def _seed_kit(root: Path, *, with_registry: bool = False, with_user: bool = False) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True)
    kit = json.loads((REPO_ROOT / ".cursor" / "mcp.json.kit.example").read_text(encoding="utf-8"))
    (cursor / "mcp.json.kit.example").write_text(json.dumps(kit, indent=2), encoding="utf-8")
    if with_user:
        user = {
            "mcpServers": {
                "deepwiki": {"url": "https://mcp.deepwiki.com/mcp"},
            }
        }
        (cursor / "mcp.user.json").write_text(json.dumps(user, indent=2), encoding="utf-8")
    if with_registry:
        registry = yaml.safe_load(
            (REPO_ROOT / ".cursor" / "mcp.registry.yaml.example").read_text(encoding="utf-8")
        )
        # only keep servers we can satisfy
        if with_user:
            registry["servers"] = {
                k: v
                for k, v in registry["servers"].items()
                if k in ("agent-colony-mcp", "deepwiki")
            }
        else:
            registry["servers"] = {"agent-colony-mcp": registry["servers"]["agent-colony-mcp"]}
        (cursor / "mcp.registry.yaml").write_text(yaml.dump(registry), encoding="utf-8")
    else:
        # still ship example for doctor fallback
        example = (REPO_ROOT / ".cursor" / "mcp.registry.yaml.example").read_text(encoding="utf-8")
        (cursor / "mcp.registry.yaml.example").write_text(example, encoding="utf-8")


def test_doctor_report_configured_vs_host(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    if str(CW) not in sys.path:
        sys.path.insert(0, str(CW))
    manage = _load("mcp_manage", CW / "mcp_manage.py")
    mcp_cli = _load("mcp_cli", CW / "mcp_cli.py")
    manage.write_merged_mcp(tmp_path)
    mcps = tmp_path / "fake-mcps"
    (mcps / "cursor-ide-browser").mkdir(parents=True)
    original = manage.cursor_project_mcps_dir
    manage.cursor_project_mcps_dir = lambda _root: mcps  # type: ignore[assignment]
    try:
        report = mcp_cli.build_doctor_report(tmp_path)
    finally:
        manage.cursor_project_mcps_dir = original  # type: ignore[assignment]
    assert "agent-colony-mcp" in report["merged_servers"]
    assert "agent-colony-mcp" in report["configured_not_host_loaded"]
    assert "cursor-ide-browser" in report["host_loaded_not_configured"]
    md = mcp_cli.format_doctor_markdown(report)
    assert "configured but NOT host-loaded" in md


def test_validate_strict_fails_without_live_registry(tmp_path: Path) -> None:
    _seed_kit(tmp_path, with_registry=False)
    cli = _load("agent_colony_cli_doc", REPO_ROOT / ".ai_infra" / "install" / "agent_colony" / "cli.py")
    code = cli.main(["mcp", "validate", "--directory", str(tmp_path), "--strict"])
    assert code == 1


def test_validate_strict_passes_with_live_registry(tmp_path: Path) -> None:
    _seed_kit(tmp_path, with_registry=True, with_user=False)
    cli = _load("agent_colony_cli_doc2", REPO_ROOT / ".ai_infra" / "install" / "agent_colony" / "cli.py")
    code = cli.main(["mcp", "validate", "--directory", str(tmp_path), "--strict"])
    assert code == 0


def test_doctor_cli_writes_artifact(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    cli = _load("agent_colony_cli_doc3", REPO_ROOT / ".ai_infra" / "install" / "agent_colony" / "cli.py")
    code = cli.main(["mcp", "doctor", "--directory", str(tmp_path)])
    assert code == 0
    arts = list((tmp_path / ".local" / "workflow-artifacts" / "mcp").glob("doctor-*.md"))
    assert arts
