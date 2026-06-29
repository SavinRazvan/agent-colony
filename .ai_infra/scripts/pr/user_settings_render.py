"""
File: user_settings_render.py
Path: .ai_infra/scripts/pr/user_settings_render.py
Role: Render git commit trailers and GitHub PR body from user settings.
Used By:
 - user_settings.py
Depends On:
 - user_settings_load.py
 - user_settings_resolve.py
Notes:
 - Does not perform network calls; output is copy/paste or gh pr create body.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from user_settings_load import (
    GITHUB_COLLAB_REL,
    is_placeholder_owner,
    load_github_collaboration,
    normalize_github_user,
)
from user_settings_resolve import (
    resolve_agents_for_pr,
    resolve_default_actor,
    resolve_github_user,
)


def _format_assisted_by(entry: dict[str, Any]) -> str:
    tool = str(entry.get("tool", "")).strip()
    if not tool:
        return ""
    model = entry.get("model")
    agent = entry.get("agent")
    if model:
        return f"Assisted-by: {tool}:{model}"
    if agent:
        return f"Assisted-by: {tool}:{agent}"
    return f"Assisted-by: {tool}"


def render_commit_trailers(root: Path | None = None) -> str:
    cfg = load_github_collaboration(root)
    if not cfg:
        raise FileNotFoundError(f"Missing {GITHUB_COLLAB_REL}")

    if is_placeholder_owner(cfg):
        raise ValueError(
            f"Complete owner.display_name and owner.github_user in {GITHUB_COLLAB_REL}"
        )

    owner = cfg["owner"]
    lines = [
        f"Author: {owner['display_name']}",
        f"GitHub-User: {normalize_github_user(str(owner['github_user']))}",
    ]

    prov = cfg.get("commit_provenance") or {}
    mode = prov.get("ai_disclosure_mode", "assisted_by")

    if mode == "assisted_by":
        for entry in prov.get("assisted_by") or []:
            if isinstance(entry, dict):
                line = _format_assisted_by(entry)
                if line:
                    lines.append(line)
    elif mode == "co_author_trailer":
        trailer = prov.get("co_author_trailer") or {}
        name = trailer.get("name")
        email = trailer.get("email")
        if name and email:
            lines.append(f"Co-authored-by: {name} <{email}>")
        for entry in prov.get("assisted_by") or []:
            if isinstance(entry, dict):
                line = _format_assisted_by(entry)
                if line:
                    lines.append(line)

    for co in prov.get("human_coauthors") or []:
        if isinstance(co, dict) and co.get("display_name") and co.get("email"):
            lines.append(f"Co-authored-by: {co['display_name']} <{co['email']}>")

    return "\n".join(lines)


def render_pr_body(
    root: Path | None = None,
    *,
    summary_bullets: list[str] | None = None,
    test_plan_items: list[str] | None = None,
    pipeline: str = "default",
    agents_from_session: bool = True,
) -> str:
    cfg = load_github_collaboration(root)
    if not cfg:
        raise FileNotFoundError(f"Missing {GITHUB_COLLAB_REL}")

    owner = cfg.get("owner") or {}
    pr_cfg = (cfg.get("pr_collaboration") or {}).get("pr_body") or {}
    summary_heading = pr_cfg.get("summary_heading", "## Summary")
    test_heading = pr_cfg.get("test_plan_heading", "## Test plan")
    collab_heading = pr_cfg.get("collaboration_heading", "## Collaboration")

    bullets = summary_bullets or ["- (describe changes)"]
    tests = test_plan_items or pr_cfg.get("default_test_plan") or ["pytest -q"]
    test_lines = [f"- [ ] {item.lstrip('- ').strip()}" for item in tests]

    actor = resolve_default_actor(root) or str(owner.get("display_name", ""))
    github_user = resolve_github_user(root)
    agents = resolve_agents_for_pr(
        root=root,
        cfg=cfg,
        pipeline=pipeline,
        agents_from_session=agents_from_session,
    )

    lines = [
        summary_heading,
        *bullets,
        "",
        test_heading,
        *test_lines,
        "",
        collab_heading,
        f"- Action-By: {actor}",
        f"- GitHub-User: {github_user}",
        f"- Agent/s: {agents}",
    ]

    pipe_spec = ((cfg.get("pr_collaboration") or {}).get("pipelines") or {}).get(pipeline) or {}
    if pipe_spec.get("requires_alignment_artifacts"):
        lines.append("- Alignment: `.local/workflow-artifacts/alignment/`")

    return "\n".join(lines)
