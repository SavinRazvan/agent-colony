"""
File: test_scaffold_full.py
Path: tests/modules/install/test_scaffold_full.py
Role: Full-branch coverage for scaffold.py beyond the happy-path in test_scaffold.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/scaffold.py
"""

from __future__ import annotations

import importlib.util
import runpy
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLD_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"


def _load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold", SCAFFOLD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_inserts_arch_scripts_when_absent_from_sys_path() -> None:
    """Force the ARCH_SCRIPTS sys.path.insert branch (scaffold.py module load guard).

    Other test modules (e.g. tests/modules/architecture_scripts/*) insert the same
    architecture/ dir into sys.path at collection time, which — depending on pytest's
    collection order — can make the `if str(ARCH_SCRIPTS) not in sys.path` check in
    scaffold.py always False across a full run, leaving the insert call itself
    uncovered. Dedupe all copies before loading so the branch executes deterministically,
    then restore sys.path so we don't affect other tests.
    """
    arch_scripts = str(REPO_ROOT / ".ai_infra" / "scripts" / "architecture")
    original_path = list(sys.path)
    while arch_scripts in sys.path:
        sys.path.remove(arch_scripts)
    try:
        assert arch_scripts not in sys.path
        _load_scaffold()
        assert arch_scripts in sys.path
    finally:
        sys.path[:] = original_path


def test_load_manifest_invalid_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    bad = tmp_path / "manifest.yaml"
    bad.write_text("not_a_profiles_key: true\n", encoding="utf-8")
    monkeypatch.setattr(mod, "MANIFEST_PATH", bad)
    with pytest.raises(RuntimeError, match="invalid manifest"):
        mod._load_manifest()


def test_resolve_profile_unknown_raises() -> None:
    mod = _load_scaffold()
    with pytest.raises(ValueError, match="unknown profile"):
        mod._resolve_profile({"profiles": {}}, "no-such-profile")


def test_copy_tree_missing_source_raises(tmp_path: Path) -> None:
    mod = _load_scaffold()
    with pytest.raises(FileNotFoundError, match="Missing source directory"):
        mod._copy_tree(tmp_path / "nope", tmp_path / "dst", False, [])


def test_copy_file_missing_source_raises(tmp_path: Path) -> None:
    mod = _load_scaffold()
    with pytest.raises(FileNotFoundError, match="Missing source file"):
        mod._copy_file(tmp_path / "nope.txt", tmp_path / "dst.txt", False, [])


def test_copy_file_if_missing_missing_source_raises(tmp_path: Path) -> None:
    mod = _load_scaffold()
    with pytest.raises(FileNotFoundError, match="Missing source file"):
        mod._copy_file_if_missing(tmp_path / "nope.txt", tmp_path / "dst.txt", False, [])


def test_scaffold_artifact_readme_stubs_skips_missing_bucket(tmp_path: Path) -> None:
    mod = _load_scaffold()
    ui_root = tmp_path / "ui"
    stubs = ui_root / "artifact-stubs" / "known"
    stubs.mkdir(parents=True)
    (stubs / "README.md").write_text("hi\n", encoding="utf-8")
    target = tmp_path / "target"
    log: list[str] = []
    mod._scaffold_artifact_readme_stubs(ui_root, target, False, log, ("known", "missing-bucket"))
    assert (target / ".local" / "workflow-artifacts" / "known" / "README.md").is_file()
    assert not (target / ".local" / "workflow-artifacts" / "missing-bucket").exists()


def test_scaffold_user_settings_missing_templates_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_scaffold()

    def _raise(_source: Path) -> Path:
        raise FileNotFoundError("no exemplars")

    monkeypatch.setattr(mod, "user_settings_templates", _raise)
    log: list[str] = []
    mod._scaffold_user_settings(REPO_ROOT, tmp_path / "target", False, log)
    assert any("SKIP user_settings" in line for line in log)


