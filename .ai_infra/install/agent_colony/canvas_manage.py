"""
File: canvas_manage.py
Path: .ai_infra/install/agent_colony/canvas_manage.py
Role: Canvas tier paths, list/sync/save, doctor drift detection (ADR-010).
Used By:
 - .ai_infra/install/agent_colony/canvas_cli.py
Depends On:
 - cursor_host_paths
Notes:
 - Repo canvases/ is git SSOT; Cursor managed path is render bridge only.
"""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import cursor_host_paths

CANVAS_SUFFIX = ".canvas.tsx"
CANVAS_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5

Tier = Literal["repo", "managed", "local", "all"]
SourceTier = Literal["repo", "local"]


def _load_local_workflow_paths(root: Path):
    pr_scripts = root / ".ai_infra" / "scripts" / "pr"
    pr_str = str(pr_scripts)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import local_workflow_paths

    return local_workflow_paths


def canvas_filename(base: str) -> str:
    if not CANVAS_NAME_RE.match(base):
        raise ValueError(f"invalid canvas base name: {base!r} (use kebab-case)")
    return f"{base}{CANVAS_SUFFIX}"


def list_canvases_in_dir(directory: Path | None) -> list[str]:
    if directory is None or not directory.is_dir():
        return []
    return sorted(p.name for p in directory.glob(f"*{CANVAS_SUFFIX}") if p.is_file())


def canvas_base(name: str) -> str:
    if name.endswith(CANVAS_SUFFIX):
        return name[: -len(CANVAS_SUFFIX)]
    return name


def tier_dir(root: Path, tier: SourceTier | Literal["managed"]) -> Path | None:
    lwp = _load_local_workflow_paths(root)
    if tier == "repo":
        path = root / lwp.REPO_CANVASES_DIR
        return path if path.is_dir() else None
    if tier == "local":
        path = root / lwp.LOCAL_CANVASES_DIR
        return path if path.is_dir() else None
    return cursor_host_paths.cursor_canvases_dir(root)


def list_by_tier(root: Path, tier: Tier) -> dict[str, list[str]]:
    tiers: dict[str, list[str]] = {}
    if tier in ("repo", "all"):
        tiers["repo"] = list_canvases_in_dir(tier_dir(root, "repo"))
    if tier in ("managed", "all"):
        tiers["managed"] = list_canvases_in_dir(tier_dir(root, "managed"))
    if tier in ("local", "all"):
        tiers["local"] = list_canvases_in_dir(tier_dir(root, "local"))
    return tiers


def validate_canvas_source(text: str) -> list[str]:
    warnings: list[str] = []
    if "export default function" not in text:
        if re.search(r"export\s+default\s+\w+\s*;", text):
            warnings.append(
                "uses separate `export default Name` — prefer `export default function …()` "
                "for Cursor canvas indexing"
            )
        else:
            warnings.append("missing `export default function` export")
    return warnings


def build_doctor_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    by_tier = list_by_tier(root, "all")
    repo_set = {canvas_base(n) for n in by_tier.get("repo", [])}
    managed_set = {canvas_base(n) for n in by_tier.get("managed", [])}
    local_set = {canvas_base(n) for n in by_tier.get("local", [])}

    repo_dir = tier_dir(root, "repo")
    managed_dir = tier_dir(root, "managed")
    stale: list[str] = []
    for base in sorted(repo_set & managed_set):
        assert repo_dir is not None and managed_dir is not None
        repo_file = repo_dir / canvas_filename(base)
        managed_file = managed_dir / canvas_filename(base)
        if repo_file.stat().st_mtime > managed_file.stat().st_mtime:
            stale.append(base)

    return {
        "root": str(root),
        "repo_dir": str(repo_dir) if repo_dir else None,
        "managed_dir": str(managed_dir) if managed_dir else None,
        "local_dir": str(tier_dir(root, "local")),
        "repo": by_tier.get("repo", []),
        "managed": by_tier.get("managed", []),
        "local": by_tier.get("local", []),
        "repo_not_managed": sorted(repo_set - managed_set),
        "managed_not_repo": sorted(managed_set - repo_set),
        "stale_managed": stale,
        "local_only": sorted(local_set - repo_set - managed_set),
    }


