"""
File: plan_manage.py
Path: .ai_infra/install/agent_colony/plan_manage.py
Role: Plan snapshot paths and copy logic (ADR-010).
Used By:
 - .ai_infra/install/agent_colony/plan_cli.py
Depends On:
 - cursor_host_paths
Notes:
 - Snapshots only; never mutates live plan.md or board SSOT.
"""

from __future__ import annotations

import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import cursor_host_paths
import yaml

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5


def _load_local_workflow_paths(root: Path):
    pr_scripts = root / ".ai_infra" / "scripts" / "pr"
    pr_str = str(pr_scripts)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import local_workflow_paths

    return local_workflow_paths


def validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        raise ValueError(f"invalid slug: {slug!r} (use kebab-case)")


def resolve_plan_source(root: Path, from_spec: str) -> Path:
    root = root.resolve()
    if from_spec == "plan.md":
        lwp = _load_local_workflow_paths(root)
        return root / lwp.PLANNING_CURRENT_DIR / "plan.md"
    if from_spec.startswith("cursor-plan:"):
        basename = from_spec.split(":", 1)[1].strip()
        if not basename.endswith(".plan.md"):
            basename = f"{basename}.plan.md"
        path = cursor_host_paths.cursor_plans_dir() / basename
        return path
    path = Path(from_spec)
    if not path.is_absolute():
        path = root / path
    return path


def snapshot_plan(
    root: Path,
    *,
    slug: str,
    from_spec: str = "plan.md",
    agent: str | None = None,
    board_item: str | None = None,
    parent_chat: str | None = None,
) -> tuple[Path, Path | None]:
    validate_slug(slug)
    root = root.resolve()
    lwp = _load_local_workflow_paths(root)
    lwp.ensure_local_artifact_tree(root=root)

    src = resolve_plan_source(root, from_spec)
    if not src.is_file():
        raise FileNotFoundError(f"plan source missing: {src}")

    today = date.today().isoformat()
    base = f"{today}-{slug}"
    dst = root / lwp.LOCAL_PLANS_DIR / f"{base}.plan.md"
    if dst.is_file():
        stamp = datetime.now(timezone.utc).strftime("%H%M%S")
        base = f"{today}-{slug}-{stamp}"
        dst = root / lwp.LOCAL_PLANS_DIR / f"{base}.plan.md"

    shutil.copy2(src, dst)

    meta_path: Path | None = None
    meta = {
        "slug": slug,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(src),
        "agent": agent,
        "board_item": board_item,
        "parent_chat": parent_chat,
    }
    meta_path = dst.parent / f"{base}.meta.yaml"
    meta_path.write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")

    _append_plan_index(root, snapshot=base, slug=slug, agent=agent, board_item=board_item, source=from_spec)
    return dst, meta_path


def list_snapshots(root: Path) -> list[dict[str, Any]]:
    root = root.resolve()
    lwp = _load_local_workflow_paths(root)
    plans_dir = root / lwp.LOCAL_PLANS_DIR
    if not plans_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(plans_dir.glob("*.plan.md")):
        # Snapshot files are `<base>.plan.md`; meta is sibling `<base>.meta.yaml`
        # (not Path.with_suffix(".meta.yaml"), which yields `<base>.plan.meta.yaml`).
        meta_path = path.parent / f"{path.name.removesuffix('.plan.md')}.meta.yaml"
        meta: dict[str, Any] = {}
        if meta_path.is_file():
            loaded = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                meta = loaded
        rows.append(
            {
                "file": path.name,
                "slug": meta.get("slug", canvas_base_from_plan(path.name)),
                "agent": meta.get("agent"),
                "board_item": meta.get("board_item"),
                "source": meta.get("source"),
            }
        )
    return rows


def canvas_base_from_plan(filename: str) -> str:
    name = filename.removesuffix(".plan.md")
    parts = name.split("-", 3)
    if len(parts) >= 4 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
        return "-".join(parts[3:])
    return name


def _snapshot_slug(path: Path) -> str:
    meta_path = path.parent / f"{path.name.removesuffix('.plan.md')}.meta.yaml"
    if meta_path.is_file():
        loaded = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict) and loaded.get("slug"):
            return str(loaded["slug"])
    return canvas_base_from_plan(path.name)


def find_latest_snapshot(root: Path, slug: str) -> Path:
    """Return the newest `.local/plans` snapshot matching *slug* (mtime)."""
    validate_slug(slug)
    root = root.resolve()
    lwp = _load_local_workflow_paths(root)
    plans_dir = root / lwp.LOCAL_PLANS_DIR
    if not plans_dir.is_dir():
        raise FileNotFoundError(f"no plan snapshot for slug {slug!r}")

    matches: list[Path] = []
    for path in plans_dir.glob("*.plan.md"):
        if _snapshot_slug(path) == slug:
            matches.append(path)
    if not matches:
        raise FileNotFoundError(f"no plan snapshot for slug {slug!r}")

    return max(matches, key=lambda p: p.stat().st_mtime)


def open_plan(root: Path, *, slug: str, force: bool = False) -> Path:
    """Copy latest local snapshot to ``~/.cursor/plans/<slug>.plan.md`` (Build bridge)."""
    validate_slug(slug)
    src = find_latest_snapshot(root, slug)
    dest = cursor_host_paths.cursor_plans_dir() / f"{slug}.plan.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and not force:
        raise ValueError(f"exists; pass --force ({dest})")
    shutil.copy2(src, dest)
    return dest


def _append_plan_index(
    root: Path,
    *,
    snapshot: str,
    slug: str,
    agent: str | None,
    board_item: str | None,
    source: str,
) -> None:
    lwp = _load_local_workflow_paths(root)
    index_path = root / lwp.LOCAL_PLANS_INDEX
    if not index_path.is_file():
        return
    row = f"| {snapshot}.plan.md | {slug} | {agent or '—'} | {board_item or '—'} | {source} |"
    text = index_path.read_text(encoding="utf-8")
    if snapshot in text:
        return
    index_path.write_text(text.rstrip() + "\n" + row + "\n", encoding="utf-8")