def test_apply_overlay_rules_missing_overlay_skips(tmp_path: Path) -> None:
    mod = _load_scaffold()
    log: list[str] = []
    mod._apply_overlay_rules(tmp_path, tmp_path / "target", "no-such-overlay", False, log)
    assert any("SKIP overlay" in line for line in log)


def test_apply_overlay_rules_copies_mdc_files(tmp_path: Path) -> None:
    mod = _load_scaffold()
    overlay_dir = tmp_path / ".ai_infra" / "my-overlay"
    overlay_dir.mkdir(parents=True)
    (overlay_dir / "one.mdc").write_text("---\n---\nrule\n", encoding="utf-8")
    target = tmp_path / "target"
    log: list[str] = []
    mod._apply_overlay_rules(tmp_path, target, "my-overlay", False, log)
    assert (target / ".cursor" / "rules" / "one.mdc").is_file()


def test_sanity_check_reports_all_failure_branches(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    (target / ".cursor" / "rules").mkdir(parents=True)
    (target / ".cursor" / "rules" / mod.ADAPTER_WALL_RULE).write_text("x\n", encoding="utf-8")
    (target / ".cursor" / "agents").mkdir(parents=True, exist_ok=True)
    (target / ".cursor" / "agents" / "workflow-intelligence-mapper.md").write_text(
        "x\n", encoding="utf-8"
    )
    (target / "examples").mkdir(parents=True)
    log: list[str] = []
    errors = mod._sanity_check(target, log, with_tests=False)
    assert any("implementer.md" in e for e in errors)
    assert any("adapter wall" in e for e in errors)
    assert any("workflow-intelligence-mapper" in e for e in errors)
    assert any("session-pointer.md" in e for e in errors)
    assert any("examples" in e for e in errors)
    assert any("CHECK FAIL" in line for line in log)


def test_run_verify_uses_sys_executable_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    (target / ".ai_infra" / "scripts" / "pr").mkdir(parents=True)
    (target / ".ai_infra" / "scripts" / "pr" / "check_testing_artifacts.py").write_text(
        "import sys\nsys.exit(0)\n", encoding="utf-8"
    )
    (target / ".ai_infra" / "scripts" / "architecture").mkdir(parents=True)
    for name in ("check_governance_consistency.py", "check_debrand.py"):
        (target / ".ai_infra" / "scripts" / "architecture" / name).write_text(
            "import sys\nsys.exit(0)\n", encoding="utf-8"
        )
    log: list[str] = []
    monkeypatch.chdir(target)
    calls: list[list[str]] = []

    def _fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)
    code = mod._run_verify(target, log)
    assert code == 0
    assert calls[0][0] == sys.executable


def test_run_verify_returns_first_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    target.mkdir(parents=True)
    log: list[str] = []

    def _fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)
    code = mod._run_verify(target, log)
    assert code == 7
    assert any("VERIFY FAIL" in line for line in log)


