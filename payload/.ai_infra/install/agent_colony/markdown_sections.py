"""
File: markdown_sections.py
Path: .ai_infra/install/agent_colony/markdown_sections.py
Role: Shared markdown section extraction for doc CLI, drift checks, and MCP resources.
Used By:
 - .ai_infra/install/agent_colony/doc_cli.py
 - .ai_infra/scripts/workflow/drift_checks.py
 - .ai_infra/mcp_servers/agent_colony_mcp/resources.py
Depends On:
 - re (stdlib)
Notes:
 - SSOT for _section_block logic; drift_checks delegates here.
"""

from __future__ import annotations

import re
from pathlib import Path


def slugify_heading(heading: str) -> str:
    """Lowercase slug for MCP URI segments and fuzzy section match."""
    text = heading.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def extract_section(text: str, heading: str) -> str:
    """Return body under ``## {heading}`` until the next ``##`` heading."""
    marker = f"## {heading}"
    if marker not in text:
        # Fuzzy: match ## line whose slug equals heading slug
        target_slug = slugify_heading(heading)
        for line in text.splitlines():
            if line.startswith("## "):
                h = line[3:].strip()
                if slugify_heading(h) == target_slug:
                    marker = f"## {h}"
                    break
        else:
            return ""
    section = text.split(marker, 1)[1]
    next_heading = re.search(r"\n## [^\n]+", section)
    body = section[: next_heading.start()] if next_heading else section
    return body.strip()


def list_h2_sections(path: Path) -> list[str]:
    """List ``##`` heading titles from a markdown file."""
    if not path.is_file():
        return []
    headings: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def section_block(text: str, heading: str) -> str:
    """Alias used by drift_checks legacy callers; includes heading line context."""
    body = extract_section(text, heading)
    if not body:
        return text
    return body
