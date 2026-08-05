"""
File: test_canvas_cli.py
Path: tests/modules/canvas_artifacts/test_canvas_cli.py
Role: Tests for canvas Pattern A CLI.
Used By:
 - pytest
Depends On:
 - canvas_manage, canvas_cli
Notes:
 - Monkeypatches Cursor managed dir resolution.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

CANVAS_SRC = """import { Stack, Text } from "cursor/canvas";
export default function DemoCanvas() {
  return <Stack><Text>demo</Text></Stack>;
}
"""


def _load(name: str):
    if str(PKG) not in sys.path:
        sys.path.insert(0, str(PKG))
    spec = importlib.util.spec_from_file_location(name, PKG / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_lwp(root: Path) -> None:
    pr = root / ".ai_infra" / "scripts" / "pr"
    pr.mkdir(parents=True)
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "local_workflow_paths.py"
    (pr / "local_workflow_paths.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


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


def test_sync_name_repo_to_managed(tmp_path: Path, monkeypatch) -> None:
    manage = _load("canvas_manage")
    repo, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    copied = manage.sync_canvas(tmp_path, name="demo", source="repo")
    assert copied == ["demo.canvas.tsx"]
    assert (managed / "demo.canvas.tsx").is_file()


def test_sync_all_requires_force(tmp_path: Path, monkeypatch) -> None:
    manage = _load("canvas_manage")
    repo, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    try:
        manage.sync_canvas(tmp_path, sync_all=True, force=False, source="repo")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "--force" in str(exc)


def test_sync_missing_only(tmp_path: Path, monkeypatch) -> None:
    manage = _load("canvas_manage")
    repo, managed, _ = _layout(tmp_path)
    original = "export default function Old() { return null; }"
    (managed / "existing.canvas.tsx").write_text(original, encoding="utf-8")
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    copied = manage.sync_canvas(tmp_path, missing=True, source="repo")
    assert copied == ["demo.canvas.tsx"]
    assert (managed / "existing.canvas.tsx").read_text() == original


def test_save_managed_to_local(tmp_path: Path, monkeypatch) -> None:
    manage = _load("canvas_manage")
    _, managed, local = _layout(tmp_path)
    (managed / "demo.canvas.tsx").write_text(CANVAS_SRC, encoding="utf-8")
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    dst = manage.save_canvas(tmp_path, slug="demo", source="managed", agent="implementer")
    assert dst == local / "demo.canvas.tsx"
    assert dst.is_file()


def test_doctor_reports_repo_not_managed(tmp_path: Path, monkeypatch) -> None:
    manage = _load("canvas_manage")
    repo, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    report = manage.build_doctor_report(tmp_path)
    assert "demo" in report["repo_not_managed"]
