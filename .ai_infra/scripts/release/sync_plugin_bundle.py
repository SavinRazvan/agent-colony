"""
File: sync_plugin_bundle.py
Path: .ai_infra/scripts/release/sync_plugin_bundle.py
Role: Build and verify Cursor Marketplace plugin bundle (repo-root agents/rules/skills + payload/).
Used By:
 - Makefile sync-plugin / check-plugin
 - marketplace-publish.md
Depends On:
 - .ai_infra/manifest.yaml
 - .ai_infra/bootstrap.py
Notes:
 - agents/, rules/, skills/ at repo root (siblings of .cursor-plugin/) = Cursor-loaded
   plugin surface, matching the official cursor/plugin-template convention exactly
   (no custom path fields in .cursor-plugin/plugin.json).
 - payload/ = ADR-001 install source tree for workflow-activate.
 - Both are generated from .cursor/ + .agents/skills/ but MUST be committed to git —
   Cursor Marketplace reads the repository tree directly, there is no build step.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        KIT_ROOT = ensure_paths_import(__file__)
        break
else:
    raise RuntimeError("kit root not found above sync_plugin_bundle.py")

from paths import ai_infra_dir

MANIFEST_PATH = ai_infra_dir() / "manifest.yaml"
# Plugin surface lives at repo root (agents/, rules/, skills/ siblings of
# .cursor-plugin/) — matches cursor/plugin-template convention exactly.
PLUGIN_DIR = KIT_ROOT
PLUGIN_COMPONENT_DIRS = ("agents", "rules", "skills")
PAYLOAD_DIR = KIT_ROOT / "payload"
ACTIVATE_SKILL_SRC = (
    ai_infra_dir() / "templates" / "plugin" / "skills" / "workflow-activate" / "SKILL.md"
)
CURSOR_WORKFLOW_SRC = KIT_ROOT / "cursor_workflow"
PAYLOAD_EXTRA_AI_INFRA = ("install/cursor_workflow", "scripts/install")
CONNECT_SKILL_SRC = (
    ai_infra_dir() / "templates" / "plugin" / "skills" / "mcp-connect" / "SKILL.md"
)
LICENSE_FILES = ("LICENSE", "NOTICE")
# Consumer MCP worksheets for /mcp-connect (examples only — never live mcp.json /
# mcp.user.json / mcp.registry.yaml with kit-dev secrets or local servers).
MCP_PAYLOAD_EXAMPLES = (
    "mcp.json.kit.example",
    "mcp.registry.yaml.example",
    "mcp.user.example.json",
    "MCP-CONFIG.md",
)
MCP_D_PAYLOAD_FILES = (
    "README.md",
    "user.example.json",
)

_SKIP_DIR_NAMES = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache"})
_SKIP_FILE_SUFFIXES = (".pyc", ".pyo")


def _ignore_bundle_artifacts(_dir: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in _SKIP_DIR_NAMES or name.endswith(_SKIP_FILE_SUFFIXES):
            ignored.add(name)
    return ignored


def _is_bundle_artifact(path: Path) -> bool:
    return any(part in _SKIP_DIR_NAMES for part in path.parts) or path.suffix in _SKIP_FILE_SUFFIXES


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
    if "extends" not in raw:
        return raw
    base = _resolve_profile(manifest, raw["extends"])
    merged: dict[str, Any] = {
        "copy_dirs": list(base.get("copy_dirs", [])),
        "copy_ai_infra": list(base.get("copy_ai_infra", [])),
        "copy_files": list(base.get("copy_files", [])),
    }
    for key in ("copy_dirs", "copy_ai_infra", "copy_files"):
        merged[key] = merged[key] + list(raw.get(key, []))
    return merged


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _copy_tree(src: Path, dst: Path, *, ignore: Any | None = None) -> None:
    if not src.is_dir():
        raise FileNotFoundError(f"missing source directory: {src}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=ignore or _ignore_bundle_artifacts)


def _load_consumer_bundle_paths() -> Any:
    arch = KIT_ROOT / ".ai_infra" / "scripts" / "architecture"
    arch_str = str(arch)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import consumer_bundle_paths

    return consumer_bundle_paths


def _copy_ai_infra_rel(ai_src: Path, ai_dst: Path, rel: str) -> None:
    src = ai_src / rel
    dst = ai_dst / rel
    cbp = _load_consumer_bundle_paths()
    if cbp.is_local_workspace_copy(rel):
        _copy_tree(src, dst, ignore=cbp.ignore_local_workspace_ci)
        return
    if cbp.is_operations_copy(rel):
        _copy_tree(src, dst, ignore=cbp.ignore_operations_maintainer)
        return
    _copy_tree(src, dst)


def _copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"missing source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _merge_maintainer_skills(plugin_skills: Path) -> None:
    """Add maintainer-only skills from .agents/skills without overwriting .cursor/skills."""
    maintainer = KIT_ROOT / ".agents" / "skills"
    if not maintainer.is_dir():
        return
    for skill_dir in sorted(maintainer.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = plugin_skills / skill_dir.name
        if dest.exists():
            continue
        _copy_tree(skill_dir, dest)


def sync_plugin_surface(plugin_dir: Path) -> None:
    agents_src = KIT_ROOT / ".cursor" / "agents"
    rules_src = KIT_ROOT / ".cursor" / "rules"
    skills_src = KIT_ROOT / ".cursor" / "skills"

    plugin_dir.mkdir(parents=True, exist_ok=True)
    _copy_tree(agents_src, plugin_dir / "agents")
    _copy_tree(rules_src, plugin_dir / "rules")
    _copy_tree(skills_src, plugin_dir / "skills")
    _merge_maintainer_skills(plugin_dir / "skills")

    activate_src = skills_src / "workflow-activate" / "SKILL.md"
    if not activate_src.is_file():
        activate_src = ACTIVATE_SKILL_SRC
    if not activate_src.is_file():
        raise FileNotFoundError(f"missing activation skill: {ACTIVATE_SKILL_SRC}")
    activate_dest = plugin_dir / "skills" / "workflow-activate" / "SKILL.md"
    if not activate_dest.parent.exists() or not activate_dest.is_file():
        activate_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(activate_src, activate_dest)

    connect_dest = plugin_dir / "skills" / "mcp-connect" / "SKILL.md"
    if not connect_dest.is_file() and CONNECT_SKILL_SRC.is_file():
        connect_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CONNECT_SKILL_SRC, connect_dest)


def sync_payload(payload_dir: Path, plugin_dir: Path, profile: str = "with_mcp") -> None:
    manifest = _load_manifest()
    spec = _resolve_profile(manifest, profile)
    ai_src = KIT_ROOT / ".ai_infra"
    ai_dst = payload_dir / ".ai_infra"

    if payload_dir.exists():
        shutil.rmtree(payload_dir)
    payload_dir.mkdir(parents=True)

    for rel in spec.get("copy_ai_infra", []):
        _copy_ai_infra_rel(ai_src, ai_dst, rel)

    for rel in PAYLOAD_EXTRA_AI_INFRA:
        _copy_tree(ai_src / rel, ai_dst / rel)

    agents_stub = ai_src / "templates" / "AGENTS.stub.md"
    if agents_stub.is_file():
        _copy_file(agents_stub, ai_dst / "templates" / "AGENTS.stub.md")

    for rel in spec.get("copy_files", []):
        if rel in {"requirements-mcp.txt", "requirements-dev.txt"}:
            _copy_file(KIT_ROOT / rel, payload_dir / rel)
        else:
            _copy_file(ai_src / rel, ai_dst / rel)

    _copy_tree(KIT_ROOT / ".agents", payload_dir / ".agents")
    _copy_tree(plugin_dir / "agents", payload_dir / ".cursor" / "agents")
    _copy_tree(plugin_dir / "rules", payload_dir / ".cursor" / "rules")
    # Consumer parity: canonical skills only under .cursor/skills; maintainer slash
    # skills live in .agents/skills. Repo-root skills/ merges both for Marketplace
    # loading — do not copy merged skills/ into payload or install --verify fails governance.
    _copy_tree(KIT_ROOT / ".cursor" / "skills", payload_dir / ".cursor" / "skills")

    if profile == "with_mcp":
        cursor_src = KIT_ROOT / ".cursor"
        cursor_dst = payload_dir / ".cursor"
        for name in MCP_PAYLOAD_EXAMPLES:
            src = cursor_src / name
            if src.is_file():
                _copy_file(src, cursor_dst / name)
        mcp_d_src = cursor_src / "mcp.d"
        if mcp_d_src.is_dir():
            mcp_d_dst = cursor_dst / "mcp.d"
            for name in MCP_D_PAYLOAD_FILES:
                src = mcp_d_src / name
                if src.is_file():
                    _copy_file(src, mcp_d_dst / name)

    _copy_tree(CURSOR_WORKFLOW_SRC, payload_dir / "cursor_workflow")

    for name in LICENSE_FILES:
        _copy_file(KIT_ROOT / name, payload_dir / name)


def _collect_files(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_file() and not _is_bundle_artifact(path):
            rel = path.relative_to(root).as_posix()
            out[rel] = _sha256(path)
    return out


def check_bundle(profile: str = "with_mcp") -> list[str]:
    errors: list[str] = []
    missing_component = any(
        not (PLUGIN_DIR / name).is_dir() for name in PLUGIN_COMPONENT_DIRS
    )
    if missing_component or not PAYLOAD_DIR.is_dir():
        return [
            "agents/, rules/, skills/, or payload/ missing — "
            "run: python .ai_infra/scripts/release/sync_plugin_bundle.py --sync"
        ]

    with tempfile.TemporaryDirectory(prefix="mas-plugin-check-") as tmp:
        tmp_root = Path(tmp)
        expected_plugin = tmp_root / "plugin"
        expected_payload = tmp_root / "payload"
        sync_plugin_surface(expected_plugin)
        sync_payload(expected_payload, expected_plugin, profile)

        component_pairs = tuple(
            (name, expected_plugin / name, PLUGIN_DIR / name) for name in PLUGIN_COMPONENT_DIRS
        )
        for label, expected_root, actual_root in (
            *component_pairs,
            ("payload", expected_payload, PAYLOAD_DIR),
        ):
            expected = _collect_files(expected_root)
            actual = _collect_files(actual_root)
            if expected != actual:
                missing = sorted(set(expected) - set(actual))
                extra = sorted(set(actual) - set(expected))
                changed = sorted(
                    rel for rel in expected if rel in actual and expected[rel] != actual[rel]
                )
                if missing:
                    errors.append(f"{label}: missing files: {missing[:8]}")
                if extra:
                    errors.append(f"{label}: extra files: {extra[:8]}")
                if changed:
                    errors.append(f"{label}: content drift: {changed[:8]}")

    required = [
        PLUGIN_DIR / "skills" / "workflow-activate" / "SKILL.md",
        PLUGIN_DIR / "skills" / "mcp-connect" / "SKILL.md",
        PLUGIN_DIR / "agents" / "implementer.md",
        PAYLOAD_DIR / ".ai_infra" / "scripts" / "pr" / "prepare.py",
        PAYLOAD_DIR / ".ai_infra" / "scripts" / "install" / "scaffold.py",
        PAYLOAD_DIR / "cursor_workflow" / "__main__.py",
        PAYLOAD_DIR / "LICENSE",
        PAYLOAD_DIR / "NOTICE",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required bundle file: {path.relative_to(KIT_ROOT)}")

    return errors


def sync_all(profile: str = "with_mcp") -> None:
    sync_plugin_surface(PLUGIN_DIR)
    sync_payload(PAYLOAD_DIR, PLUGIN_DIR, profile)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync or verify Agent Colony plugin bundle.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify agents/, rules/, skills/, and payload/ match sources (exit 1 on drift)",
    )
    parser.add_argument(
        "--profile",
        default="with_mcp",
        choices=("default", "with_mcp"),
        help="Manifest profile for payload/.ai_infra (default: with_mcp)",
    )
    args = parser.parse_args()

    if args.check:
        errors = check_bundle(args.profile)
        if errors:
            print("Plugin bundle check failed:")
            for err in errors:
                print(f" - {err}")
            return 1
        print("Plugin bundle check passed.")
        return 0

    sync_all(args.profile)
    print(f"Synced agents/, rules/, skills/, and payload/ (profile={args.profile}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
