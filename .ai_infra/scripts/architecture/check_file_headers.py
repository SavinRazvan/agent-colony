"""
File: check_file_headers.py
Path: .ai_infra/scripts/architecture/check_file_headers.py
Role: Verify kit Python modules include the standard File/Path/Role relation header.
Used By:
 - .ai_infra/scripts/architecture/check_governance_consistency.py
 - Makefile gates (via governance consistency)
Depends On:
 - .cursor/rules/file-docstring-header-relations.mdc
Notes:
 - Scans maintainer Python trees only; skips __pycache__ and empty __init__.py stubs.
"""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_MARKERS: tuple[str, ...] = ("File:", "Path:", "Role:", "Depends On:")

SCAN_ROOTS: tuple[str, ...] = (
    ".ai_infra/scripts",
    ".ai_infra/mcp_servers",
    ".ai_infra/install",
    "cursor_workflow",
    "tests/modules",
)

HEADER_WINDOW_CHARS = 900


def _is_scannable_py(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    if "__pycache__" in path.parts:
        return False
    if path.name == "__init__.py" and path.stat().st_size < 80:
        return False
    return True


def collect_file_header_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for rel_root in SCAN_ROOTS:
        scan = root / rel_root
        if not scan.is_dir():
            continue
        for path in sorted(scan.rglob("*.py")):
            if not _is_scannable_py(path):
                continue
            try:
                head = path.read_text(encoding="utf-8")[:HEADER_WINDOW_CHARS]
            except OSError:
                violations.append(f"{path.relative_to(root)}: unreadable")
                continue
            missing = [m for m in REQUIRED_MARKERS if m not in head]
            if missing:
                rel = path.relative_to(root).as_posix()
                violations.append(f"{rel}: missing header fields {missing}")
    return violations


def main(argv: list[str] | None = None) -> int:
    import argparse

    for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
        bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
        if bootstrap.is_file():
            if str(_candidate / ".ai_infra") not in sys.path:
                sys.path.insert(0, str(_candidate / ".ai_infra"))
            from bootstrap import ensure_paths_import

            kit_root = ensure_paths_import(__file__)
            break
    else:
        kit_root = Path.cwd()

    parser = argparse.ArgumentParser(description="Check Python file relation headers.")
    parser.add_argument("--directory", type=Path, default=kit_root)
    args = parser.parse_args(argv)
    root = args.directory.resolve()
    violations = collect_file_header_violations(root)
    if violations:
        print("File header check failed:")
        for violation in violations:
            print(f" - {violation}")
        return 1
    print("File header check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
