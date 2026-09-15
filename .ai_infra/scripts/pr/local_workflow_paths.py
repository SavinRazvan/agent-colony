"""
File: local_workflow_paths.py
Path: .ai_infra/scripts/pr/local_workflow_paths.py
Role: Canonical paths for workflow artifacts under `.local/workflow-artifacts/`.
Used By:
 - scripts/pr/review.py
 - scripts/pr/prepare.py
 - scripts/pr/merge.py
 - scripts/pr/finalize.py
 - scripts/install/scaffold.py
 - scripts/ci/seed_kit_workspace.py
Depends On:
 - pathlib
Notes:
 - Keep path strings aligned with `.cursor/rules/pr-workflow-enforcement.mdc` and
   `scripts/architecture/check_governance_consistency.py` merge.py parity fragments.
 - Git **commit** messages (not these `.md` paths): **`.cursor/rules/commit-trailer-format.mdc`** — `Author` / `GitHub-User`, optional `Assisted-by`; no `Made-with:`.
 - Pattern A tip files overwrite; prior tip is copied to ``pr/archive/`` via ``archive_then_write``.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW_ARTIFACTS_DIR = Path(".local/workflow-artifacts")
WORKFLOW_PR_DIR = WORKFLOW_ARTIFACTS_DIR / "pr"
WORKFLOW_PR_ARCHIVE_DIR = WORKFLOW_PR_DIR / "archive"
WORKFLOW_ALIGNMENT_DIR = WORKFLOW_ARTIFACTS_DIR / "alignment"
WORKFLOW_DRIFT_DIR = WORKFLOW_ARTIFACTS_DIR / "drift"
WORKFLOW_ENTERPRISE_AUDIT_DIR = WORKFLOW_ARTIFACTS_DIR / "enterprise-architecture-audit"
WORKFLOW_RELEASE_DIR = WORKFLOW_ARTIFACTS_DIR / "release"
WORKFLOW_AUDIT_DIR = WORKFLOW_ARTIFACTS_DIR / "audit"
WORKFLOW_DEBUG_DIR = WORKFLOW_ARTIFACTS_DIR / "debug"

REVIEW_MD = WORKFLOW_PR_DIR / "review.md"
PREP_MD = WORKFLOW_PR_DIR / "prep.md"
MERGE_MD = WORKFLOW_PR_DIR / "merge.md"
FINALIZE_MD = WORKFLOW_PR_DIR / "finalize.md"
ALIGNMENT_AUDIT_MD = WORKFLOW_ALIGNMENT_DIR / "alignment-audit.md"
ALIGNMENT_TODOS_MD = WORKFLOW_ALIGNMENT_DIR / "alignment-todos.md"
DRIFT_AUDIT_MD = WORKFLOW_DRIFT_DIR / "drift-audit.md"
DRIFT_TODOS_MD = WORKFLOW_DRIFT_DIR / "drift-todos.md"
EA_REPORT_MD = WORKFLOW_ENTERPRISE_AUDIT_DIR / "enterprise-architecture-audit.md"
EA_ACTIONS_MD = WORKFLOW_ENTERPRISE_AUDIT_DIR / "enterprise-audit-actions.md"

WORKFLOW_ARTIFACT_BUCKETS: tuple[Path, ...] = (
    WORKFLOW_PR_DIR,
    WORKFLOW_ALIGNMENT_DIR,
    WORKFLOW_DRIFT_DIR,
    WORKFLOW_ENTERPRISE_AUDIT_DIR,
    WORKFLOW_RELEASE_DIR,
    WORKFLOW_AUDIT_DIR,
    WORKFLOW_DEBUG_DIR,
)

# Directory names under workflow-artifacts/ (for README stubs; derived from bucket paths).
ARTIFACT_STUB_BUCKET_NAMES: tuple[str, ...] = tuple(p.name for p in WORKFLOW_ARTIFACT_BUCKETS)

# Default live planning trackers (index-and-planning/current/)
PLANNING_CURRENT_DIR = Path(".local/index-and-planning/current")

# Canvas / plan local evidence (ADR-010; gitignored Tier-2 runtime)
LOCAL_CANVASES_DIR = Path(".local/canvases")
LOCAL_PLANS_DIR = Path(".local/plans")
LOCAL_CANVASES_INDEX = LOCAL_CANVASES_DIR / "index.md"
LOCAL_PLANS_INDEX = LOCAL_PLANS_DIR / "index.md"
REPO_CANVASES_DIR = Path("canvases")
WORKFLOW_CANVAS_DIR = WORKFLOW_ARTIFACTS_DIR / "canvas"

LOCAL_ARTIFACT_DIRS: tuple[Path, ...] = (
    LOCAL_CANVASES_DIR,
    LOCAL_PLANS_DIR,
)

# Fallback when `.local/user_settings/github.collaboration.yaml` is missing or incomplete.
# Prefer resolve_github_user() from user_settings.py in PR scripts.
DEFAULT_GITHUB_USER = "@YourGitHubHandle"


def _sanitize_pr_slug(pr: str | None) -> str:
    raw = (pr or "").strip() or "unknown"
    digits = re.search(r"(\d+)", raw)
    if digits:
        return digits.group(1)
    cleaned = re.sub(r"[^\w.-]+", "-", raw).strip("-")
    return cleaned or "unknown"


def archive_then_write(
    path: Path,
    content: str,
    *,
    pr: str | None = None,
    phase: str = "artifact",
    encoding: str = "utf-8",
) -> Path | None:
    """
    Write ``content`` to ``path``, archiving any prior non-empty tip file first.

    Archive name: ``pr/archive/pr-<n>-<phase>-<UTC>.md``. Returns the archive
    path when a copy was made, else None. Tip path stays fixed (Pattern A).
    """
    archived: Path | None = None
    if path.is_file() and path.stat().st_size > 0:
        WORKFLOW_PR_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        phase_slug = re.sub(r"[^\w.-]+", "-", (phase or "artifact").strip()) or "artifact"
        dest = WORKFLOW_PR_ARCHIVE_DIR / f"pr-{_sanitize_pr_slug(pr)}-{phase_slug}-{stamp}.md"
        shutil.copy2(path, dest)
        archived = dest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return archived


def ensure_workflow_artifacts_tree(*, root: Path | None = None) -> None:
    """Create all canonical workflow-artifacts bucket directories if missing."""
    base = Path(".") if root is None else root
    for bucket in WORKFLOW_ARTIFACT_BUCKETS:
        (base / bucket).mkdir(parents=True, exist_ok=True)
    (base / WORKFLOW_PR_ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)


def ensure_workflow_artifacts_dir() -> None:
    """Create workflow artifact subdirectories if missing (cwd-relative)."""
    ensure_workflow_artifacts_tree()


def ensure_local_artifact_tree(*, root: Path | None = None) -> None:
    """Create `.local/canvases/` and `.local/plans/` if missing."""
    base = Path(".") if root is None else root
    for directory in LOCAL_ARTIFACT_DIRS:
        (base / directory).mkdir(parents=True, exist_ok=True)
    (base / WORKFLOW_CANVAS_DIR).mkdir(parents=True, exist_ok=True)
