"""
File: test_bootstrap_activate.py
Path: tests/modules/install/test_bootstrap_activate.py
Role: Coverage for zero-dep bootstrap_activate.py first-install entrypoint.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/bootstrap_activate.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BOOTSTRAP = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "bootstrap_activate.py"


def _load_bootstrap():
    spec = importlib.util.spec_from_file_location("bootstrap_activate", BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _manifest_dir(base: Path) -> Path:
    (base / ".ai_infra").mkdir(parents=True, exist_ok=True)
    (base / ".ai_infra" / "manifest.yaml").write_text("kit_version: 0.0.0\n", encoding="utf-8")
    return base


def test_payload_from_this_script_prefers_kit_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_bootstrap()
    # Point __file__ at a fake kit-layout copy of the script.
    kit = tmp_path / "kit"
    payload = _manifest_dir(kit / "payload")
    script = kit / ".ai_infra" / "scripts" / "install" / "bootstrap_activate.py"
    script.parent.mkdir(parents=True)
    script.write_text("# stub\n", encoding="utf-8")
    monkeypatch.setattr(mod, "__file__", str(script))
    assert mod._payload_from_this_script() == payload.resolve()


def test_main_fails_without_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_bootstrap()
    monkeypatch.setattr(mod, "_payload_from_this_script", lambda: None)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    code = mod.main(["--directory", str(tmp_path / "app")])
    assert code == 1


def test_main_invokes_cmd_activate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_bootstrap()
    payload = _manifest_dir(tmp_path / "payload")
    # Minimal install package so _load_activate_cli can open activate_cli.py
    cli = payload / ".ai_infra" / "install" / "agent_colony" / "activate_cli.py"
    cli.parent.mkdir(parents=True)
    # Re-use real activate_cli from kit for loader; patch cmd_activate after load.
    real_cli = REPO_ROOT / ".ai_infra" / "install" / "agent_colony" / "activate_cli.py"
    cli.write_text(real_cli.read_text(encoding="utf-8"), encoding="utf-8")
    (payload / ".ai_infra" / "paths.py").write_text(
        (REPO_ROOT / ".ai_infra" / "paths.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    called: dict[str, object] = {}

    def _fake_cmd(ns: SimpleNamespace) -> int:
        called["directory"] = Path(ns.directory)
        called["source"] = Path(ns.source)
        return 0

    monkeypatch.setattr(mod, "_payload_from_this_script", lambda: payload)

    def _load(_payload: Path):
        return SimpleNamespace(cmd_activate=_fake_cmd)

    monkeypatch.setattr(mod, "_load_activate_cli", _load)
    code = mod.main(["--directory", str(tmp_path / "app")])
    assert code == 0
    assert called["directory"] == (tmp_path / "app").resolve()
    assert called["source"] == payload.resolve()
