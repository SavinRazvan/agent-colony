"""
File: arch_impacting_paths.py
Path: .ai_infra/scripts/pr/arch_impacting_paths.py
Role: Detect kit-dev path diffs that force architecture-impacting merge checks.
Used By:
 - .ai_infra/scripts/pr/merge.py
 - .ai_infra/scripts/pr/prepare.py
 - tests/modules/pr_workflow/
Depends On:
 - pathlib
 - subprocess
Notes:
 - Ordinary prepare still skips leftover Schema-0 (ADR-013); path-trigger forces merge-time Schema-1 only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# Paths (prefixes or exact files) under kit-dev that force --arch-impacting at merge.
ARCH_IMPACTING_PATH_TRIGGERS: tuple[str, ...] = (
    ".cursor/rules/",
    ".cursor/skills/",
    ".cursor/agents/",
    ".agents/skills/",
    ".ai_infra/docs/decisions/",
    ".ai_infra/docs/architecture/",
    ".ai_infra/docs/roadmap/alignment-audit-schema.md",
    ".ai_infra/scripts/pr/",
    ".ai_infra/scripts/workflow/audit_artifact_schema.py",
    ".ai_infra/scripts/workflow/check_audit_artifacts.py",
    ".ai_infra/scripts/workflow/drift_checks.py",
)


def _normalize_repo_path(raw: str) -> str:
    path = raw.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.lstrip("/")


def path_triggers_arch_impacting(paths: list[str] | tuple[str, ...]) -> bool:
    """True when any changed path matches an architecture-impacting trigger."""
    for raw in paths:
        path = _normalize_repo_path(raw)
        for trigger in ARCH_IMPACTING_PATH_TRIGGERS:
            if trigger.endswith("/"):
                if path.startswith(trigger):
                    return True
            elif path == trigger:
                return True
    return False


def git_changed_paths_vs_base(
    root: Path,
    *,
    base_ref: str = "origin/main",
) -> list[str]:
    """Return paths changed between merge-base(base_ref, HEAD) and HEAD."""
    merge_base = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    base = (merge_base.stdout or "").strip()
    if merge_base.returncode != 0 or not base:
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    if diff.returncode != 0:
        return []
    return [line.strip() for line in (diff.stdout or "").splitlines() if line.strip()]


def branch_triggers_arch_impacting(
    root: Path,
    *,
    base_ref: str = "origin/main",
) -> bool:
    """True when current branch diff vs base touches an arch-impacting path."""
    return path_triggers_arch_impacting(git_changed_paths_vs_base(root, base_ref=base_ref))
