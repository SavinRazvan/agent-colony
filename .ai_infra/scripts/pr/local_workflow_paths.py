"""
File: local_workflow_paths.py
Path: .ai_infra/scripts/pr/local_workflow_paths.py
Role: Canonical paths for workflow artifacts under `.local/workflow-artifacts/`.
Used By:
 - scripts/pr/review.py
 - scripts/pr/prepare.py
 - scripts/pr/merge.py
 - scripts/install/scaffold.py
 - scripts/ci/seed_kit_workspace.py
Depends On:
 - pathlib
Notes:
 - Keep path strings aligned with `.cursor/rules/pr-workflow-enforcement.mdc` and
   `scripts/architecture/check_governance_consistency.py` merge.py parity fragments.
 - Git **commit** messages (not these `.md` paths): **`.cursor/rules/commit-trailer-format.mdc`** — `Author` / `GitHub-User`, optional `Assisted-by`; no `Made-with:`.
"""

from __future__ import annotations

from pathlib import Path

WORKFLOW_ARTIFACTS_DIR = Path(".local/workflow-artifacts")
WORKFLOW_PR_DIR = WORKFLOW_ARTIFACTS_DIR / "pr"
WORKFLOW_ALIGNMENT_DIR = WORKFLOW_ARTIFACTS_DIR / "alignment"
WORKFLOW_DRIFT_DIR = WORKFLOW_ARTIFACTS_DIR / "drift"
WORKFLOW_ENTERPRISE_AUDIT_DIR = WORKFLOW_ARTIFACTS_DIR / "enterprise-architecture-audit"
WORKFLOW_RELEASE_DIR = WORKFLOW_ARTIFACTS_DIR / "release"
WORKFLOW_AUDIT_DIR = WORKFLOW_ARTIFACTS_DIR / "audit"

REVIEW_MD = WORKFLOW_PR_DIR / "review.md"
PREP_MD = WORKFLOW_PR_DIR / "prep.md"
MERGE_MD = WORKFLOW_PR_DIR / "merge.md"
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
)

# Directory names under workflow-artifacts/ (for README stubs; derived from bucket paths).
ARTIFACT_STUB_BUCKET_NAMES: tuple[str, ...] = tuple(p.name for p in WORKFLOW_ARTIFACT_BUCKETS)

# Default live planning trackers (index-and-planning/current/)
PLANNING_CURRENT_DIR = Path(".local/index-and-planning/current")

# Fallback when `.local/user_settings/github.collaboration.yaml` is missing or incomplete.
# Prefer resolve_github_user() from user_settings.py in PR scripts.
DEFAULT_GITHUB_USER = "@YourGitHubHandle"


def ensure_workflow_artifacts_tree(*, root: Path | None = None) -> None:
    """Create all canonical workflow-artifacts bucket directories if missing."""
    base = Path(".") if root is None else root
    for bucket in WORKFLOW_ARTIFACT_BUCKETS:
        (base / bucket).mkdir(parents=True, exist_ok=True)


def ensure_workflow_artifacts_dir() -> None:
    """Create workflow artifact subdirectories if missing (cwd-relative)."""
    ensure_workflow_artifacts_tree()
