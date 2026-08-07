"""
File: test_canvas_manage_edges.py
Path: tests/modules/canvas_artifacts/test_canvas_manage_edges.py
Role: Edge coverage for canvas_manage miss lines (ADR-010).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/canvas_manage.py
Notes:
 - Direct imports via sys.path for coverage attribution.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import canvas_manage  # noqa: E402

CANVAS_SRC = """import { Stack, Text } from "cursor/canvas";
export default function DemoCanvas() {
  return <Stack><Text>demo</Text></Stack>;
}
"""


def _seed_lwp(root: Path) -> None:
    pr = root / ".ai_infra" / "scripts" / "pr"
    pr.mkdir(parents=True)
    src = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "local_workflow_paths.py"
    (pr / "local_workflow_paths.py").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    exemplars = root / ".ai_infra" / "templates" / "local-workspace" / "exemplars"
    exemplars.mkdir(parents=True)
    for name in ("local-canvases-index.md",):
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


def test_canvas_filename_invalid() -> None:
    with pytest.raises(ValueError, match="kebab-case"):
        canvas_manage.canvas_filename("Bad Name")


def test_list_canvases_none_and_missing(tmp_path: Path) -> None:
    assert canvas_manage.list_canvases_in_dir(None) == []
    assert canvas_manage.list_canvases_in_dir(tmp_path / "nope") == []


def test_canvas_base_without_suffix() -> None:
    assert canvas_manage.canvas_base("plain") == "plain"
    assert canvas_manage.canvas_base("x.canvas.tsx") == "x"


def test_validate_canvas_source_variants() -> None:
    assert canvas_manage.validate_canvas_source(CANVAS_SRC) == []
    warns = canvas_manage.validate_canvas_source("export default Foo;")
    assert any("separate" in w for w in warns)
    warns2 = canvas_manage.validate_canvas_source("no export here")
    assert any("missing" in w for w in warns2)


def test_format_doctor_markdown_missing_dirs(tmp_path: Path, monkeypatch) -> None:
    _seed_lwp(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: None)
    report = canvas_manage.build_doctor_report(tmp_path)
    body = canvas_manage.format_doctor_markdown(report)
    assert "(missing)" in body or "(not found)" in body
    assert "repo not in managed" in body


def test_stale_managed_detection(tmp_path: Path, monkeypatch) -> None:
    repo, managed, _ = _layout(tmp_path)
    (managed / "demo.canvas.tsx").write_text(CANVAS_SRC, encoding="utf-8")
    now = time.time()
    os.utime(managed / "demo.canvas.tsx", (now - 100, now - 100))
    os.utime(repo / "demo.canvas.tsx", (now, now))
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    report = canvas_manage.build_doctor_report(tmp_path)
    assert "demo" in report["stale_managed"]


def test_sync_creates_managed_when_missing(tmp_path: Path, monkeypatch) -> None:
    repo, _, _ = _layout(tmp_path)
    project = tmp_path / "cursor-project"
    project.mkdir()
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: None)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_project_dir", lambda _r: project)
    copied = canvas_manage.sync_canvas(tmp_path, name="demo", source="repo")
    assert copied == ["demo.canvas.tsx"]
    assert (project / "canvases" / "demo.canvas.tsx").is_file()


def test_sync_no_project_dir(tmp_path: Path, monkeypatch) -> None:
    _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: None)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_project_dir", lambda _r: None)
    with pytest.raises(FileNotFoundError, match="managed project"):
        canvas_manage.sync_canvas(tmp_path, name="demo", source="repo")


def test_sync_source_missing(tmp_path: Path, monkeypatch) -> None:
    _seed_lwp(tmp_path)
    managed = tmp_path / "m"
    managed.mkdir()
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    with pytest.raises(FileNotFoundError, match="source tier"):
        canvas_manage.sync_canvas(tmp_path, name="demo", source="local")


def test_sync_requires_name(tmp_path: Path, monkeypatch) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    with pytest.raises(ValueError, match="--name"):
        canvas_manage.sync_canvas(tmp_path, source="repo")


def test_sync_from_local(tmp_path: Path, monkeypatch) -> None:
    _, managed, local = _layout(tmp_path)
    (local / "demo.canvas.tsx").write_text(CANVAS_SRC, encoding="utf-8")
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    copied = canvas_manage.sync_canvas(tmp_path, name="demo", source="local")
    assert copied == ["demo.canvas.tsx"]


def test_sync_missing_named_file(tmp_path: Path, monkeypatch) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    with pytest.raises(FileNotFoundError, match="missing source canvas"):
        canvas_manage.sync_canvas(tmp_path, name="ghost", source="repo")


def test_save_missing_source_dir(tmp_path: Path, monkeypatch) -> None:
    _seed_lwp(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: None)
    with pytest.raises(FileNotFoundError, match="source tier"):
        canvas_manage.save_canvas(tmp_path, slug="demo", source="managed")


def test_save_from_repo_and_index_dedup(tmp_path: Path, monkeypatch) -> None:
    repo, managed, local = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    # ensure index exists for append + dedup paths
    index = local / "index.md"
    index.write_text(
        "# Canvases\n\n| slug | saved_utc | agent | note |\n| --- | --- | --- | --- |\n",
        encoding="utf-8",
    )
    dst = canvas_manage.save_canvas(tmp_path, slug="demo", source="repo", agent="implementer")
    assert dst == local / "demo.canvas.tsx"
    text1 = index.read_text(encoding="utf-8")
    assert "demo" in text1
    # second save same slug — dedup (slug already in index)
    canvas_manage.save_canvas(tmp_path, slug="demo", source="repo", agent="auditor")
    text2 = index.read_text(encoding="utf-8")
    assert text1.count("| demo |") == text2.count("| demo |")


def test_save_missing_file(tmp_path: Path, monkeypatch) -> None:
    _, managed, _ = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    with pytest.raises(FileNotFoundError, match="missing canvas"):
        canvas_manage.save_canvas(tmp_path, slug="nope", source="repo")


def test_save_from_local_source_branch(tmp_path: Path, monkeypatch) -> None:
    """Cover save_canvas else-branch (source=local) without SameFileError."""
    _, managed, local = _layout(tmp_path)
    monkeypatch.setattr(canvas_manage.cursor_host_paths, "cursor_canvases_dir", lambda _r: managed)
    with pytest.raises(FileNotFoundError, match="missing canvas"):
        canvas_manage.save_canvas(tmp_path, slug="demo", source="local")
    # now with file present — mock copy to avoid SameFileError
    (local / "demo.canvas.tsx").write_text(CANVAS_SRC, encoding="utf-8")
    monkeypatch.setattr(canvas_manage, "_copy_canvas", lambda src, dst: None)
    monkeypatch.setattr(canvas_manage, "_append_canvas_index", lambda *a, **k: None)
    dst = canvas_manage.save_canvas(tmp_path, slug="demo", source="local")
    assert dst == local / "demo.canvas.tsx"


def test_append_index_writes_row(tmp_path: Path) -> None:
    _seed_lwp(tmp_path)
    local = tmp_path / ".local" / "canvases"
    local.mkdir(parents=True)
    index = local / "index.md"
    index.write_text("# idx\n\n| slug | t | a | n |\n", encoding="utf-8")
    canvas_manage._append_canvas_index(tmp_path, slug="fresh", agent="implementer")
    assert "fresh" in index.read_text(encoding="utf-8")
    canvas_manage._append_canvas_index(tmp_path, slug="fresh", agent=None)  # dedup


def test_append_index_no_file(tmp_path: Path) -> None:
    """Index append is a no-op when index file is absent."""
    _seed_lwp(tmp_path)
    canvas_manage._append_canvas_index(tmp_path, slug="x", agent=None)