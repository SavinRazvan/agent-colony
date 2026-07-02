"""
File: consumer_bundle_paths.py
Path: .ai_infra/scripts/architecture/consumer_bundle_paths.py
Role: Shared paths and copy filters for consumer install / payload bundle purity.
Used By:
 - .ai_infra/scripts/install/scaffold.py
 - .ai_infra/scripts/release/sync_plugin_bundle.py
 - .ai_infra/scripts/architecture/check_consumer_purity.py
Depends On:
 - pathlib
Notes:
 - ci/kit-dev fixtures are maintainer-only; exclude from consumer template copy.
"""

from __future__ import annotations

LOCAL_WORKSPACE_REL = "templates/local-workspace"
OPERATIONS_REL = "docs/operations"
CI_FIXTURE_DIRNAME = "ci"

# Maintainer-only files under docs/operations (ADR-005); excluded from consumer copy.
OPERATIONS_MAINTAINER_ONLY: frozenset[str] = frozenset(
    {"documentation-maintenance-checklist.md"}
)

# Repo-relative paths excluded from consumer installs (for governance/purity checks).
CONSUMER_EXCLUDED_REL_PATHS: frozenset[str] = frozenset(
    f".ai_infra/{OPERATIONS_REL}/{name}" for name in OPERATIONS_MAINTAINER_ONLY
)

# Maintainer handles that must not appear in consumer-facing install surfaces.
MAINTAINER_IDENTITY_MARKERS: tuple[str, ...] = (
    "@SavinRazvan",
    "Savin Ionuț Răzvan",
)

# Kit-dev CI slice markers that must not appear in consumer .local/ after scaffold.
KIT_DEV_SLICE_MARKERS: tuple[str, ...] = (
    "CI-QUALITY",
    "ci-seed",
)


def is_local_workspace_copy(rel: str) -> bool:
    return rel.replace("\\", "/").rstrip("/") == LOCAL_WORKSPACE_REL


def is_operations_copy(rel: str) -> bool:
    return rel.replace("\\", "/").rstrip("/") == OPERATIONS_REL


def ignore_local_workspace_ci(directory: str, names: list[str]) -> set[str]:
    """shutil.copytree ignore: drop maintainer ci/ subtree from local-workspace templates."""
    if CI_FIXTURE_DIRNAME not in names:
        return set()
    norm = directory.replace("\\", "/").rstrip("/")
    if norm.endswith("/local-workspace") or norm.endswith(LOCAL_WORKSPACE_REL):
        return {CI_FIXTURE_DIRNAME}
    return set()


def ignore_operations_maintainer(_directory: str, names: list[str]) -> set[str]:
    """shutil.copytree ignore: drop kit-maintainer-only ops docs from consumer bundle."""
    return {n for n in names if n in OPERATIONS_MAINTAINER_ONLY}
