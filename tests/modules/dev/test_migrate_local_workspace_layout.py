"""
File: test_migrate_local_workspace_layout.py
Path: tests/modules/dev/test_migrate_local_workspace_layout.py
Role: Tests for `.local/` layout migration maintainer script.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/dev/migrate_local_workspace_layout.py
Notes:
 - Uses temporary directories; does not modify kit root.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATE_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "dev" / "migrate_local_workspace_layout.py"


def _load_migrate(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    argv: list[str] | None = None,
):
    if argv is None:
        argv = ["migrate_local_workspace_layout.py"]
    monkeypatch.setattr(sys, "argv", argv)
    module_name = f"migrate_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MIGRATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "REPO", root)
    monkeypatch.setattr(module, "LOCAL", root / ".local")
    monkeypatch.setattr(module, "TEMPLATE", root / ".ai_infra" / "templates" / "local-workspace")
    return module


def _copy_template_tree(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    ui_src = REPO_ROOT / ".ai_infra" / "templates" / "local-workspace"
    ui_dst = root / ".ai_infra" / "templates" / "local-workspace"
    shutil.copytree(ui_src, ui_dst)
    pr_dst = root / ".ai_infra" / "scripts" / "pr"
    pr_dst.mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "local_workflow_paths.py",
        pr_dst / "local_workflow_paths.py",
    )
    return root


def test_main_moves_legacy_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_template_tree(tmp_path)
    local = root / ".local"
    legacy_plan = local / "index-and-planning" / "plan.md"
    legacy_plan.parent.mkdir(parents=True)
    legacy_plan.write_text("# legacy plan\n", encoding="utf-8")

    mod = _load_migrate(monkeypatch, root)
    code = mod.main()
    captured = capsys.readouterr()

    assert code == 0
    assert "dry_run=False" in captured.out
    assert "[MOVE]" in captured.out
    assert not legacy_plan.is_file()
    moved = local / "index-and-planning" / "current" / "plan.md"
    assert moved.is_file()
    assert "legacy plan" in moved.read_text(encoding="utf-8")


def test_main_dry_run_flag_prints_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_template_tree(tmp_path)
    local = root / ".local"
    legacy_plan = local / "index-and-planning" / "plan.md"
    legacy_plan.parent.mkdir(parents=True)
    legacy_plan.write_text("# legacy plan\n", encoding="utf-8")

    mod = _load_migrate(
        monkeypatch,
        root,
        ["migrate_local_workspace_layout.py", "--dry-run"],
    )
    code = mod.main()
    captured = capsys.readouterr()

    assert code == 0
    assert "dry_run=True" in captured.out
    assert legacy_plan.is_file()
    assert not (local / "index-and-planning" / "current" / "plan.md").exists()


def test_main_overwrites_stale_pages_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_template_tree(tmp_path)
    cfg = root / ".local" / "agents-control-center" / "config"
    cfg.mkdir(parents=True)
    stale = {
        "version": 1,
        "pages": [
            {"id": "workflow", "title": "Workflows", "file": "../../../docs/operations/workflow-complete.md"}
        ],
    }
    pages_path = cfg / "pages.json"
    pages_path.write_text(json.dumps(stale), encoding="utf-8")

    mod = _load_migrate(monkeypatch, root)
    code = mod.main()
    captured = capsys.readouterr()

    assert code == 0
    assert "[COPY+]" in captured.out and "pages.json" in captured.out
    data = json.loads(pages_path.read_text(encoding="utf-8"))
    ids = {page["id"] for page in data["pages"]}
    assert {"pr-review", "drift-audit", "ea-audit"}.issubset(ids)
    workflow = next(p for p in data["pages"] if p["id"] == "workflow")
    assert workflow["file"].startswith("../../../.ai_infra/docs/")


def test_pages_json_needs_artifact_tabs_detects_legacy_manifest(tmp_path: Path) -> None:
    pages_path = tmp_path / "pages.json"
    pages_path.write_text(
        json.dumps({"pages": [{"id": "plan", "title": "Plan", "file": "plan.md"}]}),
        encoding="utf-8",
    )
    spec = importlib.util.spec_from_file_location("migrate_mod", MIGRATE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._pages_json_needs_artifact_tabs(pages_path) is True


def test_pages_json_paths_stale_detects_docs_prefix(tmp_path: Path) -> None:
    pages_path = tmp_path / "pages.json"
    pages_path.write_text(
        json.dumps(
            {
                "pages": [
                    {
                        "id": "workflow",
                        "title": "Workflows",
                        "file": "../../../docs/operations/workflow-complete.md",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    spec = importlib.util.spec_from_file_location("migrate_mod2", MIGRATE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._pages_json_paths_stale(pages_path) is True


def test_main_detects_legacy_dashboard_without_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_template_tree(tmp_path)
    dash = root / ".local" / "agents-control-center" / "dashboards"
    dash.mkdir(parents=True)
    legacy_html = dash / "implementation-control-center.html"
    legacy_html.write_text("<html><body>legacy dashboard</body></html>", encoding="utf-8")

    mod = _load_migrate(monkeypatch, root)
    code = mod.main()
    captured = capsys.readouterr()

    assert code == 0
    assert "[BACKUP]" in captured.out
    assert "MANIFEST" in legacy_html.read_text(encoding="utf-8")