def format_doctor_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Canvas doctor",
        "",
        f"- root: `{report['root']}`",
        f"- repo: `{report['repo_dir'] or '(missing)'}`",
        f"- managed: `{report['managed_dir'] or '(not found)'}`",
        f"- local: `{report['local_dir'] or '(missing)'}`",
        "",
        "## Counts",
        "",
        f"- repo: {len(report['repo'])}",
        f"- managed: {len(report['managed'])}",
        f"- local: {len(report['local'])}",
        "",
        "## Drift",
        "",
        f"- repo not in managed: {', '.join(report['repo_not_managed']) or '(none)'}",
        f"- managed not in repo: {', '.join(report['managed_not_repo']) or '(none)'}",
        f"- stale managed (repo newer): {', '.join(report['stale_managed']) or '(none)'}",
        f"- local-only slugs: {', '.join(report['local_only']) or '(none)'}",
        "",
    ]
    return "\n".join(lines)


def _copy_canvas(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sync_canvas(
    root: Path,
    *,
    name: str | None = None,
    missing: bool = False,
    sync_all: bool = False,
    force: bool = False,
    source: SourceTier = "repo",
) -> list[str]:
    root = root.resolve()
    src_dir = tier_dir(root, source)
    dst_dir = tier_dir(root, "managed")
    if src_dir is None:
        raise FileNotFoundError(f"source tier {source!r} directory missing")
    if dst_dir is None:
        project = cursor_host_paths.cursor_project_dir(root)
        if project is None:
            raise FileNotFoundError("Cursor managed project dir not found")
        dst_dir = project / "canvases"
        dst_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    if sync_all:
        if not force:
            raise ValueError("sync --all requires --force")
        for filename in list_canvases_in_dir(src_dir):
            _copy_canvas(src_dir / filename, dst_dir / filename)
            copied.append(filename)
        return copied

    if missing:
        for filename in list_canvases_in_dir(src_dir):
            dst = dst_dir / filename
            if not dst.is_file():
                _copy_canvas(src_dir / filename, dst)
                copied.append(filename)
        return copied

    if not name:
        raise ValueError("pass --name, --missing, or --all")
    filename = canvas_filename(name)
    src = src_dir / filename
    if not src.is_file():
        raise FileNotFoundError(f"missing source canvas: {src}")
    _copy_canvas(src, dst_dir / filename)
    copied.append(filename)
    return copied


def save_canvas(
    root: Path,
    *,
    slug: str,
    source: Literal["managed", "repo", "local"] = "managed",
    agent: str | None = None,
) -> Path:
    root = root.resolve()
    lwp = _load_local_workflow_paths(root)
    lwp.ensure_local_artifact_tree(root=root)

    if source == "managed":
        src_dir = tier_dir(root, "managed")
    elif source == "repo":
        src_dir = tier_dir(root, "repo")
    else:
        src_dir = tier_dir(root, "local")
    if src_dir is None:
        raise FileNotFoundError(f"source tier {source!r} directory missing")

    filename = canvas_filename(slug)
    src = src_dir / filename
    if not src.is_file():
        raise FileNotFoundError(f"missing canvas to save: {src}")

    dst = root / lwp.LOCAL_CANVASES_DIR / filename
    _copy_canvas(src, dst)
    _append_canvas_index(root, slug=slug, agent=agent)
    return dst


def _append_canvas_index(root: Path, *, slug: str, agent: str | None) -> None:
    lwp = _load_local_workflow_paths(root)
    index_path = root / lwp.LOCAL_CANVASES_INDEX
    if not index_path.is_file():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    agent_col = agent or "—"
    row = f"| {slug} | {stamp} | {agent_col} | saved via canvas save |"
    text = index_path.read_text(encoding="utf-8")
    if slug in text:
        return
    index_path.write_text(text.rstrip() + "\n" + row + "\n", encoding="utf-8")
