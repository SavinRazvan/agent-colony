"""
File: test_sync_plugin_bundle_full.py
Path: tests/modules/release/test_sync_plugin_bundle_full.py
Role: Full-branch coverage for sync_plugin_bundle.py beyond the happy-path tests
      in test_sync_plugin_bundle.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/release/sync_plugin_bundle.py
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SYNC_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "release" / "sync_plugin_bundle.py"


def _load_sync():
    spec = importlib.util.spec_from_file_location("sync_plugin_bundle", SYNC_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_plugin_bundle"] = module
    spec.loader.exec_module(module)
    return module


def test_load_manifest_invalid_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    bad = tmp_path / "manifest.yaml"
    bad.write_text("no_profiles: true\n", encoding="utf-8")
    monkeypatch.setattr(mod, "MANIFEST_PATH", bad)
    with pytest.raises(RuntimeError, match="invalid manifest"):
        mod._load_manifest()


def test_resolve_profile_unknown_raises() -> None:
    mod = _load_sync()
    with pytest.raises(ValueError, match="unknown profile"):
        mod._resolve_profile({"profiles": {}}, "no-such-profile")


def test_copy_tree_missing_source_raises(tmp_path: Path) -> None:
    mod = _load_sync()
    with pytest.raises(FileNotFoundError, match="missing source directory"):
        mod._copy_tree(tmp_path / "nope", tmp_path / "dst")


def test_copy_file_missing_source_raises(tmp_path: Path) -> None:
    mod = _load_sync()
    with pytest.raises(FileNotFoundError, match="missing source file"):
        mod._copy_file(tmp_path / "nope.txt", tmp_path / "dst.txt")


def test_merge_maintainer_skills_missing_dir_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "KIT_ROOT", tmp_path)
    plugin_skills = tmp_path / "plugin" / "skills"
    plugin_skills.mkdir(parents=True)
    mod._merge_maintainer_skills(plugin_skills)
    assert list(plugin_skills.iterdir()) == []


def test_merge_maintainer_skills_skips_existing_dest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "KIT_ROOT", tmp_path)
    maintainer = tmp_path / ".agents" / "skills" / "my-skill"
    maintainer.mkdir(parents=True)
    (maintainer / "SKILL.md").write_text("original\n", encoding="utf-8")
    not_a_dir = tmp_path / ".agents" / "skills" / "stray-file.txt"
    not_a_dir.write_text("x\n", encoding="utf-8")

    plugin_skills = tmp_path / "plugin" / "skills"
    dest = plugin_skills / "my-skill"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("already-here\n", encoding="utf-8")

    mod._merge_maintainer_skills(plugin_skills)
    assert (dest / "SKILL.md").read_text(encoding="utf-8") == "already-here\n"


def test_sync_plugin_surface_falls_back_to_ai_infra_activate_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "KIT_ROOT", tmp_path)
    (tmp_path / ".cursor" / "agents").mkdir(parents=True)
    (tmp_path / ".cursor" / "rules").mkdir(parents=True)
    skills_src = tmp_path / ".cursor" / "skills"
    skills_src.mkdir(parents=True)
    fallback_skill = tmp_path / "fallback" / "SKILL.md"
    fallback_skill.parent.mkdir(parents=True)
    fallback_skill.write_text("fallback activate skill\n", encoding="utf-8")
    monkeypatch.setattr(mod, "ACTIVATE_SKILL_SRC", fallback_skill)
    monkeypatch.setattr(mod, "CONNECT_SKILL_SRC", tmp_path / "no-connect-skill.md")

    plugin_dir = tmp_path / "plugin"
    mod.sync_plugin_surface(plugin_dir)

    dest = plugin_dir / "skills" / "workflow-activate" / "SKILL.md"
    assert dest.read_text(encoding="utf-8") == "fallback activate skill\n"


def test_sync_plugin_surface_copies_connect_skill_from_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "KIT_ROOT", tmp_path)
    (tmp_path / ".cursor" / "agents").mkdir(parents=True)
    (tmp_path / ".cursor" / "rules").mkdir(parents=True)
    skills_src = tmp_path / ".cursor" / "skills"
    skills_src.mkdir(parents=True)
    activate_skill = skills_src / "workflow-activate" / "SKILL.md"
    activate_skill.parent.mkdir(parents=True)
    activate_skill.write_text("activate\n", encoding="utf-8")

    connect_fallback = tmp_path / "connect-fallback" / "SKILL.md"
    connect_fallback.parent.mkdir(parents=True)
    connect_fallback.write_text("connect skill content\n", encoding="utf-8")
    monkeypatch.setattr(mod, "CONNECT_SKILL_SRC", connect_fallback)

    plugin_dir = tmp_path / "plugin"
    mod.sync_plugin_surface(plugin_dir)

    dest = plugin_dir / "skills" / "connect-external-mcp" / "SKILL.md"
    assert dest.read_text(encoding="utf-8") == "connect skill content\n"


def test_sync_plugin_surface_missing_activate_skill_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "KIT_ROOT", tmp_path)
    (tmp_path / ".cursor" / "agents").mkdir(parents=True)
    (tmp_path / ".cursor" / "rules").mkdir(parents=True)
    (tmp_path / ".cursor" / "skills").mkdir(parents=True)
    monkeypatch.setattr(mod, "ACTIVATE_SKILL_SRC", tmp_path / "no-such-activate-skill.md")

    plugin_dir = tmp_path / "plugin"
    with pytest.raises(FileNotFoundError, match="missing activation skill"):
        mod.sync_plugin_surface(plugin_dir)


def test_sync_payload_removes_existing_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    stray = payload_dir / "stray-leftover.txt"
    stray.write_text("should be removed on re-sync\n", encoding="utf-8")

    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")
    assert not stray.exists()


def test_collect_files_missing_root_returns_empty(tmp_path: Path) -> None:
    mod = _load_sync()
    assert mod._collect_files(tmp_path / "does-not-exist") == {}


def test_check_bundle_missing_plugin_or_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "PLUGIN_DIR", tmp_path / "no-plugin")
    monkeypatch.setattr(mod, "PAYLOAD_DIR", tmp_path / "no-payload")
    errors = mod.check_bundle("with_mcp")
    assert len(errors) == 1
    assert "run: python" in errors[0]


def test_check_bundle_reports_missing_extra_and_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    monkeypatch.setattr(mod, "PLUGIN_DIR", plugin_dir)
    monkeypatch.setattr(mod, "PAYLOAD_DIR", payload_dir)

    victim = plugin_dir / "agents" / "implementer.md"
    original = victim.read_text(encoding="utf-8")
    victim.write_text(original + "\n# drift\n", encoding="utf-8")

    extra = plugin_dir / "agents" / "extra-agent.md"
    extra.write_text("extra\n", encoding="utf-8")

    missing = plugin_dir / "rules"
    for f in sorted(missing.glob("*.mdc"))[:1]:
        f.unlink()

    errors = mod.check_bundle("with_mcp")
    joined = "\n".join(errors)
    assert "content drift" in joined
    assert "extra files" in joined
    assert "missing files" in joined


def test_check_bundle_reports_missing_required_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    mod = _load_sync()
    fake_kit = tmp_path / "fake_kit"
    shutil.copytree(
        REPO_ROOT,
        fake_kit,
        symlinks=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "plugin", "payload", "tests", "node_modules", "__pycache__"
        ),
    )
    monkeypatch.setattr(mod, "KIT_ROOT", fake_kit)

    plugin_dir = fake_kit / "plugin"
    payload_dir = fake_kit / "payload"
    monkeypatch.setattr(mod, "PLUGIN_DIR", plugin_dir)
    monkeypatch.setattr(mod, "PAYLOAD_DIR", payload_dir)

    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")
    (payload_dir / "LICENSE").unlink()

    errors = mod.check_bundle("with_mcp")
    assert any("missing required bundle file" in e for e in errors)


def test_sync_all_builds_plugin_and_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    monkeypatch.setattr(mod, "PLUGIN_DIR", plugin_dir)
    monkeypatch.setattr(mod, "PAYLOAD_DIR", payload_dir)
    mod.sync_all("with_mcp")
    assert (plugin_dir / "agents" / "implementer.md").is_file()
    assert (payload_dir / "LICENSE").is_file()


def test_main_sync_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    monkeypatch.setattr(mod, "PLUGIN_DIR", plugin_dir)
    monkeypatch.setattr(mod, "PAYLOAD_DIR", payload_dir)
    monkeypatch.setattr(sys, "argv", ["sync_plugin_bundle.py", "--profile", "with_mcp"])
    assert mod.main() == 0
    assert (plugin_dir / "agents" / "implementer.md").is_file()


def test_main_check_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")
    monkeypatch.setattr(mod, "PLUGIN_DIR", plugin_dir)
    monkeypatch.setattr(mod, "PAYLOAD_DIR", payload_dir)
    monkeypatch.setattr(sys, "argv", ["sync_plugin_bundle.py", "--check", "--profile", "with_mcp"])
    code = mod.main()
    captured = capsys.readouterr()
    assert code == 0
    assert "Plugin bundle check passed." in captured.out


def test_main_check_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "PLUGIN_DIR", tmp_path / "no-plugin")
    monkeypatch.setattr(mod, "PAYLOAD_DIR", tmp_path / "no-payload")
    monkeypatch.setattr(sys, "argv", ["sync_plugin_bundle.py", "--check"])
    code = mod.main()
    captured = capsys.readouterr()
    assert code == 1
    assert "Plugin bundle check failed:" in captured.out


def test_main_guard_via_runpy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["sync_plugin_bundle.py", "--check"],
    )
    with pytest.raises(SystemExit):
        runpy.run_path(str(SYNC_PATH), run_name="__main__")


def test_module_raises_when_no_kit_root_found(monkeypatch: pytest.MonkeyPatch) -> None:
    real_is_file = Path.is_file

    def _fake_is_file(self: Path) -> bool:  # noqa: ANN001
        if self.name == "bootstrap.py":
            return False
        return real_is_file(self)

    monkeypatch.setattr(Path, "is_file", _fake_is_file)
    with pytest.raises(RuntimeError, match="kit root not found above sync_plugin_bundle.py"):
        runpy.run_path(str(SYNC_PATH), run_name="sync_plugin_bundle_reload_test")


def test_load_consumer_bundle_paths_inserts_architecture_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_sync()
    monkeypatch.setattr(mod, "KIT_ROOT", REPO_ROOT)
    arch_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "architecture")
    present = arch_dir in sys.path
    if present:
        sys.path.remove(arch_dir)
    try:
        cbp = mod._load_consumer_bundle_paths()
        assert cbp is not None
        assert arch_dir in sys.path
    finally:
        if arch_dir not in sys.path:
            sys.path.insert(0, arch_dir)
