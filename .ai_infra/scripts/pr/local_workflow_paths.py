"""
File: local_workflow_paths.py
Path: .ai_infra/scripts/pr/local_workflow_paths.py
Role: Canonical paths for PR workflow markdown under `.local/workflow-artifacts/{pr,alignment,release}/`.
Used By:
 - scripts/pr/review.py
 - scripts/pr/prepare.py
 - scripts/pr/merge.py
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
WORKFLOW_RELEASE_DIR = WORKFLOW_ARTIFACTS_DIR / "release"

REVIEW_MD = WORKFLOW_PR_DIR / "review.md"
PREP_MD = WORKFLOW_PR_DIR / "prep.md"
MERGE_MD = WORKFLOW_PR_DIR / "merge.md"
ALIGNMENT_AUDIT_MD = WORKFLOW_ALIGNMENT_DIR / "alignment-audit.md"
ALIGNMENT_TODOS_MD = WORKFLOW_ALIGNMENT_DIR / "alignment-todos.md"

# Default live planning trackers (index-and-planning/current/)
PLANNING_CURRENT_DIR = Path(".local/index-and-planning/current")

# Fallback when `.local/user_settings/github.collaboration.yaml` is missing or incomplete.
# Prefer resolve_github_user() from user_settings.py in PR scripts.
DEFAULT_GITHUB_USER = "@YourGitHubHandle"


def ensure_workflow_artifacts_dir() -> None:
    """Create workflow artifact subdirectories if missing."""
    WORKFLOW_PR_DIR.mkdir(parents=True, exist_ok=True)
    WORKFLOW_ALIGNMENT_DIR.mkdir(parents=True, exist_ok=True)
    WORKFLOW_RELEASE_DIR.mkdir(parents=True, exist_ok=True)
