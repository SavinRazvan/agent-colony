"""
File: sync_plugin_bundle.py
Path: .ai_infra/scripts/release/sync_plugin_bundle.py
Role: Build and verify Cursor Marketplace plugin bundle (plugin/ + payload/).
Used By:
 - Makefile sync-plugin / check-plugin
 - marketplace-publish.md
Depends On:
 - .ai_infra/manifest.yaml
 - .ai_infra/bootstrap.py
Notes:
 - plugin/ = Cursor-loaded agents, skills, rules (team-kit layout under plugin/).
 - payload/ = ADR-001 install source tree for workflow-activate.
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
PLUGIN_DIR = KIT_ROOT / "plugin"
PAYLOAD_DIR = KIT_ROOT / "payload"
ACTIVATE_SKILL_SRC = (
    ai_infra_dir() / "templates" / "plugin" / "skills" / "workflow-activate" / "SKILL.md"
)
CURSOR_WORKFLOW_SRC = KIT_ROOT / "cursor_workflow"
PAYLOAD_EXTRA_AI_INFRA = ("install/cursor_workflow", "scripts/install")
CONNECT_SKILL_SRC = (
    ai_infra_dir() / "templates" / "plugin" / "skills" / "connect-external-mcp" / "SKILL.md"
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


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        raise FileNotFoundError(f"missing source directory: {src}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_ignore_bundle_artifacts)


def _copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"missing source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _merge_maintainer_skills(plugin_skills: Path) -> None:
    maintainer = KIT_ROOT / ".agents" / "skills"
    if not maintainer.is_dir():
        return
    for skill_dir in sorted(maintainer.iterdir()):
        if not skill_dir.is_dir():
            continue
        dest = plugin_skills / skill_dir.name
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

    if not ACTIVATE_SKILL_SRC.is_file():
        raise FileNotFoundError(f"missing activation skill template: {ACTIVATE_SKILL_SRC}")
    activate_dest = plugin_dir / "skills" / "workflow-activate" / "SKILL.md"
    activate_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ACTIVATE_SKILL_SRC, activate_dest)

    if CONNECT_SKILL_SRC.is_file():
        connect_dest = plugin_dir / "skills" / "connect-external-mcp" / "SKILL.md"
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
        _copy_tree(ai_src / rel, ai_dst / rel)

    for rel in PAYLOAD_EXTRA_AI_INFRA:
        _copy_tree(ai_src / rel, ai_dst / rel)

    agents_stub = ai_src / "templates" / "AGENTS.stub.md"
    if agents_stub.is_file():
        _copy_file(agents_stub, ai_dst / "templates" / "AGENTS.stub.md")

    for rel in spec.get("copy_files", []):
        if rel == "requirements-mcp.txt":
            _copy_file(KIT_ROOT / rel, payload_dir / rel)
        else:
            _copy_file(ai_src / rel, ai_dst / rel)

    _copy_tree(KIT_ROOT / ".agents", payload_dir / ".agents")
    _copy_tree(plugin_dir / "agents", payload_dir / ".cursor" / "agents")
    _copy_tree(plugin_dir / "rules", payload_dir / ".cursor" / "rules")
    _copy_tree(plugin_dir / "skills", payload_dir / ".cursor" / "skills")

    mcp_kit = KIT_ROOT / ".cursor" / "mcp.json.kit.example"
    if mcp_kit.is_file() and profile == "with_mcp":
        _copy_file(mcp_kit, payload_dir / ".cursor" / "mcp.json.kit.example")

    _copy_tree(CURSOR_WORKFLOW_SRC, payload_dir / "cursor_workflow")


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
    if not PLUGIN_DIR.is_dir() or not PAYLOAD_DIR.is_dir():
        return ["plugin/ or payload/ missing — run: python .ai_infra/scripts/release/sync_plugin_bundle.py --sync"]

    with tempfile.TemporaryDirectory(prefix="mas-plugin-check-") as tmp:
        tmp_root = Path(tmp)
        expected_plugin = tmp_root / "plugin"
        expected_payload = tmp_root / "payload"
        sync_plugin_surface(expected_plugin)
        sync_payload(expected_payload, expected_plugin, profile)

        for label, expected_root, actual_root in (
            ("plugin", expected_plugin, PLUGIN_DIR),
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
        PLUGIN_DIR / "skills" / "connect-external-mcp" / "SKILL.md",
        PLUGIN_DIR / "agents" / "implementer.md",
        PAYLOAD_DIR / ".ai_infra" / "scripts" / "pr" / "prepare.py",
        PAYLOAD_DIR / ".ai_infra" / "scripts" / "install" / "scaffold.py",
        PAYLOAD_DIR / "cursor_workflow" / "__main__.py",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required bundle file: {path.relative_to(KIT_ROOT)}")

    return errors


def sync_all(profile: str = "with_mcp") -> None:
    sync_plugin_surface(PLUGIN_DIR)
    sync_payload(PAYLOAD_DIR, PLUGIN_DIR, profile)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync or verify MAS Workflow Kit plugin bundle.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify plugin/ and payload/ match sources (exit 1 on drift)",
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
    print(f"Synced plugin/ and payload/ (profile={args.profile}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
