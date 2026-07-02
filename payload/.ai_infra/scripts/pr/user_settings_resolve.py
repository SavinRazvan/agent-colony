"""
File: user_settings_resolve.py
Path: .ai_infra/scripts/pr/user_settings_resolve.py
Role: Resolve PR attribution, pipelines, and session agents from trackers.
Used By:
 - user_settings.py
 - user_settings_render.py
Depends On:
 - user_settings_load.py
Notes:
 - Session agents merge change-index + session-pointer per kit handoff contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from user_settings_load import (
    GITHUB_COLLAB_REL,
    load_github_collaboration,
    normalize_github_user,
    project_root,
)

SESSION_POINTER_REL = Path(".local") / "index-and-planning" / "current" / "session-pointer.md"
CHANGE_INDEX_REL = Path(".local") / "index-and-planning" / "current" / "change-index.md"

PR_PHASE_AGENT_SUFFIX = (
    "review-pr",
    "prepare-pr",
    "merge-pr",
)

_SKIP_AGENT_TOKENS = frozenset({"—", "-", "none", "n/a", ""})


def resolve_github_user(root: Path | None = None) -> str:
    from user_settings_load import is_placeholder_owner

    cfg = load_github_collaboration(root)
    if cfg and not is_placeholder_owner(cfg):
        owner = cfg.get("owner") or {}
        return normalize_github_user(str(owner.get("github_user", "")))
    from local_workflow_paths import DEFAULT_GITHUB_USER

    return DEFAULT_GITHUB_USER


def resolve_default_actor(root: Path | None = None) -> str | None:
    from user_settings_load import is_placeholder_owner

    cfg = load_github_collaboration(root)
    if not cfg or is_placeholder_owner(cfg):
        return None
    name = str((cfg.get("owner") or {}).get("display_name", "")).strip()
    return name or None


def pipeline_agents_list(cfg: dict[str, Any] | None, pipeline: str) -> list[str]:
    if not cfg:
        return []
    pipelines = (cfg.get("pr_collaboration") or {}).get("pipelines") or {}
    spec = pipelines.get(pipeline)
    if not isinstance(spec, dict):
        return []
    agents = spec.get("agents")
    if not isinstance(agents, list):
        return []
    return [str(a).strip() for a in agents if str(a).strip()]


def pipeline_agents_string(cfg: dict[str, Any] | None, pipeline: str) -> str | None:
    agents = pipeline_agents_list(cfg, pipeline)
    if not agents:
        return None
    return " | ".join(agents)


def _normalize_agent_id(raw: str) -> str | None:
    text = raw.strip().lower()
    if not text or text in _SKIP_AGENT_TOKENS:
        return None
    return text


def _parse_markdown_table_agent_column(path: Path, *, row_prefix: str) -> list[str]:
    if not path.is_file():
        return []
    agents: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith(row_prefix):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        agent = _normalize_agent_id(parts[4])
        if agent and agent not in seen:
            seen.add(agent)
            agents.append(agent)
    return agents


def _parse_session_pointer_agents(path: Path) -> list[str]:
    if not path.is_file():
        return []
    agents: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if "**Last agent**" not in line and "**Next agent**" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        agent = _normalize_agent_id(parts[2])
        if agent and agent not in seen:
            seen.add(agent)
            agents.append(agent)
    return agents


def collect_session_agents(root: Path | None = None) -> list[str]:
    """Implementation agents from change-index (oldest→newest) then session-pointer."""
    base = project_root(root)
    merged: list[str] = []
    seen: set[str] = set()

    change_rows = _parse_markdown_table_agent_column(
        base / CHANGE_INDEX_REL,
        row_prefix="| CHG-",
    )
    for agent in reversed(change_rows):
        if agent not in seen:
            seen.add(agent)
            merged.append(agent)

    for agent in _parse_session_pointer_agents(base / SESSION_POINTER_REL):
        if agent not in seen:
            seen.add(agent)
            merged.append(agent)

    return merged


def merge_agent_lists(*groups: list[str]) -> str:
    """Dedupe agent ids preserving first-seen order across groups."""
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for raw in group:
            agent = _normalize_agent_id(raw)
            if agent and agent not in seen:
                seen.add(agent)
                merged.append(agent)
    return " | ".join(merged)


def resolve_agents_for_pr(
    *,
    root: Path | None,
    cfg: dict[str, Any] | None,
    pipeline: str,
    explicit_agents: str | None = None,
    agents_from_session: bool = True,
) -> str:
    if (explicit_agents or "").strip():
        return explicit_agents.strip()

    pipeline_agents = pipeline_agents_list(cfg, pipeline)
    if agents_from_session:
        session_agents = collect_session_agents(root)
        pr_only = [a for a in pipeline_agents if a in PR_PHASE_AGENT_SUFFIX or a == "enterprise-auditor"]
        if not pr_only:
            pr_only = list(PR_PHASE_AGENT_SUFFIX)
        return merge_agent_lists(session_agents, pr_only)

    fallback = pipeline_agents_string(cfg, pipeline)
    if fallback:
        return fallback
    raise ValueError(
        f"Missing --agents and pipeline '{pipeline}' not configured in {GITHUB_COLLAB_REL}."
    )


def resolve_pipeline_name(
    *,
    pipeline: str | None,
    arch_impacting: bool = False,
) -> str:
    if pipeline:
        return pipeline
    if arch_impacting:
        return "architecture_impacting"
    return "default"


def resolve_pr_attribution(
    *,
    root: Path | None,
    actor: str | None,
    agents: str | None,
    pipeline: str | None = None,
    arch_impacting: bool = False,
    agents_from_session: bool = True,
) -> tuple[str, str, str]:
    """Return (actor, agents_pipe_string, github_user)."""
    cfg = load_github_collaboration(root)
    resolved_actor = (actor or "").strip() or resolve_default_actor(root)
    if not resolved_actor:
        raise ValueError(
            "Missing --actor and owner.display_name not configured in "
            f"{GITHUB_COLLAB_REL}. Complete github.collaboration.yaml or pass --actor."
        )

    pipe = resolve_pipeline_name(pipeline=pipeline, arch_impacting=arch_impacting)
    resolved_agents = resolve_agents_for_pr(
        root=root,
        cfg=cfg,
        pipeline=pipe,
        explicit_agents=agents,
        agents_from_session=agents_from_session,
    )

    return resolved_actor, resolved_agents, resolve_github_user(root)
