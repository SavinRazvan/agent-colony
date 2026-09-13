"""Tests for project_ssot.owner normalization (gh --owner hygiene)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

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


def _fake_user_settings(owner: str) -> SimpleNamespace:
    return SimpleNamespace(
        GITHUB_COLLAB_REL=".local/user_settings/github.collaboration.yaml",
        load_github_collaboration=lambda root: {
            "project_ssot": {
                "enabled": True,
                "owner": owner,
                "number": 1,
                "project_id": "PVT_test",
            }
        },
    )


def test_load_project_ssot_strips_users_prefix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        pa,
        "_import_user_settings",
        lambda root: _fake_user_settings("users/FakeLogin"),
    )
    ssot, errs = pa.load_project_ssot(tmp_path)
    assert errs == []
    assert ssot is not None
    assert ssot["owner"] == "FakeLogin"


def test_load_project_ssot_rejects_invalid_owner_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        pa,
        "_import_user_settings",
        lambda root: _fake_user_settings("users/a/b"),
    )
    ssot, errs = pa.load_project_ssot(tmp_path)
    assert ssot is not None
    assert errs
    assert "invalid" in errs[0]
    assert "gh --owner" in errs[0]
    assert "rate limit" not in errs[0].lower()
    assert "429" not in errs[0]
