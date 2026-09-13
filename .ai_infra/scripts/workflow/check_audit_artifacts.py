"""
File: check_audit_artifacts.py
Path: .ai_infra/scripts/workflow/check_audit_artifacts.py
Role: CLI scanner for audit artifacts using audit_artifact_schema validation.
Used By:
 - .ai_infra/scripts/pr/prepare.py (kit-dev gate append)
 - tests/modules/workflow/test_check_audit_artifacts.py
Depends On:
 - .ai_infra/scripts/workflow/audit_artifact_schema.py
 - .ai_infra/scripts/pr/local_workflow_paths.py
Notes:
 - Exit 0 when all scanned schema-1 artifacts pass or are skipped; exit 1 on validation errors.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_PR_DIR = _SCRIPT_DIR.parent / "pr"
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
if str(_PR_DIR) not in sys.path:
    sys.path.insert(0, str(_PR_DIR))

from audit_artifact_schema import validate_audit_text  # noqa: E402
from local_workflow_paths import (  # noqa: E402
    ALIGNMENT_AUDIT_MD,
    ALIGNMENT_TODOS_MD,
    DRIFT_AUDIT_MD,
    DRIFT_TODOS_MD,
    EA_ACTIONS_MD,
    EA_REPORT_MD,
    WORKFLOW_AUDIT_DIR,
)

_CANONICAL_REL = (
    ALIGNMENT_AUDIT_MD,
    ALIGNMENT_TODOS_MD,
    DRIFT_AUDIT_MD,
    DRIFT_TODOS_MD,
    EA_REPORT_MD,
    EA_ACTIONS_MD,
)


def collect_audit_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel in _CANONICAL_REL:
        candidate = root / rel
        if candidate.is_file():
            paths.append(candidate)
    audit_dir = root / WORKFLOW_AUDIT_DIR
    if audit_dir.is_dir():
        for md in sorted(audit_dir.glob("*.md")):
            if md not in paths:
                paths.append(md)
    return paths


def validate_file(path: Path) -> tuple[bool, list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    return validate_audit_text(text)


def run_scan(root: Path) -> tuple[int, int, int, list[str]]:
    """Return (checked, skipped, failed, detail_lines)."""
    checked = skipped = failed = 0
    lines: list[str] = []
    for path in collect_audit_paths(root):
        rel = path.relative_to(root).as_posix()
        skip, errors, warnings = validate_file(path)
        if skip:
            skipped += 1
            lines.append(f"SKIP\t{rel}")
            continue
        checked += 1
        if errors:
            failed += 1
            lines.append(f"FAIL\t{rel}")
            for err in errors:
                lines.append(f"  error: {err}")
        else:
            lines.append(f"PASS\t{rel}")
        for warn in warnings:
            lines.append(f"  warn: {warn}")
    return checked, skipped, failed, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate audit artifacts (Audit-Schema: 1).")
    parser.add_argument("--directory", default=".", help="Project root")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print one-line PASS/FAIL/SKIP per file",
    )
    parser.add_argument(
        "--arch-impacting",
        action="store_true",
        help=(
            "Require alignment-audit.md and alignment-todos.md to exist, "
            "carry Audit-Schema: 1, and pass validation"
        ),
    )
    args = parser.parse_args(argv)

    root = Path(args.directory).resolve()
    checked, skipped, failed, lines = run_scan(root)
    scanned = {p.resolve() for p in collect_audit_paths(root)}

    if args.arch_impacting:
        for rel in (ALIGNMENT_AUDIT_MD, ALIGNMENT_TODOS_MD):
            path = root / rel
            rel_posix = rel.as_posix()
            if not path.is_file():
                failed += 1
                lines.append(f"FAIL\t{rel_posix} (required for --arch-impacting)")
                continue
            skip, errors, _warnings = validate_file(path)
            if skip:
                failed += 1
                lines.append(
                    f"FAIL\t{rel_posix} (required Audit-Schema: 1 for --arch-impacting)"
                )
                continue
            if errors:
                # run_scan already counted this file when it was in the scan set
                if path.resolve() not in scanned:
                    failed += 1
                    lines.append(f"FAIL\t{rel_posix} (--arch-impacting)")
                    for err in errors:
                        lines.append(f"  error: {err}")
                else:
                    lines.append(f"FAIL\t{rel_posix} (--arch-impacting incomplete)")

    if args.summary:
        verdict = "FAIL" if failed else "PASS"
        print(f"check_audit_artifacts: {verdict} checked={checked} skipped={skipped} failed={failed}")
        for line in lines:
            print(line)
    else:
        for line in lines:
            print(line)
        print(f"summary: checked={checked} skipped={skipped} failed={failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
