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


def test_main_local_missing_returns_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_template_tree(tmp_path)
    mod = _load_migrate(monkeypatch, root)
    code = mod.main()
    captured = capsys.readouterr()
    assert code == 0
    assert ".local/ missing" in captured.out


def test_pages_json_paths_stale_returns_false_when_missing(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("migrate_mod3", MIGRATE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._pages_json_paths_stale(tmp_path / "missing-pages.json") is False


def test_pages_json_paths_stale_returns_false_for_current_paths(tmp_path: Path) -> None:
    pages_path = tmp_path / "pages.json"
    shutil.copy2(
        REPO_ROOT / ".ai_infra/templates/local-workspace/pages.json",
        pages_path,
    )
    spec = importlib.util.spec_from_file_location("migrate_mod4", MIGRATE_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._pages_json_paths_stale(pages_path) is False


def test_move_skips_when_destination_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _copy_template_tree(tmp_path)
    mod = _load_migrate(monkeypatch, root)
    src = root / ".local" / "plan.md"
    dst = root / ".local" / "current-plan.md"
    src.parent.mkdir(parents=True)
    src.write_text("src\n", encoding="utf-8")
    dst.write_text("dst\n", encoding="utf-8")
    log: list[str] = []
    mod._move(src, dst, False, log)
    assert any("SKIP" in line for line in log)


def test_copy_template_skips_missing_source_and_existing_dest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_template_tree(tmp_path)
    mod = _load_migrate(monkeypatch, root)
    log: list[str] = []
    mod._copy_template("does-not-exist.html", root / ".local" / "out.html", False, log)
    assert log == []
    dest = root / ".local" / "agents-control-center" / "dashboards" / "index.html"
    dest.parent.mkdir(parents=True)
    dest.write_text("existing\n", encoding="utf-8")
    mod._copy_template("index.html", dest, False, log)
    assert log == []


def test_copy_template_overwrite_skips_missing_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_template_tree(tmp_path)
    mod = _load_migrate(monkeypatch, root)
    log: list[str] = []
    mod._copy_template_overwrite("missing.js", root / ".local" / "out.js", False, log)
    assert log == []


def test_copy_artifact_readme_stubs_skip_missing_and_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_template_tree(tmp_path)
    mod = _load_migrate(monkeypatch, root)
    stubs = root / ".ai_infra/templates/local-workspace/artifact-stubs"
    bucket = "pr"
    readme = stubs / bucket / "README.md"
    readme.unlink()
    existing = root / ".local/workflow-artifacts/alignment/README.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("keep\n", encoding="utf-8")
    log: list[str] = []
    mod._copy_artifact_readme_stubs(False, log)
    assert existing.read_text(encoding="utf-8") == "keep\n"


def test_main_migrates_legacy_architecture_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_template_tree(tmp_path)
    arch_legacy = root / ".local/index-and-planning/architecture.md"
    arch_legacy.parent.mkdir(parents=True)
    arch_legacy.write_text("# legacy architecture\n", encoding="utf-8")
    mod = _load_migrate(monkeypatch, root)
    mod.main()
    snap = root / ".local/index-and-planning/history/architecture-legacy-snapshot.md"
    assert snap.is_file()
    assert "legacy architecture" in snap.read_text(encoding="utf-8")


def test_main_uses_copy_template_for_current_pages_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy_template_tree(tmp_path)
    cfg = root / ".local/agents-control-center/config"
    cfg.mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / ".ai_infra/templates/local-workspace/pages.json",
        cfg / "pages.json",
    )
    mod = _load_migrate(monkeypatch, root)
    code = mod.main()
    captured = capsys.readouterr()
    assert code == 0
    assert "[COPY+]" not in captured.out or "pages.json" not in captured.out


def test_bootstrap_raises_when_kit_root_missing(tmp_path: Path) -> None:
    fake = tmp_path / "orphan" / "migrate_local_workspace_layout.py"
    fake.parent.mkdir(parents=True)
    fake.write_text(MIGRATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("orphan_migrate", fake)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(RuntimeError, match="kit root not found"):
        spec.loader.exec_module(mod)


def test_bootstrap_inserts_ai_infra_when_missing_from_sys_path(monkeypatch: pytest.MonkeyPatch) -> None:
    kit_ai = str(REPO_ROOT / ".ai_infra")
    while kit_ai in sys.path:
        sys.path.remove(kit_ai)
    module_name = f"migrate_insert_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MIGRATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert kit_ai in sys.path
    assert hasattr(module, "main")


def test_main_guard_via_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.setattr(sys, "argv", ["migrate_local_workspace_layout.py", "--dry-run"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(MIGRATE_PATH), run_name="__main__")
    assert exc_info.value.code == 0
