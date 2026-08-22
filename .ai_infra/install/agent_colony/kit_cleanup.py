"""
File: kit_cleanup.py
Path: .ai_infra/install/agent_colony/kit_cleanup.py
Role: Pre/post consumer kit update cleanup — runtime artifacts and orphan kit files.
Used By:
 - .ai_infra/install/agent_colony/update_cli.py
Depends On:
 - .ai_infra/install/agent_colony/update_cli.py (scan_kit_agent_deltas — lazy)
Notes:
 - Orphans = kit-managed paths present in workspace but absent from payload source.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

_RUNTIME_ROOTS = (".ai_infra", "agent_colony")
_PYCACHE_NAME = "__pycache__"
_PYC_SUFFIXES = (".pyc", ".pyo")


@dataclass(frozen=True)
class CleanSummary:
    runtime_dirs: int = 0
    runtime_files: int = 0
    orphans_removed: int = 0


def _kit_managed_roots(target: Path) -> list[Path]:
    roots: list[Path] = []
    for name in _RUNTIME_ROOTS:
        path = target / name
        if path.is_dir():
            roots.append(path)
    return roots


def clean_runtime_artifacts(target: Path) -> CleanSummary:
    """Remove __pycache__ dirs and *.pyc/*.pyo under kit-managed trees."""
    runtime_dirs = 0
    runtime_files = 0
    for root in _kit_managed_roots(target):
        for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir() and path.name == _PYCACHE_NAME:
                shutil.rmtree(path, ignore_errors=True)
                runtime_dirs += 1
                continue
            if path.is_file() and path.suffix in _PYC_SUFFIXES:
                try:
                    path.unlink()
                    runtime_files += 1
                except OSError:
                    pass
    return CleanSummary(runtime_dirs=runtime_dirs, runtime_files=runtime_files)


def list_kit_orphan_relpaths(target: Path, source: Path) -> list[str]:
    """Return workspace-relative paths that are kit-managed orphans (not in payload)."""
    from update_cli import scan_kit_agent_deltas

    _failures, warnings = scan_kit_agent_deltas(target, source)
    del _failures
    orphans: list[str] = []
    for entry in warnings:
        if " (extra in workspace; not in payload)" in entry:
            rel = entry.split(" (extra in workspace", 1)[0]
            orphans.append(rel)
    return orphans


def prune_kit_orphans(
    target: Path, source: Path, *, dry_run: bool = False
) -> CleanSummary:
    """Delete kit-managed orphan files (target-only, not in payload)."""
    removed = 0
    for rel in list_kit_orphan_relpaths(target, source):
        path = target / rel
        if not path.is_file():
            continue
        if dry_run:
            print(f"CLEAN dry-run remove {path}")
            removed += 1
            continue
        try:
            path.unlink()
            print(f"CLEAN removed {path}")
            removed += 1
        except OSError as exc:
            print(f"CLEAN skip {path}: {exc}")
    return CleanSummary(orphans_removed=removed)


def run_pre_update_clean(
    target: Path,
    source: Path,
    *,
    prune_orphans: bool,
    dry_run: bool = False,
) -> CleanSummary:
    """Before heal/upgrade: drop runtime noise; optionally prune orphans."""
    summary = clean_runtime_artifacts(target)
    if prune_orphans:
        orphan_summary = prune_kit_orphans(target, source, dry_run=dry_run)
        summary = CleanSummary(
            runtime_dirs=summary.runtime_dirs,
            runtime_files=summary.runtime_files,
            orphans_removed=orphan_summary.orphans_removed,
        )
    return summary


def run_post_update_clean(
    target: Path,
    source: Path,
    *,
    dry_run: bool = False,
) -> CleanSummary:
    """After scaffold: runtime clean + prune kit orphans."""
    summary = clean_runtime_artifacts(target)
    orphan_summary = prune_kit_orphans(target, source, dry_run=dry_run)
    return CleanSummary(
        runtime_dirs=summary.runtime_dirs,
        runtime_files=summary.runtime_files,
        orphans_removed=orphan_summary.orphans_removed,
    )


def format_clean_summary(summary: CleanSummary) -> str:
    parts: list[str] = []
    if summary.runtime_dirs:
        parts.append(f"{summary.runtime_dirs} runtime dir(s)")
    if summary.runtime_files:
        parts.append(f"{summary.runtime_files} .pyc file(s)")
    if summary.orphans_removed:
        parts.append(f"{summary.orphans_removed} orphan(s)")
    if not parts:
        return "nothing to clean"
    return ", ".join(parts)
