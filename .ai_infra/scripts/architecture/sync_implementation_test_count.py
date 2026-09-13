"""
File: sync_implementation_test_count.py
Path: .ai_infra/scripts/architecture/sync_implementation_test_count.py
Role: Rewrite IMPLEMENTATION-STATUS / README collected-test counts from pytest --collect-only.
Used By:
 - make sync-doc-test-count
 - DOC-006 remediation (exact match kept; this syncs the SSOT)
Depends On:
 - paths.resolve_project_python
Notes:
 - Does not soften DOC-006; only updates documented integers to match collect-only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_ARCH = Path(__file__).resolve().parent
_AI_INFRA = _ARCH.parents[1]  # .ai_infra/
if str(_AI_INFRA) not in sys.path:
    sys.path.insert(0, str(_AI_INFRA))

from paths import resolve_project_python  # noqa: E402

STATUS_REL = Path(".ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md")
README_REL = Path("README.md")


def collect_pytest_count(root: Path) -> int:
    proc = subprocess.run(
        [resolve_project_python(root), "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    match = re.search(r"(\d+)\s+tests?\s+collected", combined)
    if not match:
        raise RuntimeError(f"pytest --collect-only failed to report count:\n{combined}")
    return int(match.group(1))


def sync_counts(root: Path, *, dry_run: bool = False) -> int:
    count = collect_pytest_count(root)
    updates: list[str] = []

    status_path = root / STATUS_REL
    if status_path.is_file():
        text = status_path.read_text(encoding="utf-8")
        text, n1 = re.subn(r"(\*\*Tests:\*\*\s*)\d+", rf"\g<1>{count}", text)
        text, n2 = re.subn(
            r"(\|\s*Tests\s*\|\s*)\d+(\s+collected)",
            rf"\g<1>{count}\2",
            text,
        )
        if n1 or n2:
            updates.append(f"{STATUS_REL}: Tests→{count} (product={n1}, table={n2})")
            if not dry_run:
                status_path.write_text(text, encoding="utf-8")

    readme = root / README_REL
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        text, n3 = re.subn(
            r"(·\s*\*\*Tests\*\*\s*·\s*)\d+",
            rf"\g<1>{count}",
            text,
        )
        text, n4 = re.subn(
            r"(\*\*Proof:\*\*\s*)\d+(\s+tests)",
            rf"\g<1>{count}\2",
            text,
        )
        if n3 or n4:
            updates.append(f"{README_REL}: Tests→{count} (table={n3}, proof={n4})")
            if not dry_run:
                readme.write_text(text, encoding="utf-8")

    if not updates:
        print(f"sync-doc-test-count: no patterns updated (collected={count})")
        return 1
    for line in updates:
        print(f"sync-doc-test-count: {line}")
    print(f"sync-doc-test-count: collected={count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync IMPLEMENTATION-STATUS / README test counts from pytest --collect-only."
    )
    parser.add_argument("--directory", default=".", help="Repo root (default: cwd)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned updates without writing files",
    )
    args = parser.parse_args()
    try:
        return sync_counts(Path(args.directory).resolve(), dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001
        print(f"sync-doc-test-count: FAIL — {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