def test_create_venv_skips_when_exists(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    (target / ".venv").mkdir(parents=True)
    log: list[str] = []
    mod._create_venv(target, False, log)
    assert any("SKIP venv" in line for line in log)


def test_create_venv_dry_run(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    target.mkdir(parents=True)
    log: list[str] = []
    mod._create_venv(target, True, log)
    assert any("DRY-RUN python -m venv" in line for line in log)


def test_create_venv_installs_requirements(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    target.mkdir(parents=True)
    (target / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")
    (target / "requirements-mcp.txt").write_text("mcp\n", encoding="utf-8")
    log: list[str] = []
    calls: list[list[str]] = []

    def _fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
        calls.append(list(cmd))
        if cmd[:2] == [sys.executable, "-m"] and "venv" in cmd:
            (target / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)
    mod._create_venv(target, False, log)
    assert any("requirements-dev.txt" in " ".join(c) for c in calls)
    assert any("requirements-mcp.txt" in " ".join(c) for c in calls)
    assert any("VENV created" in line for line in log)


def test_scaffold_with_readme_copies_readme(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT, with_readme=True)
    assert (target / "README.md").is_file()


def test_scaffold_with_mcp_json_uses_mcp_manage(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT, with_mcp_json=True)
    assert (target / ".cursor" / "mcp.json").is_file()


def test_scaffold_with_mcp_json_fallback_to_example(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_scaffold()
    fake_source = tmp_path / "fake_source"
    shutil.copytree(REPO_ROOT, fake_source, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    mcp_manage = fake_source / ".ai_infra" / "install" / "cursor_workflow" / "mcp_manage.py"
    mcp_manage.unlink()

    target = tmp_path / "project"
    mod.scaffold(target, fake_source, with_mcp_json=True)
    assert (target / ".cursor" / "mcp.json").is_file()


def test_scaffold_raises_on_sanity_check_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"

    def _fake_sanity(_target: Path, _log: list[str], *, with_tests: bool = False) -> list[str]:
        return ["synthetic failure"]

    monkeypatch.setattr(mod, "_sanity_check", _fake_sanity)
    with pytest.raises(RuntimeError, match="scaffold sanity check failed"):
        mod.scaffold(target, REPO_ROOT)


def test_scaffold_raises_when_verify_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"

    monkeypatch.setattr(mod, "_run_verify", lambda _target, _log: 3)
    with pytest.raises(RuntimeError, match="verify failed"):
        mod.scaffold(target, REPO_ROOT, verify=True)


def test_scaffold_applies_overlay_rules_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_scaffold()
    manifest = mod._load_manifest()
    manifest["profiles"]["default"]["overlay_rules"] = "templates/rules-overlay-test"
    monkeypatch.setattr(mod, "_load_manifest", lambda: manifest)

    overlay_dir = REPO_ROOT / ".ai_infra" / "templates" / "rules-overlay-test"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / "sample.mdc").write_text("---\n---\nsample\n", encoding="utf-8")
    try:
        target = tmp_path / "project"
        mod.scaffold(target, REPO_ROOT)
        assert (target / ".cursor" / "rules" / "sample.mdc").is_file()
    finally:
        shutil.rmtree(overlay_dir, ignore_errors=True)


def test_scaffold_dry_run_with_mcp_json_logs_merge(tmp_path: Path) -> None:
    mod = _load_scaffold()
    log = mod.scaffold(tmp_path / "out", REPO_ROOT, dry_run=True, with_mcp_json=True)
    assert any("DRY-RUN merge .cursor/mcp.json" in line for line in log)


def test_scaffold_with_venv_invokes_create_venv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    calls: list[Path] = []

    def _fake_create_venv(target: Path, dry_run: bool, log: list[str]) -> None:
        calls.append(target)

    monkeypatch.setattr(mod, "_create_venv", _fake_create_venv)
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT, with_venv=True)
    assert calls == [target]


def test_main_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    monkeypatch.setattr(
        sys,
        "argv",
        ["scaffold.py", "--target", str(target), "--source", str(REPO_ROOT)],
    )
    assert mod.main() == 0


def test_main_reports_error_and_returns_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_scaffold()
    monkeypatch.setattr(
        sys,
        "argv",
        ["scaffold.py", "--target", str(REPO_ROOT), "--source", str(REPO_ROOT)],
    )
    assert mod.main() == 1


def test_scaffold_module_raises_when_no_kit_root_found(monkeypatch: pytest.MonkeyPatch) -> None:
    real_is_file = Path.is_file

    def _fake_is_file(self: Path) -> bool:  # noqa: ANN001
        if self.name == "bootstrap.py":
            return False
        return real_is_file(self)

    monkeypatch.setattr(Path, "is_file", _fake_is_file)
    sys.modules.pop("scaffold", None)
    with pytest.raises(RuntimeError, match="kit root not found above scaffold.py"):
        runpy.run_path(str(SCAFFOLD_PATH), run_name="scaffold_reload_test")


def test_main_guard_via_runpy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "project"
    monkeypatch.setattr(
        sys,
        "argv",
        ["scaffold.py", "--target", str(target), "--source", str(REPO_ROOT)],
    )
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(SCAFFOLD_PATH), run_name="__main__")
    assert exc_info.value.code == 0
