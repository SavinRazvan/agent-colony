"""Tests for project_ssot.owner normalization (gh --owner hygiene)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".ai_infra" / "install" / "agent_colony"))

import project_atomics as pa  # noqa: E402


def test_normalize_project_owner_strips_prefixes() -> None:
    assert pa.normalize_project_owner("users/SavinRazvan") == ("SavinRazvan", None)
    assert pa.normalize_project_owner("@orgs/Acme") == ("Acme", None)
    assert pa.normalize_project_owner("SavinRazvan") == ("SavinRazvan", None)


def test_owner_yaml_looks_url_shaped() -> None:
    assert pa.owner_yaml_looks_url_shaped("users/SavinRazvan") is True
    assert pa.owner_yaml_looks_url_shaped("@orgs/Acme") is True
    assert pa.owner_yaml_looks_url_shaped("SavinRazvan") is False


def test_normalize_project_owner_rejects_path() -> None:
    owner, err = pa.normalize_project_owner("users/foo/bar")
    assert err is not None
    assert "invalid" in err
