"""
File: test_install_contract.py
Path: tests/modules/install/test_install_contract.py
Role: Assert installed consumer trees match install-contract.json profiles.
Used By:
 - pytest
Depends On:
 - .ai_infra/install-contract.json
 - .ai_infra/scripts/install/scaffold.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from tests.modules.install._manifest_version import expected_kit_version

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO_ROOT / ".ai_infra" / "install-contract.json"
SCAFFOLD_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"


def _load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold", SCAFFOLD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_contract_profile(contract: dict, name: str) -> dict:
    raw = contract["profiles"][name]
    if "extends" not in raw:
        return raw
    base = _resolve_contract_profile(contract, raw["extends"])
    merged = {
        "required_paths": list(base.get("required_paths", [])),
        "forbidden_paths": list(base.get("forbidden_paths", [])),
        "recommended_paths": list(base.get("recommended_paths", [])),
    }
    merged["required_paths"].extend(raw.get("required_paths", []))
    merged["forbidden_paths"].extend(raw.get("forbidden_paths", []))
    merged["recommended_paths"].extend(raw.get("recommended_paths", []))
    return merged


def _assert_contract(target: Path, profile: str) -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    spec = _resolve_contract_profile(contract, profile)
    for rel in spec["required_paths"]:
        assert (target / rel).exists(), f"missing required path: {rel}"
    for rel in spec["forbidden_paths"]:
        assert not (target / rel).exists(), f"forbidden path present: {rel}"
    for rel in spec.get("recommended_paths", []):
        assert (target / rel).exists(), f"missing recommended path: {rel}"


@pytest.mark.parametrize("profile", ("default", "with_mcp", "consumer_lite"))
def test_install_contract_profiles(tmp_path: Path, profile: str) -> None:
    mod = _load_scaffold()
    target = tmp_path / f"consumer-{profile}"
    mod.scaffold(
        target,
        REPO_ROOT,
        profile=profile,
        with_mcp_json=(profile in ("with_mcp", "consumer_lite")),
    )
    _assert_contract(target, profile)
    kit_version = target / ".ai_infra" / ".kit-version"
    assert kit_version.is_file()
    assert kit_version.read_text(encoding="utf-8").strip() == expected_kit_version()
    if profile == "consumer_lite":
        assert not (target / ".cursor" / "agents" / "auditor.md").exists()
        assert not (target / ".cursor" / "skills" / "board-shell").exists()
        marker = target / ".local" / "generated-data" / "install-profile.json"
        assert marker.is_file()
        assert json.loads(marker.read_text(encoding="utf-8"))["profile"] == "consumer_lite"
