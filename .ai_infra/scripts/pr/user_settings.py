"""
File: user_settings.py
Path: .ai_infra/scripts/pr/user_settings.py
Role: Public API for `.local/user_settings/` — load, resolve, render, validate.
Used By:
 - scripts/pr/review.py, prepare.py, merge.py
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - user_settings_load.py
 - user_settings_resolve.py
 - user_settings_render.py
Notes:
 - Facade preserving import surface for PR scripts and integrate validate.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from user_settings_load import (
    GITHUB_COLLAB_REL,
    MCP_AGENTS_REL,
    PIPELINE_NAMES,
    github_collaboration_path,
    is_placeholder_owner,
    load_github_collaboration,
    load_mcp_agents,
    mcp_agents_path,
    project_root,
    validate_github_collaboration_schema,
    validate_mcp_agents_schema,
)
from user_settings_render import render_commit_trailers, render_pr_body
from user_settings_resolve import (
    collect_session_agents,
    merge_agent_lists,
    pipeline_agents_list,
    pipeline_agents_string,
    resolve_agents_for_pr,
    resolve_default_actor,
    resolve_github_user,
    resolve_pipeline_name,
    resolve_pr_attribution,
)

__all__ = [
    "GITHUB_COLLAB_REL",
    "MCP_AGENTS_REL",
    "PIPELINE_NAMES",
    "add_pr_attribution_arguments",
    "collect_session_agents",
    "github_collaboration_path",
    "is_placeholder_owner",
    "load_github_collaboration",
    "load_mcp_agents",
    "mcp_agents_path",
    "merge_agent_lists",
    "pipeline_agents_list",
    "pipeline_agents_string",
    "render_commit_trailers",
    "render_pr_body",
    "resolve_agents_for_pr",
    "resolve_default_actor",
    "resolve_github_user",
    "resolve_pipeline_name",
    "resolve_pr_attribution",
    "validate_github_collaboration",
    "validate_github_collaboration_schema",
    "validate_mcp_agents_schema",
    "validate_mcp_agents_worksheet",
]


def validate_github_collaboration(root: Path | None = None) -> list[str]:
    errors: list[str] = []
    path = github_collaboration_path(root)
    if not path.is_file():
        errors.append(f"missing {GITHUB_COLLAB_REL} (re-run install scaffold or copy exemplars)")
        return errors

    cfg = None
    try:
        cfg = load_github_collaboration(root)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if cfg is None:
        errors.append(f"invalid YAML in {GITHUB_COLLAB_REL}")
        return errors

    errors.extend(validate_github_collaboration_schema(root))

    if is_placeholder_owner(cfg):
        errors.append(
            f"incomplete owner in {GITHUB_COLLAB_REL} — set display_name and github_user"
        )

    prov = cfg.get("commit_provenance") or {}
    for forbidden in prov.get("forbid_in_commits") or []:
        if "Made-with" in str(forbidden):
            continue

    pipelines = (cfg.get("pr_collaboration") or {}).get("pipelines") or {}
    if "default" not in pipelines:
        errors.append(f"missing pr_collaboration.pipelines.default in {GITHUB_COLLAB_REL}")

    return errors


def validate_mcp_agents_worksheet(root: Path | None = None) -> list[str]:
    errors: list[str] = []
    path = mcp_agents_path(root)
    if not path.is_file():
        errors.append(f"missing {MCP_AGENTS_REL}")
        return errors

    cfg = load_mcp_agents(root)
    if cfg is None:
        errors.append(f"invalid YAML in {MCP_AGENTS_REL}")
        return errors

    errors.extend(validate_mcp_agents_schema(root))

    registry_path = project_root(root) / ".cursor" / "mcp.registry.yaml"
    registry_text = registry_path.read_text(encoding="utf-8") if registry_path.is_file() else ""

    for server in cfg.get("external_servers") or []:
        if not isinstance(server, dict) or not server.get("enabled"):
            continue
        sid = server.get("id")
        if sid and sid not in registry_text:
            errors.append(
                f"enabled external server '{sid}' in mcp.agents.yaml not found in "
                ".cursor/mcp.registry.yaml — sync registry after editing worksheet"
            )

    return errors


def add_pr_attribution_arguments(parser: Any) -> None:
    parser.add_argument(
        "--actor",
        default=None,
        help="Actor display name (default: owner.display_name from github.collaboration.yaml)",
    )
    parser.add_argument(
        "--agents",
        default=None,
        help="Agent pipeline string (overrides session + pipeline merge when set)",
    )
    parser.add_argument(
        "--pipeline",
        default=None,
        choices=PIPELINE_NAMES,
        help="Named PR phase pipeline from github.collaboration.yaml",
    )
    parser.add_argument(
        "--agents-from-session",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Merge agents from change-index.md + session-pointer.md with PR phase agents "
            "(default: true when --agents omitted)"
        ),
    )
