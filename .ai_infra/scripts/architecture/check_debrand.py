"""
File: check_debrand.py
Path: .ai_infra/scripts/architecture/check_debrand.py
Role: Fail when banned legacy product names appear in tracked kit surfaces.
Used By:
 - README.md verification section
 - Local pre-merge checks
Depends On:
 - pathlib
 - re
Notes:
 - Scans explicit paths only (fast); excludes .venv and .git.
"""

from __future__ import annotations

import re
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
    raise RuntimeError("kit root not found above check_debrand.py")

from paths import kit_root_from_script

ROOT = kit_root_from_script(__file__)

SCAN_ROOTS: tuple[Path, ...] = (
    ROOT / ".cursor",
    ROOT / ".agents",
    ROOT / ".ai_infra",
    ROOT / "tests",
    ROOT / "cursor_workflow",
    ROOT / "overlays",
    ROOT / "project-rules",
    ROOT / "schemas",
)

SCAN_FILES: tuple[Path, ...] = (
    ROOT / "AGENTS.md",
    ROOT / "README.md",
)

BANNED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("eXo-brain", re.compile(r"eXo-brain", re.IGNORECASE)),
    ("exo-brain", re.compile(r"exo-brain", re.IGNORECASE)),
    ("eXo_brain", re.compile(r"eXo_brain", re.IGNORECASE)),
    ("mcp-starter-kit", re.compile(r"mcp-starter-kit", re.IGNORECASE)),
    ("Cursor Workflow Starter Kit", re.compile(r"Cursor Workflow Starter Kit", re.IGNORECASE)),
    ("with_exo_pack", re.compile(r"with_exo_pack")),
    ("overlay-exo", re.compile(r"overlay-exo")),
    ("pack_exo_brain", re.compile(r"pack_exo_brain")),
    ("examples/eXo-brain-pack", re.compile(r"examples/eXo-brain-pack", re.IGNORECASE)),
)

TEXT_SUFFIXES = {".md", ".mdc", ".py", ".yaml", ".yml", ".txt", ".json", ".jsonc"}

SKIP_REL_PATHS = frozenset(
    {
        ".ai_infra/scripts/architecture/check_debrand.py",
        ".ai_infra/scripts/architecture/check_governance_consistency.py",
    }
)


def _iter_files() -> list[Path]:
    paths: list[Path] = [p for p in SCAN_FILES if p.is_file()]
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            paths.append(root)
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if ".venv" in path.parts or ".git" in path.parts:
                continue
            if path.suffix.lower() in TEXT_SUFFIXES:
                paths.append(path)
    return sorted(set(paths))


def _collect_violations() -> list[str]:
    violations: list[str] = []
    for path in _iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in SKIP_REL_PATHS:
            continue
        for label, pattern in BANNED_PATTERNS:
            if pattern.search(text):
                violations.append(f"{rel}: banned term ({label})")
    return violations


def main() -> int:
    violations = _collect_violations()
    if violations:
        print("De-brand check failed:")
        for violation in violations:
            print(f" - {violation}")
        return 1
    print("De-brand check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
