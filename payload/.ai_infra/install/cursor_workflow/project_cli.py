"""
File: project_cli.py
Path: .ai_infra/install/cursor_workflow/project_cli.py
Role: Thin CLI dispatcher for GitHub Project SSOT — cmd_* handlers and register_project_subparser.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - .cursor/skills/project-board-ssot/SKILL.md
 - .cursor/agents/project-board.md
Depends On:
 - .ai_infra/install/cursor_workflow/project_atomics.py
 - .ai_infra/install/cursor_workflow/gh_project_adapter.py
 - .ai_infra/install/cursor_workflow/project_recipes.py
Notes:
 - Re-exports public symbols for tests and project_outbox late imports.
 - Pattern A: one gh invocation per action; exit codes in project_atomics.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gh_project_adapter import (
    _REPO_ID_CACHE,
    _parse_pvti_from_gh_json,
    create_board_item,
    create_draft_item,
    create_issue_item,
    edit_item_body,
    fetch_project_items,
    find_item_by_id,
    promote_draft_item_to_issue,
    resolve_draft_content,
    resolve_item_content,
    resolve_repository_id,
    run_gh,
    set_item_assignee,
    set_item_date,
    set_item_number,
    set_item_status,
)
from project_atomics import (
    EXIT_GH,
    EXIT_NOT_FOUND,
    EXIT_OK,
    EXIT_QUEUED,
    EXIT_USAGE,
    EXIT_VALIDATION,
    NOTE_ATTRIBUTION_PREFIX_RE,
    NOTE_LINE_WITH_TIMESTAMP_RE,
    _PLACEHOLDER_RE,
    _SESSION_REL,
    _TEMPLATE_NAMES,
    _add_id_or_last,
    _import_user_settings,
    _item_body,
    _item_title,
    _normalize_status,
    append_notes_to_body,
    attribution_required,
    build_export_snapshot,
    fail,
    format_agent_attribution,
    format_note_line,
    is_placeholder_item_id,
    latest_notes_line,
    load_card_template,
    load_last_item_id,
    load_project_ssot,
    normalize_github_handle,
    notes_line_attributed,
    parse_board_item_from_text,
    project_templates_dir,
    render_card_template,
    require_enabled,
    resolve_field_option_id,
    resolve_human_github_user,
    resolve_item_id_arg,
    resolve_plain_field_id,
    resolve_status_option_id,
    save_last_item_id,
    session_last_path,
    status_field_id,
    utc_note_timestamp,
    utc_today_iso,
    validate_card_body,
)

def _load_enabled_ssot(root: Path, cmd: str) -> tuple[dict[str, Any] | None, int]:
    """Return (ssot, 0) or (None, exit_code) after printing FAIL."""
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        return None, fail(cmd, EXIT_USAGE, errs[0] if errs else "project_ssot missing")
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        return None, fail(cmd, EXIT_USAGE, enabled_errs[0])
    return ssot, EXIT_OK

from project_recipes import (
    _try_queue_rate_limit,
    append_notes_helper,
    find_items_mentioning_pr,
    in_progress_conflicts_for_user,
    resolve_item_id_for_pr,
)

def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        return fail("status", EXIT_USAGE, errs[0] if errs else "project_ssot missing")
    enabled_errs = require_enabled(ssot)
    enabled = not enabled_errs
    payload = {
        "enabled": bool(ssot.get("enabled")),
        "operational": enabled,
        "name": ssot.get("name"),
        "owner": ssot.get("owner"),
        "number": ssot.get("number"),
        "url": ssot.get("url"),
        "project_id": ssot.get("project_id"),
        "default_repo": ssot.get("default_repo"),
        "tool": ssot.get("tool", "gh"),
        "sync_policy": ssot.get("sync_policy"),
        "fallback": ssot.get("fallback"),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"enabled: {payload['enabled']}")
        print(f"operational: {payload['operational']}")
        print(f"name: {payload['name']}")
        print(f"owner: {payload['owner']}")
        print(f"number: {payload['number']}")
        print(f"url: {payload['url']}")
        print(f"project_id: {payload['project_id']}")
        print(f"sync_policy: {payload['sync_policy']}")
        print(f"fallback: {payload['fallback']}")
        if enabled_errs:
            for e in enabled_errs:
                print(f"note: {e}", file=sys.stderr)
    return EXIT_OK if enabled else EXIT_USAGE
def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "list")
    if ssot is None:
        return code
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    proc = run_gh(
        [
            "project",
            "item-list",
            str(number),
            "--owner",
            owner,
            "--format",
            "json",
            "--limit",
            str(args.limit),
        ]
    )
    if proc.returncode != 0:
        return fail(
            "list",
            EXIT_GH,
            (proc.stderr or proc.stdout or "gh project item-list failed").strip(),
        )
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return fail("list", EXIT_GH, f"invalid JSON from gh: {exc}")
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []
    filter_status = (args.status or "").strip().lower().replace("-", "_")
    if filter_status in ("inprogress",):
        filter_status = "in_progress"
    if filter_status in ("review",):
        filter_status = "in_review"
    out_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").strip().lower().replace(" ", "_")
        if filter_status and status != filter_status:
            continue
        out_items.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "status": item.get("status"),
                "priority": item.get("priority"),
                "size": item.get("size"),
            }
        )
    if args.json:
        print(json.dumps({"items": out_items, "totalCount": len(out_items)}, indent=2))
    else:
        if not out_items:
            print("(no items)")
        for it in out_items:
            print(f"{it.get('id')}\t{it.get('status')}\t{it.get('title')}")
    return EXIT_OK
def cmd_create(args: argparse.Namespace) -> int:
    """Create DraftIssue or Issue per item_kind_default; --template routes to create-from-template."""
    if getattr(args, "template", None):
        return cmd_create_from_template(args)
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "create")
    if ssot is None:
        return code
    body = args.body or ""
    sections = (ssot.get("conventions") or {}).get("body_sections") or []
    if not body and sections:
        body = "\n\n".join(f"## {s}\n\n(TBD)" for s in sections)
    item_id, raw, err = create_board_item(ssot, args.title, body)
    if err:
        return fail("create", EXIT_GH, err)
    print(raw or item_id or "")
    if item_id:
        save_last_item_id(root, item_id, title=args.title, action="create")
        print(f"item_id={item_id}")
        print("next: python3 -m cursor_workflow project claim --last --agent <agent>")
    return EXIT_OK
def cmd_create_from_template(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "create-from-template")
    if ssot is None:
        return code
    tmpl_name = getattr(args, "template", None) or "slice"
    try:
        tmpl = load_card_template(root, str(tmpl_name))
    except (ValueError, FileNotFoundError) as exc:
        return fail("create-from-template", EXIT_USAGE, str(exc))
    body = render_card_template(
        tmpl,
        acceptance=getattr(args, "acceptance", "") or "(TBD)",
        rollback=getattr(args, "rollback", "") or "(TBD)",
        notes=getattr(args, "notes", "") or "",
    )
    sections = list((ssot.get("conventions") or {}).get("body_sections") or [])
    missing = validate_card_body(body, sections)
    if missing:
        return fail(
            "create-from-template",
            EXIT_VALIDATION,
            f"template missing sections: {', '.join(missing)}",
        )
    item_id, raw, err = create_board_item(ssot, args.title, body)
    if err:
        return fail("create-from-template", EXIT_GH, err)
    status_to = (getattr(args, "status", None) or "").strip()
    if status_to and item_id:
        ok, detail = set_item_status(ssot, item_id, status_to)
        if not ok:
            return fail("create-from-template", EXIT_GH, f"created but set-status failed: {detail}")
    if raw:
        print(raw)
    if item_id:
        save_last_item_id(root, item_id, title=args.title, action="create-from-template")
        print(f"item_id={item_id}")
        if status_to:
            print(f"status={status_to}")
        print("next: python3 -m cursor_workflow project claim --last --agent <agent>")
    return EXIT_OK
def cmd_set_status(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "set-status")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "set-status")
    if item_id is None:
        return id_code
    try:
        option_id = resolve_status_option_id(ssot, args.to)
        field_id = status_field_id(ssot)
    except KeyError as exc:
        return fail("set-status", EXIT_USAGE, str(exc))
    project_id = str(ssot["project_id"])
    proc = run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            item_id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "gh project item-edit failed").strip()
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="set-status",
            err_detail=detail,
            op="set-status",
            item_id=item_id,
            agent=(getattr(args, "agent", None) or "project-cli"),
            payload={"to": args.to},
        )
        if queued is not None:
            return queued
        return fail("set-status", EXIT_GH, detail)
    print(f"set-status: {item_id} → {args.to} ({option_id})")
    return EXIT_OK
def cmd_set_field(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "set-field")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "set-field")
    if item_id is None:
        return id_code
    field = args.field.strip().lower()
    if field not in ("priority", "size", "estimate"):
        return fail(
            "set-field",
            EXIT_USAGE,
            "--field must be priority, size, or estimate",
        )
    if field == "estimate":
        try:
            num = float(str(args.to).strip())
        except ValueError:
            return fail("set-field", EXIT_USAGE, "--to must be a number for estimate")
        if num < 0:
            return fail("set-field", EXIT_USAGE, "estimate must be >= 0")
        ok, detail = set_item_number(ssot, item_id, "estimate", num)
        if not ok:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="set-field",
                err_detail=detail,
                op="set-field",
                item_id=item_id,
                agent=(getattr(args, "agent", None) or "project-cli"),
                payload={"field": "estimate", "to": num},
            )
            if queued is not None:
                return queued
            return fail("set-field", EXIT_GH, detail)
        print(f"set-field: {item_id} estimate → {num}")
        return EXIT_OK
    try:
        field_id, option_id = resolve_field_option_id(ssot, field, args.to)
    except KeyError as exc:
        return fail("set-field", EXIT_USAGE, str(exc))
    project_id = str(ssot["project_id"])
    proc = run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            item_id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "gh project item-edit failed").strip()
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="set-field",
            err_detail=detail,
            op="set-field",
            item_id=item_id,
            agent=(getattr(args, "agent", None) or "project-cli"),
            payload={"field": field, "to": args.to},
        )
        if queued is not None:
            return queued
        return fail("set-field", EXIT_GH, detail)
    print(f"set-field: {item_id} {field} → {args.to} ({option_id})")
    return EXIT_OK
def cmd_get(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "get")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "get")
    if item_id is None:
        return id_code
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        return fail("get", EXIT_GH, err)
    item = find_item_by_id(items, item_id)
    if item is None:
        return fail("get", EXIT_NOT_FOUND, f"item not found: {item_id}")
    payload = {
        "id": item.get("id"),
        "title": _item_title(item),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "size": item.get("size"),
        "start_date": item.get("start date")
        or item.get("Start date")
        or item.get("start_date"),
        "estimate": item.get("estimate") or item.get("Estimate"),
        "body": _item_body(item),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"id: {payload['id']}")
        print(f"title: {payload['title']}")
        print(f"status: {payload['status']}")
        print(f"priority: {payload['priority']}")
        print(f"size: {payload['size']}")
        print(f"start_date: {payload['start_date']}")
        print(f"estimate: {payload['estimate']}")
        print("--- body ---")
        print(payload["body"] or "(empty)")
    return EXIT_OK
def cmd_append_notes(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "append-notes")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "append-notes")
    if item_id is None:
        return id_code
    ok, detail, err_code = append_notes_helper(
        root,
        ssot,
        item_id,
        agent=getattr(args, "agent", None) or "",
        text=args.text,
        limit=args.limit,
    )
    if not ok:
        if err_code == EXIT_GH:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="append-notes",
                err_detail=detail,
                op="append-notes",
                item_id=item_id,
                agent=getattr(args, "agent", None) or "project-cli",
                payload={"text": args.text},
            )
            if queued is not None:
                return queued
        return fail("append-notes", err_code, detail)
    if detail == "idempotent":
        print(f"append-notes: {item_id} — already present (idempotent skip)")
    else:
        print(f"append-notes: {item_id} — updated")
    return EXIT_OK
def cmd_set_assignee(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "set-assignee")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "set-assignee")
    if item_id is None:
        return id_code
    login = (getattr(args, "login", None) or "").strip()
    if not login:
        try:
            login = resolve_human_github_user(root).lstrip("@")
        except Exception as exc:  # noqa: BLE001
            return fail("set-assignee", EXIT_USAGE, str(exc))
    if not login:
        return fail(
            "set-assignee",
            EXIT_USAGE,
            "no login (pass --login or set owner.github_user)",
        )
    ok, detail = set_item_assignee(ssot, item_id, login)
    if not ok:
        # DraftIssue / unsupported → validation; gh failures look like network
        if "DraftIssue" in detail or "unsupported" in detail:
            return fail("set-assignee", EXIT_VALIDATION, detail)
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="set-assignee",
            err_detail=detail,
            op="set-assignee",
            item_id=item_id,
            agent=(getattr(args, "agent", None) or "project-cli"),
            payload={"login": login},
        )
        if queued is not None:
            return queued
        return fail("set-assignee", EXIT_GH, detail)
    print(f"set-assignee: {item_id} → @{detail.lstrip('@')}")
    return EXIT_OK
def cmd_claim(args: argparse.Namespace) -> int:
    """Pattern A: set in_progress + optional assignee + attributed Notes."""
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "claim")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "claim")
    if item_id is None:
        return id_code
    agent = (getattr(args, "agent", None) or "").strip()
    if not agent:
        return fail("claim", EXIT_USAGE, "--agent required")
    try:
        user = resolve_human_github_user(root)
    except Exception as exc:  # noqa: BLE001
        return fail("claim", EXIT_USAGE, str(exc))
    if not user:
        return fail("claim", EXIT_USAGE, "owner.github_user missing")
    conventions = ssot.get("conventions") or {}
    claim_payload: dict[str, Any] = {
        "to": "in_progress",
        "text": getattr(args, "text", None) or "claimed",
    }
    # Best-effort: include planned Start date for outbox flush if rate-limited mid-flight
    fields_block = ssot.get("fields") if isinstance(ssot.get("fields"), dict) else {}
    start_cfg = fields_block.get("start_date") if isinstance(fields_block, dict) else None
    if conventions.get("set_start_date_on_claim", True) and isinstance(
        start_cfg, dict
    ) and start_cfg.get("field_id"):
        claim_payload["start_date"] = utc_today_iso()
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="claim",
            err_detail=err,
            op="claim",
            item_id=item_id,
            agent=agent,
            payload=claim_payload,
        )
        if queued is not None:
            return queued
        return fail("claim", EXIT_GH, err)
    item = find_item_by_id(items, item_id)
    if item is None:
        return fail("claim", EXIT_NOT_FOUND, f"item not found: {item_id}")
    before = _normalize_status(str(item.get("status") or ""))
    if conventions.get("one_in_progress_per_assignee", True):
        conflicts = in_progress_conflicts_for_user(
            items, user_handle=user, exclude_id=item_id
        )
        if conflicts:
            ids = ", ".join(str(c.get("id")) for c in conflicts[:5])
            return fail(
                "claim",
                EXIT_VALIDATION,
                f"one_in_progress_per_assignee: already In progress for {user}: {ids}",
            )
    ok, detail = set_item_status(ssot, item_id, "in_progress")
    if not ok:
        if "unknown status" in detail:
            return fail("claim", EXIT_USAGE, detail)
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="claim",
            err_detail=detail,
            op="claim",
            item_id=item_id,
            agent=agent,
            payload=claim_payload,
        )
        if queued is not None:
            return queued
        return fail("claim", EXIT_GH, detail)
    claim_mode = str(conventions.get("claim") or "set_assignee")
    if claim_mode == "set_assignee":
        a_ok, a_detail = set_item_assignee(ssot, item_id, user.lstrip("@"))
        if not a_ok:
            print(f"claim: WARN — assignee skipped: {a_detail}", file=sys.stderr)
        else:
            print(f"claim: assignee=@{a_detail.lstrip('@')}")
    # Tier-1: Start date = UTC today (WARN on failure; do not fail claim)
    if claim_payload.get("start_date"):
        today = str(claim_payload["start_date"])
        d_ok, d_detail = set_item_date(ssot, item_id, "start_date", today)
        if not d_ok:
            print(f"claim: WARN — start_date skipped: {d_detail}", file=sys.stderr)
        else:
            print(f"claim: start_date={d_detail}")
    note = getattr(args, "text", None) or "claimed"
    n_ok, n_detail, n_code = append_notes_helper(
        root, ssot, item_id, agent=agent, text=note, limit=args.limit
    )
    if not n_ok:
        if n_code == EXIT_GH:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="claim",
                err_detail=n_detail,
                op="append-notes",
                item_id=item_id,
                agent=agent,
                payload={"text": note},
            )
            if queued is not None:
                print(
                    "claim: status set; Notes QUEUED due to rate-limit",
                    file=sys.stderr,
                )
                return queued
        return fail("claim", n_code, f"status set but Notes failed: {n_detail}")
    save_last_item_id(root, item_id, title=_item_title(item), action="claim")
    attr = format_agent_attribution(root, agent)
    print(f"claim: {item_id} → in_progress ({n_detail})")
    print(f"item_id={item_id} · {attr} · Status={before or '?'}→in_progress")
    print(
        f"next: python3 -m cursor_workflow project handoff --last --agent {agent} "
        f"--next <agent> --to in_review"
    )
    return EXIT_OK
def cmd_handoff(args: argparse.Namespace) -> int:
    """Pattern A: attributed Notes with next=@user/agent + optional status."""
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "handoff")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "handoff")
    if item_id is None:
        return id_code
    agent = (getattr(args, "agent", None) or "").strip()
    next_agent = (getattr(args, "next", None) or "").strip().lstrip("@")
    if not agent:
        return fail("handoff", EXIT_USAGE, "--agent required")
    if not next_agent:
        return fail("handoff", EXIT_USAGE, "--next required (agent name)")
    try:
        next_attr = format_agent_attribution(root, next_agent)
        self_attr = format_agent_attribution(root, agent)
    except ValueError as exc:
        return fail("handoff", EXIT_USAGE, str(exc))
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="handoff",
            err_detail=err,
            op="handoff",
            item_id=item_id,
            agent=agent,
            payload={
                "next": next_agent,
                "to": (getattr(args, "to", None) or "").strip(),
                "note": (getattr(args, "text", None) or "").strip(),
            },
        )
        if queued is not None:
            return queued
        return fail("handoff", EXIT_GH, err)
    item = find_item_by_id(items, item_id)
    if item is None:
        return fail("handoff", EXIT_NOT_FOUND, f"item not found: {item_id}")
    before = _normalize_status(str(item.get("status") or ""))
    extra = (getattr(args, "text", None) or "").strip()
    note_core = f"next={next_attr}"
    if extra:
        note_core = f"{extra} · {note_core}"
    status_to = (getattr(args, "to", None) or "").strip()
    if status_to:
        ok, detail = set_item_status(ssot, item_id, status_to)
        if not ok:
            if "unknown" in detail.lower():
                return fail("handoff", EXIT_USAGE, detail)
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="handoff",
                err_detail=detail,
                op="handoff",
                item_id=item_id,
                agent=agent,
                payload={"next": next_agent, "to": status_to, "note": extra},
            )
            if queued is not None:
                return queued
            return fail("handoff", EXIT_GH, detail)
    n_ok, n_detail, n_code = append_notes_helper(
        root, ssot, item_id, agent=agent, text=note_core, limit=args.limit
    )
    if not n_ok:
        if n_code == EXIT_GH:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="handoff",
                err_detail=n_detail,
                op="handoff",
                item_id=item_id,
                agent=agent,
                payload={"next": next_agent, "to": status_to, "note": extra},
            )
            if queued is not None:
                return queued
        return fail("handoff", n_code, n_detail)
    save_last_item_id(root, item_id, title=_item_title(item), action="handoff")
    after = status_to or before or "?"
    print(f"handoff: {item_id} — {n_detail}")
    print(
        f"item_id={item_id} · {self_attr} · Status={before or '?'}→{after} · next={next_attr}"
    )
    return EXIT_OK
def cmd_validate_item(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "validate-item")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "validate-item")
    if item_id is None:
        return id_code
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        return fail("validate-item", EXIT_GH, err)
    item = find_item_by_id(items, item_id)
    if item is None:
        return fail("validate-item", EXIT_NOT_FOUND, f"item not found: {item_id}")
    body = _item_body(item)
    sections = list((ssot.get("conventions") or {}).get("body_sections") or [])
    missing = validate_card_body(body, sections)
    problems: list[str] = []
    if missing:
        problems.append(f"missing sections: {', '.join(missing)}")
    status = _normalize_status(str(item.get("status") or ""))
    options = ((ssot.get("fields") or {}).get("status") or {}).get("options") or {}
    if status and status not in options and str(item.get("status") or "").strip():
        if status not in set(options):
            problems.append(f"unknown status {item.get('status')!r}")
    if attribution_required(ssot):
        line = latest_notes_line(body)
        if line is not None and not notes_line_attributed(line):
            problems.append(f"latest Notes line not attributed: {line[:80]}")
    if problems:
        return fail("validate-item", EXIT_VALIDATION, "; ".join(problems))
    print(f"validate-item: {item_id} — ok")
    print(f"status={item.get('status')}")
    return EXIT_OK
def cmd_last(args: argparse.Namespace) -> int:
    """Print last saved item_id (token-efficient)."""
    root = Path(args.directory).resolve()
    lid = load_last_item_id(root)
    if not lid:
        return fail("last", EXIT_USAGE, "no last item — create-from-template first")
    print(lid)
    return EXIT_OK
def cmd_mention_pr(args: argparse.Namespace) -> int:
    """
    Append Notes with canonical PR URL + print find-by-pr candidates.
    When Draft + promote_to_issue_on_pr: promote first (FAIL on promote error).
    Does not write LINKED_PULL_REQUESTS (derived on GitHub for Issue↔PR links).
    """
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "mention-pr")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "mention-pr")
    if item_id is None:
        return id_code
    agent = (getattr(args, "agent", None) or "").strip()
    if not agent:
        return fail("mention-pr", EXIT_USAGE, "--agent required")
    pr_ref = (getattr(args, "pr", None) or "").strip()
    if not pr_ref:
        return fail("mention-pr", EXIT_USAGE, "--pr required")
    repo = str(ssot.get("default_repo") or "").strip()
    view_args = ["pr", "view", pr_ref, "--json", "url,number,title"]
    if repo:
        view_args.extend(["--repo", repo])
    proc = run_gh(view_args)
    if proc.returncode != 0:
        return fail(
            "mention-pr",
            EXIT_GH,
            (proc.stderr or proc.stdout or "gh pr view failed").strip(),
        )
    try:
        pdata = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return fail("mention-pr", EXIT_GH, "invalid gh pr view JSON")
    pr_url = str(pdata.get("url") or "").strip()
    pr_num = pdata.get("number")
    if not pr_url:
        return fail("mention-pr", EXIT_GH, "pr view missing url")
    kind, _cid, _meta, kerr = resolve_item_content(ssot, item_id)
    conventions = ssot.get("conventions") or {}
    promote_on = conventions.get("promote_to_issue_on_pr", True)
    if kind == "draft" or (kerr and "Draft" in str(kerr)):
        if promote_on:
            p_ok, p_detail, p_meta = promote_draft_item_to_issue(ssot, item_id, repo=repo)
            if not p_ok:
                queued = _try_queue_rate_limit(
                    root,
                    ssot,
                    cmd="mention-pr",
                    err_detail=p_detail,
                    op="promote-to-issue",
                    item_id=item_id,
                    agent=agent,
                    payload={"repo": repo, "text": f"PR {pr_num}: {pr_url}"},
                )
                if queued is not None:
                    return queued
                return fail(
                    "mention-pr",
                    EXIT_GH,
                    f"promote_to_issue_on_pr failed: {p_detail}",
                )
            print(
                f"mention-pr: promoted {item_id} → Issue #{p_meta.get('issue_number')}",
                file=sys.stderr,
            )
        else:
            print(
                "mention-pr: WARN — card looks DraftIssue; GitHub Linked pull requests "
                "fills for Issue-backed items. Run: project promote-to-issue --last "
                f"(promote_to_issue_on_pr={promote_on}).",
                file=sys.stderr,
            )
    note = f"PR {pr_num}: {pr_url}"
    ok, detail, err_code = append_notes_helper(
        root, ssot, item_id, agent=agent, text=note, limit=args.limit
    )
    if not ok:
        if err_code == EXIT_GH:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="mention-pr",
                err_detail=detail,
                op="append-notes",
                item_id=item_id,
                agent=agent,
                payload={"text": note},
            )
            if queued is not None:
                return queued
        return fail("mention-pr", err_code, detail)
    print(f"mention-pr: {item_id} — Notes {note}")
    items, err = fetch_project_items(ssot, limit=args.limit)
    if not err:
        matches = find_items_mentioning_pr(
            items, pr_number=str(pr_num or ""), pr_url=pr_url
        )
        if matches:
            print(
                "mention-pr: find-by-pr candidates: "
                + ", ".join(str(m.get("id")) for m in matches[:5])
            )
        else:
            print("mention-pr: find-by-pr — no other matches yet (Notes just written)")
    return EXIT_OK
def cmd_promote_to_issue(args: argparse.Namespace) -> int:
    """Convert DraftIssue project item to Issue (same PVTI_); Notes + optional assignee."""
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "promote-to-issue")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "promote-to-issue")
    if item_id is None:
        return id_code
    agent = (getattr(args, "agent", None) or "").strip()
    if not agent:
        return fail("promote-to-issue", EXIT_USAGE, "--agent required")
    repo = (getattr(args, "repo", None) or "").strip() or str(
        ssot.get("default_repo") or ""
    ).strip()
    ok, detail, meta = promote_draft_item_to_issue(ssot, item_id, repo=repo)
    if not ok:
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="promote-to-issue",
            err_detail=detail,
            op="promote-to-issue",
            item_id=item_id,
            agent=agent,
            payload={"repo": repo},
        )
        if queued is not None:
            return queued
        return fail("promote-to-issue", EXIT_GH, detail)
    issue_n = meta.get("issue_number")
    url = str(meta.get("url") or "")
    out_id = str(meta.get("item_id") or item_id)
    if meta.get("noop"):
        print(f"promote-to-issue: {out_id} already Issue #{issue_n}")
    else:
        print(f"promote-to-issue: {out_id} → Issue #{issue_n} ({url})")
    # Best-effort assignee (human)
    try:
        user = resolve_human_github_user(root)
    except Exception:  # noqa: BLE001
        user = ""
    if user:
        a_ok, a_detail = set_item_assignee(ssot, out_id, user.lstrip("@"))
        if not a_ok:
            print(f"promote-to-issue: WARN — assignee skipped: {a_detail}", file=sys.stderr)
        else:
            print(f"promote-to-issue: assignee=@{a_detail.lstrip('@')}")
    note = f"promoted to Issue #{issue_n}: {url}" if url else f"promoted to Issue #{issue_n}"
    n_ok, n_detail, n_code = append_notes_helper(
        root, ssot, out_id, agent=agent, text=note, limit=args.limit
    )
    if not n_ok:
        if n_code == EXIT_GH:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="promote-to-issue",
                err_detail=n_detail,
                op="append-notes",
                item_id=out_id,
                agent=agent,
                payload={"text": note},
            )
            if queued is not None:
                print(
                    "promote-to-issue: Issue converted; Notes QUEUED due to rate-limit",
                    file=sys.stderr,
                )
                return queued
        return fail("promote-to-issue", n_code, f"promoted but Notes failed: {n_detail}")
    save_last_item_id(root, out_id, title="", action="promote-to-issue")
    attr = format_agent_attribution(root, agent)
    print(f"promote-to-issue: Notes {n_detail}")
    print(f"item_id={out_id} · {attr} · Issue=#{issue_n}")
    print(
        f"next: python3 -m cursor_workflow project mention-pr --pr <n> --last --agent {agent}"
    )
    return EXIT_OK
def cmd_guide(args: argparse.Namespace) -> int:
    """Print safe agent recipe with --last (no placeholder ids)."""
    root = Path(args.directory).resolve()
    agent = (getattr(args, "agent", None) or "implementer").strip()
    nxt = (getattr(args, "next", None) or "verifier").strip()
    lid = load_last_item_id(root) or "(none — create first)"
    print("# Safe board recipes — use --last; never paste docs placeholders as --id")
    print(f"# last item_id: {lid}")
    print("python3 -m cursor_workflow project doctor")
    print("python3 -m cursor_workflow project outbox status")
    print(
        'python3 -m cursor_workflow project create-from-template '
        '--title "[SLICE] short-name" --template slice --status ready'
    )
    print(
        f"python3 -m cursor_workflow project claim --last --agent {agent}  "
        "# In progress + assignee (Issue) + Start date (UTC)"
    )
    print(
        f"python3 -m cursor_workflow project promote-to-issue --last --agent {agent}  "
        "# Draft→Issue (same PVTI_); before PR"
    )
    print(
        "python3 -m cursor_workflow project set-field --field estimate --to 3 --last"
    )
    print(
        f"python3 -m cursor_workflow project handoff --last --agent {agent} "
        f"--next {nxt} --to in_review"
    )
    print(
        f"python3 -m cursor_workflow project mention-pr --pr <n> --last --agent {agent}  "
        "# auto-promotes Draft when promote_to_issue_on_pr"
    )
    print("python3 -m cursor_workflow project validate-item --last")
    print("# If EXIT_QUEUED (6): python3 -m cursor_workflow project outbox flush")
    return EXIT_OK
def cmd_queue(args: argparse.Namespace) -> int:
    """Explicit enqueue (no live board write)."""
    import project_outbox as _outbox  # noqa: PLC0415

    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "queue")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "queue")
    if item_id is None:
        return id_code
    agent = (getattr(args, "agent", None) or "").strip()
    if not agent:
        return fail("queue", EXIT_USAGE, "--agent required")
    op = (getattr(args, "op", None) or "").strip()
    payload: dict[str, Any] = {}
    if op == "append-notes":
        text = (getattr(args, "text", None) or "").strip()
        if not text:
            return fail("queue", EXIT_USAGE, "--text required for append-notes")
        payload = {"text": text}
    elif op == "set-status":
        to = (getattr(args, "to", None) or "").strip()
        if not to:
            return fail("queue", EXIT_USAGE, "--to required for set-status")
        payload = {"to": to}
    elif op == "handoff":
        nxt = (getattr(args, "next", None) or "").strip()
        if not nxt:
            return fail("queue", EXIT_USAGE, "--next required for handoff")
        payload = {
            "next": nxt,
            "to": (getattr(args, "to", None) or "").strip(),
            "note": (getattr(args, "text", None) or "").strip(),
        }
    elif op == "claim":
        payload = {
            "to": (getattr(args, "to", None) or "in_progress").strip() or "in_progress",
            "text": (getattr(args, "text", None) or "claimed").strip(),
        }
    elif op == "set-assignee":
        login = (getattr(args, "login", None) or "").strip()
        if not login:
            try:
                login = resolve_human_github_user(root)
            except Exception as exc:  # noqa: BLE001
                return fail("queue", EXIT_USAGE, str(exc))
        payload = {"login": login.lstrip("@")}
    else:
        return fail(
            "queue",
            EXIT_USAGE,
            "op must be append-notes|set-status|handoff|claim|set-assignee",
        )
    entry, err = _outbox.enqueue_op(
        root, ssot, op=op, item_id=item_id, agent=agent, payload=payload
    )
    if entry is None:
        return fail("queue", EXIT_VALIDATION, err)
    print(_outbox.queued_message("queue", entry))
    return EXIT_QUEUED
def cmd_outbox_status(args: argparse.Namespace) -> int:
    import project_outbox as _outbox  # noqa: PLC0415

    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "outbox")
    if ssot is None:
        return code
    cfg = _outbox.load_outbox_config(ssot)
    path = _outbox.outbox_path(root, cfg)
    counts = _outbox.count_outbox(path)
    rl = _outbox.graphql_rate_limit()
    print(f"outbox.enabled: {cfg['enabled']}")
    print(f"outbox.path: {path}")
    print(
        f"counts: pending={counts['pending']} failed={counts['failed']} "
        f"done={counts['done']} total={counts['total']}"
    )
    if rl.get("error"):
        print(f"graphql: error — {rl['error']}")
    else:
        reset = _outbox.format_reset_iso(rl.get("reset_epoch"))
        print(
            f"graphql: remaining={rl.get('remaining')}/{rl.get('limit')} "
            f"reset={reset} min_flush={cfg['min_graphql_remaining']}"
        )
    return EXIT_OK
def cmd_outbox_flush(args: argparse.Namespace) -> int:
    import project_outbox as _outbox  # noqa: PLC0415

    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "outbox")
    if ssot is None:
        return code
    max_ops = getattr(args, "max", None)
    code_out, summary = _outbox.flush_outbox(
        root, ssot, max_ops=max_ops, limit=getattr(args, "limit", 100) or 100
    )
    if code_out != EXIT_OK:
        return fail("outbox flush", code_out, summary)
    print(f"outbox flush: {summary}")
    return EXIT_OK
def cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        return fail("doctor", EXIT_USAGE, errs[0] if errs else "project_ssot missing")
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        return fail("doctor", EXIT_USAGE, enabled_errs[0])
    try:
        status_field_id(ssot)
        resolve_status_option_id(ssot, "ready")
    except KeyError as exc:
        return fail("doctor", EXIT_USAGE, str(exc))
    user = resolve_human_github_user(root)
    if not user:
        return fail("doctor", EXIT_USAGE, "owner.github_user missing")
    tpl_dir = project_templates_dir(root)
    for name in _TEMPLATE_NAMES:
        path = tpl_dir / f"card-body-{name}.md"
        if not path.is_file():
            return fail("doctor", EXIT_USAGE, f"missing template {path}")
    import project_outbox as _outbox  # noqa: PLC0415

    cfg_pre = _outbox.load_outbox_config(ssot)
    rl_pre = _outbox.graphql_rate_limit()
    skip_live = False
    if not rl_pre.get("error"):
        try:
            rem_pre = int(rl_pre.get("remaining")) if rl_pre.get("remaining") is not None else 9999
        except (TypeError, ValueError):
            rem_pre = 9999
        if rem_pre < int(cfg_pre["min_graphql_remaining"]):
            skip_live = True
            print(
                "doctor: WARN — skipping live gh project item-list (low GraphQL quota)",
                file=sys.stderr,
            )
    if not skip_live:
        proc = run_gh(
            [
                "project",
                "item-list",
                str(ssot["number"]),
                "--owner",
                str(ssot["owner"]),
                "--format",
                "json",
                "--limit",
                "1",
            ]
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "gh project not readable").strip()
            if _outbox.is_rate_limit_error(detail):
                print(
                    "doctor: WARN — gh project item-list rate-limited; config still ok",
                    file=sys.stderr,
                )
            else:
                return fail("doctor", EXIT_GH, detail)
    print("doctor: ok")
    print(f"project: {ssot.get('name')} ({ssot.get('url')})")
    print(f"human: {user}")
    print(f"templates: {tpl_dir}")
    fields = ssot.get("fields") if isinstance(ssot.get("fields"), dict) else {}
    for key in ("start_date", "estimate"):
        block = fields.get(key) if isinstance(fields, dict) else None
        if isinstance(block, dict) and block.get("field_id"):
            print(f"tier1.{key}: {block['field_id']}")
        else:
            print(
                f"doctor: WARN — fields.{key}.field_id missing (Tier-1 claim/estimate)",
                file=sys.stderr,
            )
    conventions = ssot.get("conventions") if isinstance(ssot.get("conventions"), dict) else {}
    print(
        f"set_start_date_on_claim: {conventions.get('set_start_date_on_claim', True)}"
    )
    print(f"item_kind_default: {conventions.get('item_kind_default', 'draft')}")
    print(f"promote_to_issue_on_pr: {conventions.get('promote_to_issue_on_pr', True)}")
    default_repo = str(ssot.get("default_repo") or "").strip()
    if default_repo:
        print(f"default_repo: {default_repo}")
    else:
        print(
            "doctor: WARN — project_ssot.default_repo missing "
            "(required for promote-to-issue / item_kind_default=issue)",
            file=sys.stderr,
        )
    print(
        "doctor: note — convertProjectV2DraftIssueItemToIssue may fail on fine-grained PATs; "
        "use classic PAT with project+repo scopes if promote fails"
    )
    cfg = cfg_pre
    path = _outbox.outbox_path(root, cfg)
    counts = _outbox.count_outbox(path)
    rl = rl_pre
    print(f"outbox: enabled={cfg['enabled']} pending={counts['pending']} path={path}")
    if rl.get("error"):
        print(f"doctor: WARN — graphql rate_limit: {rl['error']}", file=sys.stderr)
    else:
        rem = rl.get("remaining")
        try:
            rem_i = int(rem) if rem is not None else -1
        except (TypeError, ValueError):
            rem_i = -1
        reset = _outbox.format_reset_iso(rl.get("reset_epoch"))
        print(f"graphql: remaining={rem}/{rl.get('limit')} reset={reset}")
        if rem_i >= 0 and rem_i < int(cfg["min_graphql_remaining"]):
            print(
                f"doctor: WARN — GraphQL remaining {rem_i} < "
                f"min_graphql_remaining {cfg['min_graphql_remaining']}; "
                f"prefer outbox queue; flush after {reset}",
                file=sys.stderr,
            )
    if counts["pending"] > 0:
        print(
            f"doctor: WARN — {counts['pending']} pending outbox ops; "
            f"run: python3 -m cursor_workflow project outbox flush",
            file=sys.stderr,
        )
    return EXIT_OK
def cmd_find_by_pr(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "find-by-pr")
    if ssot is None:
        return code
    item_id, candidates, err = resolve_item_id_for_pr(
        ssot, pr=args.pr, repo=args.repo or None, limit=args.limit
    )
    payload = {
        "item_id": item_id,
        "candidates": candidates,
        "error": err,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if item_id:
            print(item_id)
        else:
            fail("find-by-pr", EXIT_NOT_FOUND, err or "not found")
            if candidates:
                print("candidates:", ", ".join(candidates), file=sys.stderr)
            return EXIT_NOT_FOUND
    return EXIT_OK if item_id else EXIT_NOT_FOUND
def cmd_export(args: argparse.Namespace) -> int:
    """Read-only snapshot — never mutates the board."""
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "export")
    if ssot is None:
        return code
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        return fail("export", EXIT_GH, err)
    snapshot = build_export_snapshot(ssot, items)
    text = json.dumps(snapshot, indent=2) + "\n"
    if args.stdout:
        print(text, end="")
        return EXIT_OK
    out_path = Path(args.output) if args.output else (
        root / ".local" / "generated-data" / "project-board-snapshot.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path} ({snapshot['totalCount']} items)")
    if args.json:
        print(text, end="")
    return EXIT_OK
def register_project_subparser(sub: argparse._SubParsersAction) -> None:
    project = sub.add_parser(
        "project",
        help="GitHub Project SSOT (project_ssot in github.collaboration.yaml)",
    )
    project_sub = project.add_subparsers(dest="project_command", required=True)

    status_cmd = project_sub.add_parser("status", help="Show project_ssot config from user_settings")
    status_cmd.add_argument("--directory", type=Path, default=".")
    status_cmd.add_argument("--json", action="store_true")
    status_cmd.set_defaults(func=cmd_status)

    list_cmd = project_sub.add_parser("list", help="List project items (optional status filter)")
    list_cmd.add_argument("--directory", type=Path, default=".")
    list_cmd.add_argument(
        "--status",
        default="",
        help="Filter: backlog|ready|in_progress|in_review|done",
    )
    list_cmd.add_argument("--limit", type=int, default=100)
    list_cmd.add_argument("--json", action="store_true")
    list_cmd.set_defaults(func=cmd_list)

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
    create_cmd.set_defaults(func=cmd_create)

    cft = project_sub.add_parser(
        "create-from-template",
        help="Create DraftIssue from card-body template (Pattern A)",
    )
    cft.add_argument("--directory", type=Path, default=".")
    cft.add_argument("--title", required=True)
    cft.add_argument("--template", default="slice", choices=_TEMPLATE_NAMES)
    cft.add_argument("--acceptance", default="")
    cft.add_argument("--rollback", default="")
    cft.add_argument("--notes", default="")
    cft.add_argument("--status", default="", help="Optional: ready|backlog|…")
    cft.set_defaults(func=cmd_create_from_template)

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
    set_status.set_defaults(func=cmd_set_status)

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
    set_field.set_defaults(func=cmd_set_field)

    get_cmd = project_sub.add_parser("get", help="Get one project item by id")
    get_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(get_cmd)
    get_cmd.add_argument("--limit", type=int, default=100)
    get_cmd.add_argument("--json", action="store_true")
    get_cmd.set_defaults(func=cmd_get)

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
    notes_cmd.add_argument("--limit", type=int, default=100)
    notes_cmd.set_defaults(func=cmd_append_notes)

    claim_cmd = project_sub.add_parser(
        "claim",
        help="Pattern A: In progress + Notes (+ assignee when Issue-backed)",
    )
    claim_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(claim_cmd)
    claim_cmd.add_argument("--agent", required=True, help="Agent id for @user/agent Notes")
    claim_cmd.add_argument("--text", default="claimed", help="Notes text after attribution")
    claim_cmd.add_argument("--limit", type=int, default=100)
    claim_cmd.set_defaults(func=cmd_claim)

    mention_cmd = project_sub.add_parser(
        "mention-pr",
        help="Notes with PR URL + find-by-pr (auto-promote Draft when promote_to_issue_on_pr)",
    )
    mention_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(mention_cmd)
    mention_cmd.add_argument("--pr", required=True, help="PR number or URL")
    mention_cmd.add_argument("--agent", required=True)
    mention_cmd.add_argument("--limit", type=int, default=100)
    mention_cmd.set_defaults(func=cmd_mention_pr)

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
    promote_cmd.add_argument("--limit", type=int, default=100)
    promote_cmd.set_defaults(func=cmd_promote_to_issue)

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
    handoff_cmd.add_argument("--limit", type=int, default=100)
    handoff_cmd.set_defaults(func=cmd_handoff)

    val_cmd = project_sub.add_parser(
        "validate-item",
        help="Check body sections / attribution / status (exit 5 on fail)",
    )
    val_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(val_cmd)
    val_cmd.add_argument("--limit", type=int, default=100)
    val_cmd.set_defaults(func=cmd_validate_item)

    last_cmd = project_sub.add_parser("last", help="Print last saved item_id (after create/claim)")
    last_cmd.add_argument("--directory", type=Path, default=".")
    last_cmd.set_defaults(func=cmd_last)

    guide_cmd = project_sub.add_parser(
        "guide",
        help="Print safe recipes using --last (no placeholder ids)",
    )
    guide_cmd.add_argument("--directory", type=Path, default=".")
    guide_cmd.add_argument("--agent", default="implementer")
    guide_cmd.add_argument("--next", default="verifier")
    guide_cmd.set_defaults(func=cmd_guide)

    doc_cmd = project_sub.add_parser(
        "doctor",
        help="Validate project_ssot config, templates, and gh project access",
    )
    doc_cmd.add_argument("--directory", type=Path, default=".")
    doc_cmd.set_defaults(func=cmd_doctor)

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
    assignee_cmd.set_defaults(func=cmd_set_assignee)

    find_cmd = project_sub.add_parser(
        "find-by-pr", help="Resolve project item id from PR (Board-Item or body scan)"
    )
    find_cmd.add_argument("--directory", type=Path, default=".")
    find_cmd.add_argument("--pr", required=True, help="PR number or URL")
    find_cmd.add_argument("--repo", default="", help="owner/repo (defaults to project_ssot.default_repo)")
    find_cmd.add_argument("--limit", type=int, default=100)
    find_cmd.add_argument("--json", action="store_true")
    find_cmd.set_defaults(func=cmd_find_by_pr)

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
    export_cmd.add_argument("--limit", type=int, default=100)
    export_cmd.add_argument("--json", action="store_true", help="Also print JSON to stdout")
    export_cmd.add_argument("--stdout", action="store_true", help="Print JSON only (no file write)")
    export_cmd.set_defaults(func=cmd_export)

    queue_cmd = project_sub.add_parser(
        "queue",
        help="Enqueue a board op to local outbox (no live write; EXIT_QUEUED=6)",
    )
    queue_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(queue_cmd)
    queue_cmd.add_argument(
        "--op",
        required=True,
        choices=("append-notes", "set-status", "handoff", "claim", "set-assignee"),
    )
    queue_cmd.add_argument("--agent", required=True)
    queue_cmd.add_argument("--text", default="", help="Notes text / handoff note / claim text")
    queue_cmd.add_argument("--to", default="", help="Status for set-status/handoff/claim")
    queue_cmd.add_argument("--next", default="", help="Next agent for handoff")
    queue_cmd.add_argument("--login", default="", help="Assignee login for set-assignee")
    queue_cmd.set_defaults(func=cmd_queue)

    outbox_cmd = project_sub.add_parser(
        "outbox",
        help="Inspect or flush rate-limit board outbox",
    )
    outbox_sub = outbox_cmd.add_subparsers(dest="outbox_command", required=True)
    ob_status = outbox_sub.add_parser("status", help="Counts + GraphQL remaining")
    ob_status.add_argument("--directory", type=Path, default=".")
    ob_status.set_defaults(func=cmd_outbox_status)
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
    ob_flush.add_argument("--limit", type=int, default=100)
    ob_flush.set_defaults(func=cmd_outbox_flush)
