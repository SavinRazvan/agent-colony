"""
File: project_parser.py
Path: .ai_infra/install/agent_colony/project_parser.py
Role: Argparse registration for `agent_colony project` subcommands.
Used By:
 - .ai_infra/install/agent_colony/project_cli.py (re-export)
 - .ai_infra/install/agent_colony/cli.py (via project_cli.register_project_subparser)
Depends On:
 - .ai_infra/install/agent_colony/project_cli.py (cmd_* handlers; late import)
 - .ai_infra/install/agent_colony/project_atomics.py (_TEMPLATE_NAMES, _add_id_or_last)
Notes:
 - Late-imports cmd_* from project_cli to avoid import cycles and preserve facade.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def register_project_subparser(sub: argparse._SubParsersAction) -> None:
    """Wire `project` subcommands; handlers live on project_cli for monkeypatch stability."""
    import project_cli as pc
    from project_atomics import _TEMPLATE_NAMES, _add_id_or_last

    project = sub.add_parser(
        "project",
        help="GitHub Project SSOT (project_ssot in github.collaboration.yaml)",
    )
    project_sub = project.add_subparsers(dest="project_command", required=True)

    status_cmd = project_sub.add_parser("status", help="Show project_ssot config from user_settings")
    status_cmd.add_argument("--directory", type=Path, default=".")
    status_cmd.add_argument("--json", action="store_true")
    status_cmd.set_defaults(func=pc.cmd_status)

    entry_cmd = project_sub.add_parser(
        "entry",
        help="Quota-aware Continuation Entry (scoped list or snapshot reuse)",
    )
    entry_cmd.add_argument("--directory", type=Path, default=".")
    entry_cmd.add_argument(
        "--also-ready",
        action="store_true",
        help="Include Ready items in addition to In progress",
    )
    entry_cmd.add_argument(
        "--force-live",
        action="store_true",
        help="Force live item-list even in conserve band (not when offline_artifacts)",
    )
    entry_cmd.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Override efficiency.entry_list_limit for live mode",
    )
    entry_cmd.add_argument(
        "--digest",
        action="store_true",
        help="One-line mode + item count + next command (token-efficient)",
    )
    entry_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON digest (mode, remaining, items, next)",
    )
    entry_cmd.set_defaults(func=pc.cmd_entry)

    list_cmd = project_sub.add_parser("list", help="List project items (optional status filter)")
    list_cmd.add_argument("--directory", type=Path, default=".")
    list_cmd.add_argument(
        "--status",
        default="",
        help="Filter: backlog|ready|in_progress|in_review|done",
    )
    list_cmd.add_argument("--limit", type=int, default=200)
    list_cmd.add_argument("--json", action="store_true")
    list_cmd.set_defaults(func=pc.cmd_list)

    create_cmd = project_sub.add_parser(
        "create", help="Create a DraftIssue on the project (--template = create-from-template)"
    )
    create_cmd.add_argument("--directory", type=Path, default=".")
    create_cmd.add_argument("--title", required=True)
    create_cmd.add_argument("--body", default="")
    create_cmd.add_argument(
        "--template",
        default="",
        help="slice|bug — use card body template (same as create-from-template)",
    )
    create_cmd.add_argument("--acceptance", default="")
    create_cmd.add_argument("--rollback", default="")
    create_cmd.add_argument("--notes", default="")
    create_cmd.add_argument(
        "--status",
        default="",
        help="Optional status after create (e.g. ready) when using --template",
    )
    create_cmd.add_argument(
        "--priority",
        default="",
        help="Required with --template: p0|p1|p2 (no silent default)",
    )
    create_cmd.add_argument(
        "--size",
        default=None,
        help="With --template: xs|s|m|l|xl (default s)",
    )
    create_cmd.add_argument(
        "--estimate",
        default=None,
        help="With --template: points number (default 1)",
    )
    create_cmd.add_argument(
        "--agent",
        default="",
        help="With --template: agent id for guessed Size/Estimate Notes",
    )
    create_cmd.add_argument(
        "--no-assignee",
        action="store_true",
        help="With --template: skip assigning owner.github_user",
    )
    create_cmd.set_defaults(func=pc.cmd_create)

    cft = project_sub.add_parser(
        "create-from-template",
        help="Create board item from card-body template (Pattern A)",
    )
    cft.add_argument("--directory", type=Path, default=".")
    cft.add_argument("--title", required=True)
    cft.add_argument("--template", default="slice", choices=_TEMPLATE_NAMES)
    cft.add_argument("--acceptance", default="")
    cft.add_argument("--rollback", default="")
    cft.add_argument("--notes", default="")
    cft.add_argument(
        "--status",
        default="ready",
        help="Status after create (default: ready)",
    )
    cft.add_argument(
        "--priority",
        required=True,
        help="Required: p0|p1|p2 (no silent default)",
    )
    cft.add_argument(
        "--size",
        default=None,
        help="xs|s|m|l|xl (default s; Notes when guessed)",
    )
    cft.add_argument(
        "--estimate",
        default=None,
        help="Points number (default 1; Notes when guessed)",
    )
    cft.add_argument(
        "--agent",
        default="",
        help="Agent id for Size/Estimate guessed Notes line",
    )
    cft.add_argument(
        "--no-assignee",
        action="store_true",
        help="Skip assigning owner.github_user on Issue create (default: assign)",
    )
    cft.set_defaults(func=pc.cmd_create_from_template)

    set_status = project_sub.add_parser("set-status", help="Set item Status from YAML option ids")
    set_status.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(set_status)
    set_status.add_argument(
        "--to",
        required=True,
        help="Logical status: backlog|ready|in_progress|in_review|done",
    )
    set_status.add_argument(
        "--agent",
        default="project-cli",
        help="Agent id for outbox attribution if rate-limited",
    )
    set_status.set_defaults(func=pc.cmd_set_status)

    set_field = project_sub.add_parser(
        "set-field",
        help="Set Priority, Size, or Estimate from YAML field ids",
    )
    set_field.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(set_field)
    set_field.add_argument(
        "--field", required=True, choices=("priority", "size", "estimate")
    )
    set_field.add_argument(
        "--to",
        required=True,
        help="e.g. p1, s, or number for estimate",
    )
    set_field.add_argument(
        "--agent",
        default="project-cli",
        help="Agent id for outbox attribution if rate-limited",
    )
    set_field.set_defaults(func=pc.cmd_set_field)

    get_cmd = project_sub.add_parser("get", help="Get one project item by id")
    get_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(get_cmd)
    get_cmd.add_argument("--limit", type=int, default=200)
    get_cmd.add_argument("--json", action="store_true")
    get_cmd.set_defaults(func=pc.cmd_get)

    notes_cmd = project_sub.add_parser(
        "append-notes",
        help="Append a line under ## Notes (prefix @user/agent when --agent set)",
    )
    notes_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(notes_cmd)
    notes_cmd.add_argument("--text", required=True)
    notes_cmd.add_argument(
        "--agent",
        default="",
        help="Agent id for attribution (required when require_attribution_on_exit)",
    )
    notes_cmd.add_argument("--limit", type=int, default=200)
    notes_cmd.set_defaults(func=pc.cmd_append_notes)

    set_section = project_sub.add_parser(
        "set-section",
        help="Replace ## Acceptance or ## Rollback (Notes stay append-only)",
    )
    set_section.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(set_section)
    set_section.add_argument(
        "--section",
        required=True,
        help="acceptance|rollback (case-insensitive)",
    )
    set_section.add_argument(
        "--text",
        required=True,
        help="New section body (must not be empty or (TBD))",
    )
    set_section.add_argument(
        "--agent",
        default="",
        help="Optional: append Notes audit line set-section Acceptance|Rollback",
    )
    set_section.add_argument("--limit", type=int, default=200)
    set_section.set_defaults(func=pc.cmd_set_section)

    claim_cmd = project_sub.add_parser(
        "claim",
        help="Pattern A: In progress + Notes (+ assignee when Issue-backed)",
    )
    claim_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(claim_cmd)
    claim_cmd.add_argument("--agent", required=True, help="Agent id for @user/agent Notes")
    claim_cmd.add_argument("--text", default="claimed", help="Notes text after attribution")
    claim_cmd.add_argument("--limit", type=int, default=200)
    claim_cmd.set_defaults(func=pc.cmd_claim)

    mention_cmd = project_sub.add_parser(
        "mention-pr",
        help="Notes with PR URL + find-by-pr (auto-promote Draft when promote_to_issue_on_pr)",
    )
    mention_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(mention_cmd)
    mention_cmd.add_argument("--pr", required=True, help="PR number or URL")
    mention_cmd.add_argument("--agent", required=True)
    mention_cmd.add_argument("--limit", type=int, default=200)
    mention_cmd.set_defaults(func=pc.cmd_mention_pr)

    promote_cmd = project_sub.add_parser(
        "promote-to-issue",
        help="Convert DraftIssue → Issue (same PVTI_); assignee + Notes",
    )
    promote_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(promote_cmd)
    promote_cmd.add_argument("--agent", required=True)
    promote_cmd.add_argument(
        "--repo",
        default="",
        help="owner/repo (defaults to project_ssot.default_repo)",
    )
    promote_cmd.add_argument("--limit", type=int, default=200)
    promote_cmd.set_defaults(func=pc.cmd_promote_to_issue)

    handoff_cmd = project_sub.add_parser(
        "handoff",
        help="Pattern A: Notes next=@user/agent + optional set-status",
    )
    handoff_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(handoff_cmd)
    handoff_cmd.add_argument("--agent", required=True)
    handoff_cmd.add_argument("--next", required=True, help="Next agent name (no @user/ needed)")
    handoff_cmd.add_argument("--to", default="", help="Optional status: in_review|done|…")
    handoff_cmd.add_argument("--text", default="", help="Optional extra Notes text")
    handoff_cmd.add_argument("--limit", type=int, default=200)
    handoff_cmd.set_defaults(func=pc.cmd_handoff)

    val_cmd = project_sub.add_parser(
        "validate-item",
        help="Check body sections / Tier-1 fields / placeholders / attribution (exit 5 on fail)",
    )
    val_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(val_cmd)
    val_cmd.add_argument("--limit", type=int, default=200)
    val_cmd.set_defaults(func=pc.cmd_validate_item)

    last_cmd = project_sub.add_parser("last", help="Print last saved item_id (after create/claim)")
    last_cmd.add_argument("--directory", type=Path, default=".")
    last_cmd.set_defaults(func=pc.cmd_last)

    guide_cmd = project_sub.add_parser(
        "guide",
        help="Print safe recipes using --last (no placeholder ids)",
    )
    guide_cmd.add_argument("--directory", type=Path, default=".")
    guide_cmd.add_argument("--agent", default="implementer")
    guide_cmd.add_argument("--next", default="verifier")
    guide_cmd.set_defaults(func=pc.cmd_guide)

    doc_cmd = project_sub.add_parser(
        "doctor",
        help="Validate project_ssot config, templates, and gh project access",
    )
    doc_cmd.add_argument("--directory", type=Path, default=".")
    doc_cmd.set_defaults(func=pc.cmd_doctor)

    boot_cmd = project_sub.add_parser(
        "board-bootstrap",
        help="Schema-aware Project shell check (optional ensure-fields / apply-readme)",
    )
    boot_cmd.add_argument("--directory", type=Path, default=".")
    boot_cmd.add_argument(
        "--check",
        action="store_true",
        help="Run readiness checks against board-shell.schema.yaml (required)",
    )
    boot_cmd.add_argument(
        "--ensure-fields",
        action="store_true",
        help="Create missing schema field definitions via createProjectV2Field; print suggested YAML ids",
    )
    boot_cmd.add_argument(
        "--apply-readme",
        action="store_true",
        help="Push project-readme.md to Project via updateProjectV2 (opt-in)",
    )
    boot_cmd.set_defaults(func=pc.cmd_board_bootstrap)

    shell_cmd = project_sub.add_parser(
        "board-shell",
        help="Board shell schema overlay helpers",
    )
    shell_sub = shell_cmd.add_subparsers(dest="board_shell_command", required=True)
    shell_init = shell_sub.add_parser(
        "init",
        help="Install board-shell.schema.yaml overlay from kit exemplar",
    )
    shell_init.add_argument("--directory", type=Path, default=".")
    shell_init.add_argument(
        "--minimal",
        action="store_true",
        help="Copy minimal 2-view overlay (Prioritized backlog + Status board)",
    )
    shell_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .local/user_settings/board-shell.schema.yaml",
    )
    shell_init.set_defaults(func=pc.cmd_board_shell_init)

    assignee_cmd = project_sub.add_parser(
        "set-assignee",
        help="Assign GitHub human user (Issue-backed); default owner.github_user",
    )
    assignee_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(assignee_cmd)
    assignee_cmd.add_argument(
        "--login",
        default="",
        help="GitHub login (default: owner.github_user from collab YAML)",
    )
    assignee_cmd.set_defaults(func=pc.cmd_set_assignee)

    close_issue_cmd = project_sub.add_parser(
        "close-linked-issue",
        help="Best-effort close of Issue linked to a merged PR's board item "
        "(opt-in via conventions.close_linked_issue_on_cleanup; caller: full-pr-workflow finalize.py)",
    )
    close_issue_cmd.add_argument("--directory", type=Path, default=".")
    close_issue_cmd.add_argument("--pr", required=True, help="PR number or URL")
    close_issue_cmd.add_argument("--repo", default="", help="owner/repo (defaults to project_ssot.default_repo)")
    close_issue_cmd.add_argument(
        "--dry-run", action="store_true", help="Print planned action without closing the Issue"
    )
    close_issue_cmd.set_defaults(func=pc.cmd_close_linked_issue)

    heal_cmd = project_sub.add_parser(
        "heal-cards",
        help="Inventory incomplete Status/Tier-1 cards; optionally set Done on CLOSED Issues",
    )
    heal_cmd.add_argument("--directory", type=Path, default=".")
    heal_cmd.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Print incomplete inventory (default)",
    )
    heal_cmd.add_argument(
        "--apply",
        action="store_true",
        help="Set Status→Done when linked Issue is CLOSED and Status empty/non-done",
    )
    heal_cmd.add_argument(
        "--fill-tier1",
        action="store_true",
        help="With --apply: fill missing Priority=p2 / Size=s / Estimate=1 when configured",
    )
    heal_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply: print planned writes without mutating the board",
    )
    heal_cmd.add_argument("--limit", type=int, default=200)
    heal_cmd.add_argument("--json", action="store_true", help="JSON inventory (check mode)")
    heal_cmd.add_argument(
        "--agent",
        default="heal-cards",
        help="Agent id for outbox attribution",
    )
    heal_cmd.set_defaults(func=pc.cmd_heal_cards)

    find_cmd = project_sub.add_parser(
        "find-by-pr", help="Resolve project item id from PR (Board-Item or body scan)"
    )
    find_cmd.add_argument("--directory", type=Path, default=".")
    find_cmd.add_argument("--pr", required=True, help="PR number or URL")
    find_cmd.add_argument("--repo", default="", help="owner/repo (defaults to project_ssot.default_repo)")
    find_cmd.add_argument("--limit", type=int, default=200)
    find_cmd.add_argument("--json", action="store_true")
    find_cmd.set_defaults(func=pc.cmd_find_by_pr)

    export_cmd = project_sub.add_parser(
        "export", help="Read-only board snapshot (never mutates Status)"
    )
    export_cmd.add_argument("--directory", type=Path, default=".")
    export_cmd.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: .local/generated-data/project-board-snapshot.json)",
    )
    export_cmd.add_argument("--limit", type=int, default=200)
    export_cmd.add_argument("--json", action="store_true", help="Also print JSON to stdout")
    export_cmd.add_argument("--stdout", action="store_true", help="Print JSON only (no file write)")
    export_cmd.add_argument(
        "--reuse-if-fresh",
        type=int,
        default=None,
        metavar="SECONDS",
        help="Reuse on-disk snapshot when younger than SECONDS "
        "(default: efficiency.export_reuse_ttl_seconds)",
    )
    export_cmd.add_argument(
        "--force",
        action="store_true",
        help="Always refresh snapshot from live item-list",
    )
    export_cmd.set_defaults(func=pc.cmd_export)

    queue_cmd = project_sub.add_parser(
        "queue",
        help="Enqueue a board op to local outbox (no live write; EXIT_QUEUED=6)",
    )
    queue_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(queue_cmd)
    queue_cmd.add_argument(
        "--op",
        required=True,
        choices=(
            "append-notes",
            "set-status",
            "set-section",
            "handoff",
            "claim",
            "set-assignee",
        ),
    )
    queue_cmd.add_argument("--agent", required=True)
    queue_cmd.add_argument("--text", default="", help="Notes text / handoff note / claim text")
    queue_cmd.add_argument("--to", default="", help="Status for set-status/handoff/claim")
    queue_cmd.add_argument("--next", default="", help="Next agent for handoff")
    queue_cmd.add_argument("--login", default="", help="Assignee login for set-assignee")
    queue_cmd.set_defaults(func=pc.cmd_queue)

    outbox_cmd = project_sub.add_parser(
        "outbox",
        help="Inspect or flush rate-limit board outbox",
    )
    outbox_sub = outbox_cmd.add_subparsers(dest="outbox_command", required=True)
    ob_status = outbox_sub.add_parser("status", help="Counts + GraphQL remaining")
    ob_status.add_argument("--directory", type=Path, default=".")
    ob_status.set_defaults(func=pc.cmd_outbox_status)
    ob_flush = outbox_sub.add_parser(
        "flush",
        help="Apply pending outbox ops (refuses if GraphQL remaining too low)",
    )
    ob_flush.add_argument("--directory", type=Path, default=".")
    ob_flush.add_argument(
        "--max",
        type=int,
        default=None,
        help="Override max_flush_per_run from settings",
    )
    ob_flush.add_argument("--limit", type=int, default=200)
    ob_flush.set_defaults(func=pc.cmd_outbox_flush)
