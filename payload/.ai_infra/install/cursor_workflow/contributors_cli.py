"""
File: contributors_cli.py
Path: .ai_infra/install/cursor_workflow/contributors_cli.py
Role: CLI handlers for contributors subcommands (user_settings integration).
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - .ai_infra/scripts/pr/user_settings.py
Notes:
 - Adds scripts/pr to sys.path to import user_settings on consumer installs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _import_user_settings(root: Path):
    pr_dir = root / ".ai_infra" / "scripts" / "pr"
    if not pr_dir.is_dir():
        raise FileNotFoundError(f"missing {pr_dir}")
    pr_str = str(pr_dir)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import user_settings

    return user_settings


def cmd_contributors_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        us = _import_user_settings(root)
    except FileNotFoundError as exc:
        print(f"contributors validate: FAIL — {exc}", file=sys.stderr)
        return 1

    errors = us.validate_github_collaboration(root)
    if args.check_mcp:
        errors.extend(us.validate_mcp_agents_worksheet(root))

    if errors:
        print("contributors validate: FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    print("contributors validate: PASS")
    return 0


def cmd_contributors_show(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        us = _import_user_settings(root)
    except FileNotFoundError as exc:
        print(f"contributors show: FAIL — {exc}", file=sys.stderr)
        return 1

    cfg = us.load_github_collaboration(root)
    if not cfg:
        print(f"missing {us.GITHUB_COLLAB_REL}")
        return 1

    actor = us.resolve_default_actor(root) or "(incomplete — edit owner.display_name)"
    print(f"owner.display_name: {actor}")
    print(f"github_user: {us.resolve_github_user(root)}")
    print(f"default pipeline: {us.pipeline_agents_string(cfg, 'default') or '(missing)'}")
    print(f"architecture_impacting: {us.pipeline_agents_string(cfg, 'architecture_impacting') or '(missing)'}")
    session = us.collect_session_agents(root)
    if session:
        cfg2 = us.load_github_collaboration(root)
        merged = us.resolve_agents_for_pr(
            root=root,
            cfg=cfg2,
            pipeline="default",
            agents_from_session=True,
        )
        print(f"session agents: {' | '.join(session)}")
        print(f"merged Agent/s (default pipeline): {merged}")
    print(f"config: {us.github_collaboration_path(root)}")
    return 0


def cmd_contributors_commit_trailers(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        us = _import_user_settings(root)
        print(us.render_commit_trailers(root))
    except (FileNotFoundError, ValueError) as exc:
        print(f"contributors commit-trailers: FAIL — {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_contributors_pr_body(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        us = _import_user_settings(root)
        bullets = args.summary or ["- (describe changes)"]
        tests = args.test_plan or None
        print(
            us.render_pr_body(
                root,
                summary_bullets=bullets,
                test_plan_items=tests,
                pipeline=args.pipeline,
                agents_from_session=not args.no_agents_from_session,
            )
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"contributors pr-body: FAIL — {exc}", file=sys.stderr)
        return 1
    return 0


def register_contributors_subparser(sub: argparse._SubParsersAction) -> None:
    contrib = sub.add_parser(
        "contributors",
        help="GitHub collaboration settings from .local/user_settings/",
    )
    contrib_sub = contrib.add_subparsers(dest="contributors_command", required=True)

    validate = contrib_sub.add_parser("validate", help="Check github.collaboration.yaml (+ optional MCP worksheet)")
    validate.add_argument("--directory", type=Path, default=".")
    validate.add_argument(
        "--check-mcp",
        action="store_true",
        help="Also validate mcp.agents.yaml against mcp.registry.yaml",
    )
    validate.set_defaults(func=cmd_contributors_validate)

    show = contrib_sub.add_parser("show", help="Print resolved owner, handle, and default pipeline")
    show.add_argument("--directory", type=Path, default=".")
    show.set_defaults(func=cmd_contributors_show)

    trailers = contrib_sub.add_parser(
        "commit-trailers",
        help="Render git commit trailer block from github.collaboration.yaml",
    )
    trailers.add_argument("--directory", type=Path, default=".")
    trailers.set_defaults(func=cmd_contributors_commit_trailers)

    pr_body = contrib_sub.add_parser(
        "pr-body",
        help="Render gh pr create body from github.collaboration.yaml",
    )
    pr_body.add_argument("--directory", type=Path, default=".")
    pr_body.add_argument(
        "--pipeline",
        default="default",
        choices=("default", "architecture_impacting", "multi_agent_feature", "infrastructure_integration"),
    )
    pr_body.add_argument(
        "--summary",
        action="append",
        help="Summary bullet (repeat); prefix with - optional",
    )
    pr_body.add_argument(
        "--test-plan",
        action="append",
        dest="test_plan",
        help="Test plan checkbox item (repeat)",
    )
    pr_body.add_argument(
        "--no-agents-from-session",
        action="store_true",
        help="Use pipeline YAML only; do not merge change-index / session-pointer agents",
    )
    pr_body.set_defaults(func=cmd_contributors_pr_body)
