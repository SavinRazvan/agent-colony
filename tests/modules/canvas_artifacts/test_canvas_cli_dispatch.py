"""
File: test_canvas_cli_dispatch.py
Path: tests/modules/canvas_artifacts/test_canvas_cli_dispatch.py
Role: Dispatch coverage for canvas_cli via cli.main (ADR-010).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/cli.py
 - .ai_infra/install/agent_colony/canvas_cli.py
 - .ai_infra/install/agent_colony/canvas_manage.py
Notes:
 - Imports package modules via sys.path so coverage attributes correctly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import canvas_manage  # noqa: E402
import cli  # noqa: E402

CANVAS_SRC = """import { Stack, Text } from "cursor/canvas";
export default function DemoCanvas() {
  return <Stack><Text>demo</Text></Stack>;
}
"""

CANVAS_SEPARATE_EXPORT = """function Demo() { return null; }
export default Demo;
"""


def _seed_lwp(root: Path) -> None:
    pr = root / ".ai_infra" / "scripts" / "pr"
    pr.mkdir(parents=True)
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "local_workflow_paths.py"
    (pr / "local_workflow_paths.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    exemplars = root / ".ai_infra" / "templates" / "local-workspace" / "exemplars"
    exemplars.mkdir(parents=True)
    for name in ("local-canvases-index.md", "local-plans-index.md"):
        src_idx = REPO_ROOT / ".ai_infra" / "templates" / "local-workspace" / "exemplars" / name
        if src_idx.is_file():
            (exemplars / name).write_text(src_idx.read_text(encoding="utf-8"), encoding="utf-8")


def _layout(root: Path) -> tuple[Path, Path, Path]:
    _seed_lwp(root)
    repo = root / "canvases"
    managed = root / "managed-canvases"
    local = root / ".local" / "canvases"
    repo.mkdir(parents=True)
    managed.mkdir(parents=True)
    local.mkdir(parents=True)
    (repo / "demo.canvas.tsx").write_text(CANVAS_SRC, encoding="utf-8")
    return repo, managed, local


def test_canvas_doctor_writes_artifact(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    assert cli.main(["canvas", "doctor", "--directory", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "# Canvas doctor" in out
    assert "artifact:" in out
    arts = list((tmp_path / ".local" / "workflow-artifacts" / "canvas").glob("doctor-*.md"))
    assert len(arts) == 1


def test_canvas_list_empty_tiers(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: None)
    assert cli.main(["canvas", "list", "--directory", str(tmp_path), "--tier", "all"]) == 0
    out = capsys.readouterr().out
    assert "(none)" in out


def test_canvas_list_repo_tier(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    assert cli.main(["canvas", "list", "--directory", str(tmp_path), "--tier", "repo"]) == 0
    out = capsys.readouterr().out
    assert "[repo]" in out
    assert "demo.canvas.tsx" in out


def test_canvas_sync_missing_source(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    managed = tmp_path / "managed"
    managed.mkdir()
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    code = cli.main(["canvas", "sync", "--directory", str(tmp_path), "--name", "nope"])
    assert code == canvas_manage.EXIT_NOT_FOUND
    err = capsys.readouterr().err
    assert "FAIL" in err


def test_canvas_sync_all_without_force(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    code = cli.main(["canvas", "sync", "--directory", str(tmp_path), "--all"])
    assert code == canvas_manage.EXIT_USAGE
    assert "FAIL" in capsys.readouterr().err


def test_canvas_sync_all_force(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    assert cli.main(["canvas", "sync", "--directory", str(tmp_path), "--all", "--force"]) == 0
    out = capsys.readouterr().out
    assert "copied" in out
    assert (managed / "demo.canvas.tsx").is_file()


def test_canvas_sync_nothing_to_copy(tmp_path: Path, monkeypatch, capsys) -> None:
    repo, managed, _ = _layout(tmp_path)
    (managed / "demo.canvas.tsx").write_text(CANVAS_SRC, encoding="utf-8")
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    assert cli.main(["canvas", "sync", "--directory", str(tmp_path), "--missing"]) == 0
    assert "nothing to copy" in capsys.readouterr().out


def test_canvas_sync_by_name(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    assert cli.main(["canvas", "sync", "--directory", str(tmp_path), "--name", "demo"]) == 0
    assert "copied 1" in capsys.readouterr().out


def test_canvas_save_with_validation_warnings(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    (managed / "demo.canvas.tsx").write_text(CANVAS_SEPARATE_EXPORT, encoding="utf-8")
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    assert cli.main(
        ["canvas", "save", "--directory", str(tmp_path), "--slug", "demo", "--agent", "implementer"]
    ) == 0
    captured = capsys.readouterr()
    assert "WARN" in captured.err
    assert "canvas save:" in captured.out


def test_canvas_save_not_found(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_lwp(tmp_path)
    managed = tmp_path / "managed"
    managed.mkdir()
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    code = cli.main(["canvas", "save", "--directory", str(tmp_path), "--slug", "missing"])
    assert code == canvas_manage.EXIT_NOT_FOUND


def test_canvas_save_invalid_slug(tmp_path: Path, monkeypatch, capsys) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    code = cli.main(["canvas", "save", "--directory", str(tmp_path), "--slug", "Bad_Name"])
    assert code == canvas_manage.EXIT_VALIDATION
