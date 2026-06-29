"""
File: scaffold.py
Path: .ai_infra/scripts/install/scaffold.py
Role: Manifest-driven install of Cursor Agent Infrastructure into a target project.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - Makefile install-dry-run
Depends On:
 - .ai_infra/manifest.yaml
 - .ai_infra/bootstrap.py
Notes:
 - Default profile: .cursor, .agents, slim .ai_infra, .local exemplars, AGENTS stub.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ensure_paths_import = None
for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        _root = _candidate
        if str(_root / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_root / ".ai_infra"))
        from bootstrap import ensure_paths_import as _epi

        ensure_paths_import = _epi
        break
else:
    raise RuntimeError("kit root not found above scaffold.py")

assert ensure_paths_import is not None
KIT_ROOT = ensure_paths_import(__file__)

from paths import ai_infra_dir, kit_root, ui_local_workspace, user_settings_templates

MANIFEST_PATH = ai_infra_dir() / "manifest.yaml"
USER_SETTINGS_FILES = [
    "README.md",
    "github.collaboration.yaml",
    "mcp.agents.yaml",
]
EXEMPLAR_TRACKERS = [
    "session-pointer.md",
    "change-index.md",
    "plan.md",
    "work-tracker.md",
    "test-plan.md",
    "test-index.md",
]
ADAPTER_WALL_RULE = "provider-neutral-adapter-wall.mdc"
PREPARE_REL = Path(".ai_infra") / "scripts" / "pr" / "prepare.py"
KIT_TESTS_MARKER = Path("tests") / "modules" / "install" / "test_scaffold.py"
SMOKE_TEST_REL = Path("tests") / "modules" / "smoke" / "test_kit_installed.py"
SMOKE_TEST_BODY = '''"""
File: test_kit_installed.py
Path: tests/modules/smoke/test_kit_installed.py
Role: Smoke test that core kit paths exist after consumer install.
Used By:
 - pytest (consumer default scaffold)
Depends On:
 - scaffold minimal test layout
Notes:
 - Replaced when install uses --with-tests (kit dev only).
