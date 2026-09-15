"""
File: test_debug_capture.py
Path: tests/modules/debug/test_debug_capture.py
Role: Tests for secure debugger command capture and ingest.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/debug_capture.py
 - .ai_infra/install/agent_colony/debug_storage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

import debug_capture  # noqa: E402
import debug_storage  # noqa: E402


def _campaign(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    campaign = workspace / ".local" / "workflow-artifacts" / "debug" / "demo"
    debug_storage.ensure_owner_dir(campaign / "vault" / "logs" / "by-run")
    debug_storage.atomic_write_text(campaign / "vault" / "logs" / "events.jsonl", "")
    return workspace, campaign


def test_capture_uses_shell_false_and_redacts_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace, campaign = _campaign(tmp_path)
    real_popen = debug_capture.subprocess.Popen
    seen: dict[str, object] = {}

    def spy_popen(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        seen["shell"] = kwargs.get("shell")
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(debug_capture.subprocess, "Popen", spy_popen)
    secret = "capture-secret-canary"
    code, result = debug_capture.capture_command(
        workspace=workspace,
        campaign_dir=campaign,
        argv=[sys.executable, "-c", "import os; print(os.environ['API_TOKEN'])"],
        env={"API_TOKEN": secret, "PATH": ""},
    )
    assert code == 0
    assert seen["shell"] is False
    assert secret not in (result.run_dir / "stdout.log").read_text(encoding="utf-8")


def test_capture_timeout_maps_to_124(tmp_path: Path) -> None:
    workspace, campaign = _campaign(tmp_path)
    code, result = debug_capture.capture_command(
        workspace=workspace,
        campaign_dir=campaign,
        argv=[sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_s=1,
        propagate_exit=True,
    )
    assert code == 124
    assert result.termination_reason == "timeout"


def test_capture_refuses_native_windows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace, campaign = _campaign(tmp_path)
    monkeypatch.setattr(debug_capture.os, "name", "nt")
    with pytest.raises(debug_capture.DebugCaptureError):
        debug_capture.capture_command(
            workspace=workspace,
            campaign_dir=campaign,
            argv=[sys.executable, "-c", "print('x')"],
        )


def test_ingest_redacts_file(tmp_path: Path) -> None:
    workspace, campaign = _campaign(tmp_path)
    source = workspace / "input.log"
    source.write_text("password: ingest-secret-canary\n", encoding="utf-8")
    result = debug_capture.ingest_file(workspace=workspace, campaign_dir=campaign, source=Path("input.log"))
    assert "ingest-secret-canary" not in (result.run_dir / "stdout.log").read_text(encoding="utf-8")
