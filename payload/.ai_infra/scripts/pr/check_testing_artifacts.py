"""
File: check_testing_artifacts.py
Path: .ai_infra/scripts/pr/check_testing_artifacts.py
Role: Validate required testing planning/index artifacts before PR prepare.
Used By:
 - scripts/pr/prepare.py
 - .agents/skills/pr-workflow/SKILL.md
Depends On:
 - pathlib
 - argparse
Notes:
 - Intended as a lightweight pre-prepare guard to keep testing continuity anchored.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _check_exists(path: Path) -> tuple[bool, str]:
    if path.exists():
        return True, f"PASS: exists -> {path}"
    return False, f"FAIL: missing -> {path}"


def _check_nonempty(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"FAIL: missing -> {path}"
    content = path.read_text(encoding="utf-8").strip()
    if content:
        return True, f"PASS: non-empty -> {path}"
    return False, f"FAIL: empty -> {path}"


def _check_test_index_structure(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"FAIL: missing -> {path}"
    content = path.read_text(encoding="utf-8")
    if "Module:" in content and "Coverage status:" in content:
        return True, f"PASS: structure markers found -> {path}"
    return False, f"FAIL: expected markers not found (`Module:` and `Coverage status:`) -> {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate required testing artifacts for PR prepare.")
    parser.add_argument(
        "--planning-dir",
        dest="planning_dir",
        default=".local/index-and-planning/current",
        help="Directory containing test-plan.md, test-index.md, and related planning markdown.",
    )
    parser.add_argument(
        "--control-center-dir",
        dest="legacy_planning_dir",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--tests-dir",
        default="tests/modules",
        help="Directory containing module-aligned tests.",
    )
    args = parser.parse_args()

    planning_root = args.legacy_planning_dir or args.planning_dir
    control_center = Path(planning_root)
    tests_dir = Path(args.tests_dir)
    test_plan = control_center / "test-plan.md"
    test_index = control_center / "test-index.md"

    checks = [
        _check_exists(control_center),
        _check_exists(tests_dir),
        _check_nonempty(test_plan),
        _check_nonempty(test_index),
        _check_test_index_structure(test_index),
    ]

    failed = False
    for ok, message in checks:
        print(message)
        if not ok:
            failed = True

    if failed:
        print("Testing artifact check failed.")
        return 1

    print("Testing artifact check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