"""
from pathlib import Path


def test_core_layout_installed() -> None:
    assert Path(".cursor/agents/implementer.md").is_file()
    assert Path(".ai_infra/scripts/pr/prepare.py").is_file()
    assert Path(".local/index-and-planning/current/session-pointer.md").is_file()
'''


def _log(messages: list[str], line: str) -> None:
    messages.append(line)
    print(line)


def _load_manifest() -> dict[str, Any]:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "profiles" not in data:
        raise RuntimeError(f"invalid manifest: {MANIFEST_PATH}")
    return data


def _resolve_profile(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    profiles = manifest["profiles"]
    if name not in profiles:
        raise ValueError(f"unknown profile: {name}")
    raw = profiles[name]
    if "extends" in raw:
        base = _resolve_profile(manifest, raw["extends"])
        merged: dict[str, Any] = {
            "copy_dirs": list(base.get("copy_dirs", [])),
            "copy_ai_infra": list(base.get("copy_ai_infra", [])),
            "copy_files": list(base.get("copy_files", [])),
            "scaffold_local": base.get("scaffold_local", False),
            "agents_md": base.get("agents_md"),
            "mcp_json": base.get("mcp_json", False),
            "overlay_rules": base.get("overlay_rules"),
        }
        for key in ("copy_dirs", "copy_ai_infra", "copy_files"):
            merged[key] = merged[key] + list(raw.get(key, []))
        for key in ("scaffold_local", "agents_md", "mcp_json", "overlay_rules"):
            if key in raw:
                merged[key] = raw[key]
        return merged
    return raw


def _copy_tree(src: Path, dst: Path, dry_run: bool, log: list[str]) -> None:
    if not src.is_dir():
        raise FileNotFoundError(f"Missing source directory: {src}")
    if dry_run:
        _log(log, f"DRY-RUN copytree {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    _log(log, f"COPY {src} -> {dst}")


def _copy_file(src: Path, dst: Path, dry_run: bool, log: list[str]) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"Missing source file: {src}")
    if dry_run:
        _log(log, f"DRY-RUN copy {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    _log(log, f"COPY {src} -> {dst}")


def _scaffold_local(source: Path, target: Path, dry_run: bool, log: list[str]) -> None:
    ui_root = ui_local_workspace(source)
    exemplars = ui_root / "exemplars"
    pages_src = ui_root / "pages.json"
    current = target / ".local" / "index-and-planning" / "current"
    history = target / ".local" / "index-and-planning" / "history"
    pr_dir = target / ".local" / "workflow-artifacts" / "pr"
    acc_config = target / ".local" / "agents-control-center" / "config"

    for path in (current, history, pr_dir, acc_config):
        if dry_run:
            _log(log, f"DRY-RUN mkdir {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)

    for name in EXEMPLAR_TRACKERS:
        _copy_file(exemplars / name, current / name, dry_run, log)

    arch_stub = target / ".local" / "index-and-planning" / "current" / "architecture.md"
    if not arch_stub.exists() and not dry_run:
        arch_stub.write_text(
            "# Architecture\n\nAdd project architecture under `docs/architecture/`.\n",
            encoding="utf-8",
        )
        _log(log, f"WRITE {arch_stub}")

    if pages_src.is_file():
        _copy_file(pages_src, acc_config / "pages.json", dry_run, log)


def _scaffold_user_settings(source: Path, target: Path, dry_run: bool, log: list[str]) -> None:
    try:
        exemplars = user_settings_templates(source)
    except FileNotFoundError:
        _log(log, "SKIP user_settings (missing templates/user-settings/exemplars on source)")
        return
    dest_root = target / ".local" / "user_settings"
    if dry_run:
        _log(log, f"DRY-RUN mkdir {dest_root}")
    else:
        dest_root.mkdir(parents=True, exist_ok=True)
    for name in USER_SETTINGS_FILES:
        _copy_file(exemplars / name, dest_root / name, dry_run, log)


def _scaffold_minimal_tests(target: Path, dry_run: bool, log: list[str]) -> None:
    smoke_file = target / SMOKE_TEST_REL
    if dry_run:
        _log(log, f"DRY-RUN write minimal smoke {smoke_file}")
        return
    smoke_file.parent.mkdir(parents=True, exist_ok=True)
    smoke_file.write_text(SMOKE_TEST_BODY, encoding="utf-8")
    _log(log, f"WRITE {smoke_file}")


def _apply_overlay_rules(source: Path, target: Path, rel_overlay: str, dry_run: bool, log: list[str]) -> None:
    overlay = source / ".ai_infra" / rel_overlay
    if not overlay.is_dir():
        _log(log, f"SKIP overlay (missing {overlay})")
        return
    dest = target / ".cursor" / "rules"
    for mdc in overlay.glob("*.mdc"):
        _copy_file(mdc, dest / mdc.name, dry_run, log)


def _sanity_check(target: Path, log: list[str], *, with_tests: bool = False) -> list[str]:
    errors: list[str] = []
    agents = target / ".cursor" / "agents"
    rules = target / ".cursor" / "rules"
    if not (agents / "implementer.md").is_file():
        errors.append("missing .cursor/agents/implementer.md")
    if (rules / ADAPTER_WALL_RULE).is_file():
        errors.append(f"adapter wall must not be in core rules: {ADAPTER_WALL_RULE}")
    mapper = agents / "workflow-intelligence-mapper.md"
    if mapper.is_file():
        errors.append("workflow-intelligence-mapper should not ship in core")
    session = target / ".local" / "index-and-planning" / "current" / "session-pointer.md"
    if not session.is_file():
        errors.append("missing session-pointer.md")
    if (target / "examples").exists():
        errors.append("forbidden in slim install: examples")
    if not with_tests and (target / KIT_TESTS_MARKER).is_file():
        errors.append("forbidden in slim install: full kit tests tree")
    smoke = target / SMOKE_TEST_REL
    if not with_tests and not smoke.is_file():
        errors.append(f"missing consumer smoke test: {SMOKE_TEST_REL}")
    for err in errors:
        _log(log, f"CHECK FAIL: {err}")
    if not errors:
        _log(log, "CHECK PASS: core layout sanity")
    return errors


def _run_verify(target: Path, log: list[str]) -> int:
    py = target / ".venv" / "bin" / "python"
    if not py.is_file():
        py = Path(sys.executable)
    infra = target / ".ai_infra"
    cmds = [
        [str(py), str(infra / "scripts" / "pr" / "check_testing_artifacts.py")],
        [str(py), "-m", "pytest", "-q"],
        [str(py), str(infra / "scripts" / "architecture" / "check_governance_consistency.py")],
        [str(py), str(infra / "scripts" / "architecture" / "check_debrand.py")],
    ]
    for cmd in cmds:
        _log(log, f"RUN {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=target, check=False)
        if proc.returncode != 0:
            _log(log, f"VERIFY FAIL: exit {proc.returncode}")
            return proc.returncode
    _log(log, "VERIFY PASS: all gates green")
    return 0


def _create_venv(target: Path, dry_run: bool, log: list[str]) -> None:
    venv = target / ".venv"
    if venv.exists():
        _log(log, f"SKIP venv (exists): {venv}")
        return
    if dry_run:
        _log(log, f"DRY-RUN python -m venv {venv}")
        return
    subprocess.run([sys.executable, "-m", "venv", str(venv)], cwd=target, check=True)
    pip = venv / "bin" / "pip"
    subprocess.run([str(pip), "install", "-q", "pytest", "mcp>=1.2", "pyyaml"], check=True)
    req = target / "requirements-dev.txt"
    if req.is_file():
        subprocess.run([str(pip), "install", "-q", "-r", str(req)], check=True)
    mcp_req = target / "requirements-mcp.txt"
    if mcp_req.is_file():
        subprocess.run([str(pip), "install", "-q", "-r", str(mcp_req)], check=True)
    _log(log, f"VENV created: {venv}")


def scaffold(
    target: Path,
    source: Path,
    *,
    profile: str = "default",
    dry_run: bool = False,
    with_readme: bool = False,
    with_tests: bool = False,
    with_venv: bool = False,
    with_mcp_json: bool = False,
    verify: bool = False,
) -> list[str]:
    log: list[str] = []
    target = target.resolve()
    source = source.resolve()

    if target == source:
        raise ValueError("target must differ from source (do not scaffold into kit root)")

    if with_mcp_json and profile == "default":
        profile = "with_mcp"

    manifest = _load_manifest()
    spec = _resolve_profile(manifest, profile)
    ai_src = source / ".ai_infra"
    ai_dst = target / ".ai_infra"

    _log(log, f"SOURCE {source}")
    _log(log, f"TARGET {target}")
    _log(log, f"PROFILE {profile}")

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for entry in spec.get("copy_dirs", []):
        rel_src = entry["src"]
        rel_dst = entry["dst"]
        _copy_tree(source / rel_src, target / rel_dst, dry_run, log)

    for rel in spec.get("copy_ai_infra", []):
        _copy_tree(ai_src / rel, ai_dst / rel, dry_run, log)

    for rel in spec.get("copy_files", []):
        if rel == "requirements-mcp.txt":
            _copy_file(source / rel, target / rel, dry_run, log)
        else:
            _copy_file(ai_src / rel, ai_dst / rel, dry_run, log)

    kit_version = str(manifest.get("kit_version", "0.0.0"))
    kit_version_path = ai_dst / ".kit-version"
    if dry_run:
        _log(log, f"DRY-RUN write {kit_version_path} ({kit_version})")
    else:
        kit_version_path.parent.mkdir(parents=True, exist_ok=True)
        kit_version_path.write_text(f"{kit_version}\n", encoding="utf-8")
        _log(log, f"WRITE {kit_version_path} ({kit_version})")

    if spec.get("agents_md") == "stub":
        stub = ai_src / "templates" / "AGENTS.stub.md"
        _copy_file(stub, target / "AGENTS.md", dry_run, log)

    if with_readme:
        _copy_file(source / "README.md", target / "README.md", dry_run, log)

    if with_tests:
        _copy_tree(source / "tests", target / "tests", dry_run, log)
    else:
        _scaffold_minimal_tests(target, dry_run, log)

    if spec.get("scaffold_local"):
        _scaffold_local(source, target, dry_run, log)
        _scaffold_user_settings(source, target, dry_run, log)

    overlay = spec.get("overlay_rules")
    if overlay:
        _apply_overlay_rules(source, target, overlay, dry_run, log)

    if with_mcp_json or spec.get("mcp_json"):
        if dry_run:
            _log(log, "DRY-RUN merge .cursor/mcp.json from kit + user fragments")
        else:
            mcp_manage_path = source / ".ai_infra" / "install" / "cursor_workflow" / "mcp_manage.py"
            if mcp_manage_path.is_file():
                import importlib.util

                spec_mod = importlib.util.spec_from_file_location("mcp_manage", mcp_manage_path)
                assert spec_mod is not None and spec_mod.loader is not None
                mcp_manage = importlib.util.module_from_spec(spec_mod)
                spec_mod.loader.exec_module(mcp_manage)
                dest = mcp_manage.write_merged_mcp(target)
                mcp_manage.ensure_mcp_gitignore(target)
                _log(log, f"WRITE merged MCP config {dest}")
            else:
                example = target / ".cursor" / "mcp.json.kit.example"
                dest = target / ".cursor" / "mcp.json"
                if example.is_file():
                    _copy_file(example, dest, dry_run, log)

    if not dry_run:
        errors = _sanity_check(target, log, with_tests=with_tests)
        if errors:
            raise RuntimeError("scaffold sanity check failed: " + "; ".join(errors))

    if with_venv and not dry_run:
        _create_venv(target, dry_run, log)

    if verify and not dry_run:
        code = _run_verify(target, log)
        if code != 0:
            raise RuntimeError(f"verify failed with exit {code}")

    _log(log, "SCAFFOLD DONE")
    return log


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Cursor Agent Infrastructure into a target project.")
    parser.add_argument("--target", required=True, type=Path, help="Destination project directory")
    parser.add_argument(
        "--source",
        type=Path,
        default=KIT_ROOT,
        help="Kit root (default: auto-detect)",
    )
    parser.add_argument("--profile", default="default", help="Install profile from manifest.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Print actions only")
    parser.add_argument("--with-readme", action="store_true", help="Copy kit README.md")
    parser.add_argument("--with-tests", action="store_true", help="Copy tests/ (kit dev only)")
    parser.add_argument("--with-venv", action="store_true", help="Create .venv and install deps")
    parser.add_argument("--with-mcp-json", action="store_true", help="Use with_mcp profile + mcp.json")
    parser.add_argument("--verify", action="store_true", help="Run gates after install")
    args = parser.parse_args()

    try:
        scaffold(
            args.target,
            args.source,
            profile=args.profile,
            dry_run=args.dry_run,
            with_readme=args.with_readme,
            with_tests=args.with_tests,
            with_venv=args.with_venv,
            with_mcp_json=args.with_mcp_json,
            verify=args.verify,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
