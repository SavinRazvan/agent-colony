"""
File: test_markdown_sections.py
Path: tests/modules/install/test_markdown_sections.py
Role: Unit tests for markdown_sections helper.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/markdown_sections.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

from markdown_sections import extract_section, list_h2_sections, slugify_heading  # noqa: E402


def test_extract_section_basic() -> None:
    text = "# Title\n\n## Alpha\n\none\n\n## Beta\n\ntwo\n"
    assert "one" in extract_section(text, "Alpha")
    assert "two" not in extract_section(text, "Alpha")


def test_slugify_heading() -> None:
    assert slugify_heading("Continuation contract") == "continuation-contract"


def test_list_h2_sections_repo_skill() -> None:
    path = REPO_ROOT / ".cursor" / "skills" / "evidence-first" / "SKILL.md"
    headings = list_h2_sections(path)
    assert "When (every agent)" in headings or any("When" in h for h in headings)
