"""
File: check_consumer_purity.py
Path: .ai_infra/scripts/architecture/check_consumer_purity.py
Role: Fail when a consumer install tree contains kit-dev fixtures or maintainer identity leaks.
Used By:
 - Makefile install-dry-run
 - Local pre-merge checks
Depends On:
 - .ai_infra/scripts/architecture/consumer_bundle_paths.py
Notes:
 - Scans an installed target (default /tmp/workflow-kit-dry-run), not the kit-dev repo root.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ROOT = ensure_paths_import(__file__)
        break
else:
    raise RuntimeError("kit root not found above check_consumer_purity.py")

ARCH_SCRIPTS = ROOT / ".ai_infra" / "scripts" / "architecture"
if str(ARCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ARCH_SCRIPTS))

from consumer_bundle_paths import (  # noqa: E402
    CI_FIXTURE_DIRNAME,
    KIT_DEV_SLICE_MARKERS,
    LOCAL_WORKSPACE_REL,
    MAINTAINER_IDENTITY_MARKERS,
    OPERATIONS_MAINTAINER_ONLY,
    OPERATIONS_REL,
)

TEXT_SUFFIXES = {".md", ".mdc", ".py", ".yaml", ".yml", ".txt", ".json", ".jsonc"}
DEFAULT_TARGET = Path("/tmp/workflow-kit-dry-run")

CONSUMER_SCAN_ROOTS: tuple[str, ...] = (
    ".cursor/rules",
    ".ai_infra/templates/user-settings",
    ".local",
)

SKIP_UNDER_TEMPLATES = frozenset()

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _scan_file_for_markers(path: Path, markers: tuple[str, ...]) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    text = _read_text(path)
    hits = [m for m in markers if m in text]
    if not hits:
        return []
    rel = path.as_posix()
    return [f"{rel}: contains {hit!r}" for hit in hits]


def check_consumer_purity(target: Path) -> list[str]:
    violations: list[str] = []

    ci_path = target / ".ai_infra" / LOCAL_WORKSPACE_REL / CI_FIXTURE_DIRNAME
    if ci_path.exists():
        violations.append(f"{ci_path.relative_to(target)}: kit-dev ci fixtures must not ship")

    for maintainer_doc in OPERATIONS_MAINTAINER_ONLY:
        leaked = target / ".ai_infra" / OPERATIONS_REL / maintainer_doc
        if leaked.is_file():
            violations.append(
                f"{leaked.relative_to(target)}: kit-maintainer-only doc must not ship"
            )

    commit_rule = target / ".cursor" / "rules" / "commit-trailer-format.mdc"
    if commit_rule.is_file():
        violations.extend(
            _scan_file_for_markers(commit_rule, MAINTAINER_IDENTITY_MARKERS)
        )

    for rel_root in CONSUMER_SCAN_ROOTS:
        root = target / rel_root
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if ".venv" in path.parts:
                continue
            rel = path.relative_to(target).as_posix()
            if rel_root == ".local":
                violations.extend(
                    _scan_file_for_markers(path, KIT_DEV_SLICE_MARKERS + MAINTAINER_IDENTITY_MARKERS)
                )
            elif rel_root == ".ai_infra/templates/user-settings":
                violations.extend(_scan_file_for_markers(path, MAINTAINER_IDENTITY_MARKERS))
            # .cursor/rules/commit-trailer handled above

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check consumer install tree for kit-dev leaks.")
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Installed consumer tree (default: {DEFAULT_TARGET})",
    )
    args = parser.parse_args(argv)
    target = args.target.resolve()
    if not target.is_dir():
        print(f"Consumer purity check failed: target not found: {target}")
        return 1
    violations = check_consumer_purity(target)
    if violations:
        print("Consumer purity check failed:")
        for violation in violations:
            print(f" - {violation}")
        return 1
    print(f"Consumer purity check passed ({target}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
