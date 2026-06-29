"""
File: user_settings.py
Path: .ai_infra/scripts/pr/user_settings.py
Role: Load `.local/user_settings/` YAML and render GitHub commit/PR attribution.
Used By:
 - scripts/pr/review.py, prepare.py, merge.py
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - pathlib
 - yaml (PyYAML)
Notes:
 - `.local/user_settings/` is gitignored; exemplars ship under .ai_infra/templates/user-settings/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from local_workflow_paths import DEFAULT_GITHUB_USER

GITHUB_COLLAB_REL = Path(".local") / "user_settings" / "github.collaboration.yaml"
MCP_AGENTS_REL = Path(".local") / "user_settings" / "mcp.agents.yaml"

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"
GITHUB_COLLAB_SCHEMA = SCHEMAS_DIR / "github-collaboration.schema.json"
MCP_AGENTS_SCHEMA = SCHEMAS_DIR / "mcp-agents.schema.json"

PLACEHOLDER_DISPLAY_NAMES = frozenset({"Your Full Name", "Your Name"})
PLACEHOLDER_GITHUB_USERS = frozenset({"@yourhandle", "@YourGitHubHandle", "yourhandle"})

PIPELINE_NAMES = (
    "default",
    "architecture_impacting",
    "multi_agent_feature",
    "infrastructure_integration",
)

SESSION_POINTER_REL = Path(".local") / "index-and-planning" / "current" / "session-pointer.md"
CHANGE_INDEX_REL = Path(".local") / "index-and-planning" / "current" / "change-index.md"

PR_PHASE_AGENT_SUFFIX = (
    "review-pr",
    "prepare-pr",
    "merge-pr",
)

_SKIP_AGENT_TOKENS = frozenset({"—", "-", "none", "n/a", ""})


def _project_root(root: Path | None) -> Path:
    return (root or Path.cwd()).resolve()


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return data


def _validate_against_schema(data: dict[str, Any], schema_path: Path) -> list[str]:
    if not schema_path.is_file():
        return [f"missing schema {schema_path.name}"]
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{path}: {err.message}")
    return errors


def validate_github_collaboration_schema(root: Path | None = None) -> list[str]:
    cfg = load_github_collaboration(root)
    if cfg is None:
        return [f"invalid YAML in {GITHUB_COLLAB_REL}"]
    return _validate_against_schema(cfg, GITHUB_COLLAB_SCHEMA)


def validate_mcp_agents_schema(root: Path | None = None) -> list[str]:
    cfg = load_mcp_agents(root)
    if cfg is None:
        return [f"invalid YAML in {MCP_AGENTS_REL}"]
    return _validate_against_schema(cfg, MCP_AGENTS_SCHEMA)


def github_collaboration_path(root: Path | None = None) -> Path:
    return _project_root(root) / GITHUB_COLLAB_REL


def mcp_agents_path(root: Path | None = None) -> Path:
    return _project_root(root) / MCP_AGENTS_REL


def load_github_collaboration(root: Path | None = None) -> dict[str, Any] | None:
    return _load_yaml(github_collaboration_path(root))


def load_mcp_agents(root: Path | None = None) -> dict[str, Any] | None:
    return _load_yaml(mcp_agents_path(root))


def _normalize_github_user(raw: str) -> str:
    text = raw.strip()
    if not text:
        return DEFAULT_GITHUB_USER
    return text if text.startswith("@") else f"@{text}"


def is_placeholder_owner(cfg: dict[str, Any]) -> bool:
    owner = cfg.get("owner") or {}
    name = str(owner.get("display_name", "")).strip()
    handle = _normalize_github_user(str(owner.get("github_user", "")))
    if not name or name in PLACEHOLDER_DISPLAY_NAMES:
        return True
    if handle in PLACEHOLDER_GITHUB_USERS:
        return True
    return False


def resolve_github_user(root: Path | None = None) -> str:
    cfg = load_github_collaboration(root)
    if cfg and not is_placeholder_owner(cfg):
        owner = cfg.get("owner") or {}
        return _normalize_github_user(str(owner.get("github_user", "")))
    return DEFAULT_GITHUB_USER


def resolve_default_actor(root: Path | None = None) -> str | None:
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
    base = _project_root(root)
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
        f"GitHub-User: {_normalize_github_user(str(owner['github_user']))}",
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


def validate_github_collaboration(root: Path | None = None) -> list[str]:
    errors: list[str] = []
    path = github_collaboration_path(root)
    if not path.is_file():
        errors.append(f"missing {GITHUB_COLLAB_REL} (re-run install scaffold or copy exemplars)")
        return errors

    cfg = load_github_collaboration(root)
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

    registry_path = _project_root(root) / ".cursor" / "mcp.registry.yaml"
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
