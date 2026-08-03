"""
File: project_cli.py
Path: .ai_infra/install/cursor_workflow/project_cli.py
Role: Thin CLI facade for GitHub Project SSOT — cmd_* delegates, re-exports, register_project_subparser.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - .cursor/skills/board-ssot/SKILL.md
 - .cursor/agents/project-board.md
Depends On:
 - .ai_infra/install/cursor_workflow/project_atomics.py
 - .ai_infra/install/cursor_workflow/gh_project_adapter.py
 - .ai_infra/install/cursor_workflow/project_recipes.py
 - .ai_infra/install/cursor_workflow/project_parser.py
 - .ai_infra/install/cursor_workflow/project_handlers.py
Notes:
 - Re-exports public symbols for tests and project_outbox late imports.
 - Heavy cmds live in project_handlers; argparse in project_parser.
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
    fetch_project_item_by_id,
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
    BODY_GATE_STATUSES,
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
    assert_body_ready_for_status,
    attribution_required,
    build_export_snapshot,
    fail,
    format_agent_attribution,
    format_note_line,
    collect_validate_item_problems,
    is_placeholder_item_id,
    is_placeholder_section_content,
    item_field_value,
    latest_notes_line,
    load_card_template,
    normalize_set_section_name,
    section_body_content,
    load_last_item_id,
    load_project_ssot,
    normalize_github_handle,
    notes_line_attributed,
    parse_board_item_from_text,
    project_templates_dir,
    render_card_template,
    replace_section_content,
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
    ensure_start_date_if_starting,
    item_start_date_value,
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
    guard_write_or_queue,
    in_progress_conflicts_for_user,
    note_successful_write,
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
                "estimate": item.get("estimate") or item.get("Estimate"),
                "start_date": item.get("start date")
                or item.get("Start date")
                or item.get("start_date"),
            }
        )
    if args.json:
        print(json.dumps({"items": out_items, "totalCount": len(out_items)}, indent=2))
    else:
        if not out_items:
            print("(no items)")
        for it in out_items:
            print(
                f"{it.get('id')}\t{it.get('status')}\t{it.get('priority') or ''}\t"
                f"{it.get('size') or ''}\t{it.get('estimate') or ''}\t{it.get('title')}"
            )
    return EXIT_OK
def cmd_create(args: argparse.Namespace) -> int:
    """Create DraftIssue or Issue per item_kind_default; --template routes to create-from-template."""
    if getattr(args, "template", None):
        return cmd_create_from_template(args)
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "create")
    if ssot is None:
        return code
    sync_policy = str(ssot.get("sync_policy") or "").strip()
    if sync_policy == "board_only":
        return fail(
            "create",
            EXIT_USAGE,
            "board_only requires create-from-template "
            "(use: project create --template slice|bug|research --priority p0|p1|p2 …)",
        )
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
    priority = str(getattr(args, "priority", None) or "").strip().lower()
    if not priority:
        return fail(
            "create-from-template",
            EXIT_USAGE,
            "--priority is required (p0|p1|p2); no silent default",
        )
    size_raw = getattr(args, "size", None)
    estimate_raw = getattr(args, "estimate", None)
    size_defaulted = not str(size_raw or "").strip()
    estimate_defaulted = estimate_raw is None or str(estimate_raw).strip() == ""
    size = "s" if size_defaulted else str(size_raw).strip().lower()
    estimate_s = "1" if estimate_defaulted else str(estimate_raw).strip()
    try:
        estimate_num = float(estimate_s)
    except ValueError:
        return fail("create-from-template", EXIT_USAGE, "--estimate must be a number")
    if estimate_num < 0:
        return fail("create-from-template", EXIT_USAGE, "estimate must be >= 0")
    guessed = size_defaulted or estimate_defaulted
    agent = str(getattr(args, "agent", None) or "").strip()
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
    if item_id:
        try:
            field_id, option_id = resolve_field_option_id(ssot, "priority", priority)
        except KeyError as exc:
            return fail(
                "create-from-template",
                EXIT_USAGE,
                f"created but priority failed: {exc}",
            )
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
            return fail(
                "create-from-template",
                EXIT_GH,
                f"created but priority failed: {detail}",
            )
        print(f"priority={priority}")
        try:
            size_fid, size_oid = resolve_field_option_id(ssot, "size", size)
            proc = run_gh(
                [
                    "project",
                    "item-edit",
                    "--project-id",
                    project_id,
                    "--id",
                    item_id,
                    "--field-id",
                    size_fid,
                    "--single-select-option-id",
                    size_oid,
                ]
            )
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "gh project item-edit failed").strip()
                print(f"create-from-template: WARN — size skipped: {detail}", file=sys.stderr)
            else:
                print(f"size={size}")
        except KeyError as exc:
            print(f"create-from-template: WARN — size skipped: {exc}", file=sys.stderr)
        ok, detail = set_item_number(ssot, item_id, "estimate", estimate_num)
        if not ok:
            print(f"create-from-template: WARN — estimate skipped: {detail}", file=sys.stderr)
        else:
            print(f"estimate={estimate_num}")
        if guessed:
            guess_note = "Size/Estimate guessed (default s/1)"
            if agent:
                n_ok, n_detail, _n_code = append_notes_helper(
                    root, ssot, item_id, agent=agent, text=guess_note, limit=100
                )
                if not n_ok:
                    print(
                        f"create-from-template: WARN — guessed Notes failed: {n_detail}",
                        file=sys.stderr,
                    )
                else:
                    print(f"notes: {guess_note}")
            else:
                print(
                    f"create-from-template: WARN — {guess_note} "
                    "(pass --agent to append Notes)",
                    file=sys.stderr,
                )
        skip_assignee = bool(getattr(args, "no_assignee", False))
        if skip_assignee:
            print("assignee=skipped:--no-assignee")
        else:
            conventions = ssot.get("conventions") if isinstance(ssot.get("conventions"), dict) else {}
            kind_default = str(conventions.get("item_kind_default") or "issue").strip().lower()
            if kind_default == "draft":
                print("assignee=skipped:draft")
            else:
                login = ""
                try:
                    login = resolve_human_github_user(root).lstrip("@")
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"create-from-template: WARN — assignee skipped: {exc}",
                        file=sys.stderr,
                    )
                if login:
                    a_ok, a_detail = set_item_assignee(ssot, item_id, login)
                    if a_ok:
                        print(f"assignee=@{a_detail.lstrip('@')}")
                    elif "DraftIssue" in a_detail or "Draft" in a_detail:
                        print("assignee=skipped:draft")
                    else:
                        print(
                            f"create-from-template: WARN — assignee skipped: {a_detail}",
                            file=sys.stderr,
                        )
                        queued = _try_queue_rate_limit(
                            root,
                            ssot,
                            cmd="create-from-template",
                            err_detail=a_detail,
                            op="set-assignee",
                            item_id=item_id,
                            agent=agent or "project-cli",
                            payload={"login": login},
                        )
                        if queued is not None:
                            print(
                                "create-from-template: assignee QUEUED due to rate-limit",
                                file=sys.stderr,
                            )
    if raw:
        print(raw)
    if item_id:
        save_last_item_id(root, item_id, title=args.title, action="create-from-template")
        print(f"item_id={item_id}")
        if status_to:
            print(f"status={status_to}")
        print("next: python3 -m cursor_workflow project claim --last --agent <agent>")
    return EXIT_OK


def read_project_readme(ssot: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (README text, error) for the Project board."""
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    proc = run_gh(
        [
            "project",
            "view",
            str(number),
            "--owner",
            owner,
            "--format",
            "json",
        ]
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "gh project view failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON from gh: {exc}"
    if not isinstance(data, dict):
        return None, "project view did not return an object"
    readme = data.get("readme")
    if readme is None:
        readme = ""
    if not isinstance(readme, str):
        return None, "project readme is not a string"
    return readme, None


def read_project_views(ssot: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Return (views, error) using a best-effort GraphQL query."""
    project_id = str(ssot["project_id"])
    query = (
        "query($id:ID!){node(id:$id){...on ProjectV2{views(first:20){nodes{"
        "name layout fields(first:20){nodes{... on ProjectV2FieldCommon{name}}}"
        "}}}}}"
    )
    proc = run_gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"id={project_id}",
        ]
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "gh project views query failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, f"invalid graphql JSON: {exc}"
    if not isinstance(data, dict):
        return None, "graphql response was not an object"
    errors = data.get("errors")
    if errors:
        msg: Any = errors
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                msg = first.get("message") or first
            else:
                msg = first
        elif isinstance(errors, dict):
            msg = errors.get("message") or errors
        return None, str(msg)
    node = (data.get("data") or {}).get("node")
    if not isinstance(node, dict):
        return None, "project views metadata unavailable"
    views_block = node.get("views")
    nodes = views_block.get("nodes") if isinstance(views_block, dict) else None
    if not isinstance(nodes, list):
        return None, "project views metadata unavailable"
    out: list[dict[str, Any]] = []
    for view in nodes:
        if not isinstance(view, dict):
            continue
        fields_block = view.get("fields")
        field_nodes = fields_block.get("nodes") if isinstance(fields_block, dict) else None
        names: list[str] = []
        if isinstance(field_nodes, list):
            for fn in field_nodes:
                if isinstance(fn, dict) and fn.get("name"):
                    names.append(str(fn["name"]))
        out.append(
            {
                "name": view.get("name"),
                "layout": view.get("layout"),
                "fields": names,
            }
        )
    return out, None


def list_project_fields(ssot: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Return (fields, error) — id, name, dataType, options for single-select."""
    project_id = str(ssot["project_id"])
    query = (
        "query($id:ID!){node(id:$id){...on ProjectV2{fields(first:50){nodes{"
        "...on ProjectV2FieldCommon{id name dataType}"
        "...on ProjectV2SingleSelectField{id name dataType options{id name}}"
        "}}}}}"
    )
    proc = run_gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"id={project_id}",
        ]
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "gh project fields query failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, f"invalid graphql JSON: {exc}"
    if not isinstance(data, dict):
        return None, "graphql response was not an object"
    errors = data.get("errors")
    if errors:
        msg: Any = errors
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                msg = first.get("message") or first
            else:
                msg = first
        return None, str(msg)
    node = (data.get("data") or {}).get("node")
    if not isinstance(node, dict):
        return None, "project fields metadata unavailable"
    fields_block = node.get("fields")
    nodes = fields_block.get("nodes") if isinstance(fields_block, dict) else None
    if not isinstance(nodes, list):
        return None, "project fields metadata unavailable"
    out: list[dict[str, Any]] = []
    for field in nodes:
        if not isinstance(field, dict) or not field.get("name"):
            continue
        entry: dict[str, Any] = {
            "id": field.get("id"),
            "name": field.get("name"),
            "dataType": field.get("dataType"),
        }
        opts = field.get("options")
        if isinstance(opts, list):
            entry["options"] = [
                {"id": o.get("id"), "name": o.get("name")}
                for o in opts
                if isinstance(o, dict)
            ]
        out.append(entry)
    return out, None


_DATA_TYPE_MAP = {
    "single_select": "SINGLE_SELECT",
    "SINGLE_SELECT": "SINGLE_SELECT",
    "number": "NUMBER",
    "NUMBER": "NUMBER",
    "date": "DATE",
    "DATE": "DATE",
    "text": "TEXT",
    "TEXT": "TEXT",
}


def ensure_board_shell_fields(
    root: Path,
    ssot: dict[str, Any],
    schema: dict[str, Any],
) -> int:
    """Create missing project fields from schema; print suggested YAML ids. Never invent option ids blindly."""
    live, err = list_project_fields(ssot)
    if err:
        return fail("board-bootstrap", EXIT_GH, err)
    live_by_name = {
        str(f.get("name") or "").strip(): f for f in (live or []) if f.get("name")
    }
    fields_block = schema.get("fields") if isinstance(schema.get("fields"), dict) else {}
    required = fields_block.get("required") if isinstance(fields_block, dict) else []
    if not isinstance(required, list):
        required = []

    project_id = str(ssot["project_id"])
    created: list[str] = []
    for spec in required:
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name") or "").strip()
        if not name or name == "Status":
            # Status is a built-in / already required by doctor — do not recreate
            continue
        if name in live_by_name:
            continue
        dtype_raw = str(spec.get("data_type") or "text").strip()
        dtype = _DATA_TYPE_MAP.get(dtype_raw, dtype_raw.upper())
        mutation = (
            "mutation($input:CreateProjectV2FieldInput!){"
            "createProjectV2Field(input:$input){projectV2Field{"
            "...on ProjectV2FieldCommon{id name dataType}"
            "...on ProjectV2SingleSelectField{id name dataType options{id name}}"
            "}}}"
        )
        input_obj: dict[str, Any] = {
            "projectId": project_id,
            "dataType": dtype,
            "name": name,
        }
        if dtype == "SINGLE_SELECT":
            opts = spec.get("options") if isinstance(spec.get("options"), list) else []
            input_obj["singleSelectOptions"] = [
                {"name": str(o), "color": "GRAY", "description": ""}
                for o in opts
                if str(o).strip()
            ]
        payload = {"query": mutation, "variables": {"input": input_obj}}
        proc = run_gh(
            ["api", "graphql", "--input", "-"],
            input_text=json.dumps(payload),
        )
        if proc.returncode != 0:
            print(
                f"board-bootstrap: WARN — create field {name!r} failed: "
                f"{(proc.stderr or proc.stdout or '').strip()}",
                file=sys.stderr,
            )
            continue
        try:
            resp = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            resp = {}
        if isinstance(resp, dict) and resp.get("errors"):
            print(
                f"board-bootstrap: WARN — create field {name!r} graphql errors: {resp.get('errors')}",
                file=sys.stderr,
            )
            continue
        created.append(name)
        print(f"board-bootstrap: created field {name!r} ({dtype})")

    # Re-list and print suggested YAML snippet
    live2, err2 = list_project_fields(ssot)
    if err2:
        print(f"board-bootstrap: WARN — re-list fields failed: {err2}", file=sys.stderr)
        return EXIT_OK
    print("board-bootstrap: suggested fields: (copy ids into github.collaboration.yaml)")
    key_map = {
        "Priority": "priority",
        "Size": "size",
        "Estimate": "estimate",
        "Start date": "start_date",
        "End date": "end_date",
        "Status": "status",
    }
    for f in live2 or []:
        fname = str(f.get("name") or "").strip()
        key = key_map.get(fname)
        if not key:
            continue
        print(f"  {key}:")
        print(f"    field_id: {f.get('id')}")
        opts = f.get("options")
        if isinstance(opts, list) and opts:
            print("    options:")
            for o in opts:
                oname = str(o.get("name") or "").strip()
                oid = o.get("id")
                if oname and oid:
                    okey = oname.lower().replace(" ", "_")
                    if key == "status":
                        status_map = {
                            "backlog": "backlog",
                            "ready": "ready",
                            "in_progress": "in_progress",
                            "in progress": "in_progress",
                            "in_review": "in_review",
                            "in review": "in_review",
                            "done": "done",
                        }
                        okey = status_map.get(oname.casefold(), okey)
                    print(f"      {okey}: {oid}")
    if created:
        print(f"board-bootstrap: ensure-fields created={','.join(created)}")
    else:
        print("board-bootstrap: ensure-fields created=(none — already present)")
    return EXIT_OK


def apply_board_shell_readme(
    root: Path,
    ssot: dict[str, Any],
    schema: dict[str, Any],
) -> int:
    """Push project-readme.md (placeholders filled) via updateProjectV2."""
    tpl_dir = project_templates_dir(root)
    readme_name = "project-readme.md"
    readme_cfg = schema.get("readme") if isinstance(schema.get("readme"), dict) else {}
    if isinstance(readme_cfg, dict) and readme_cfg.get("template"):
        readme_name = str(readme_cfg["template"])
    path = tpl_dir / readme_name
    if not path.is_file():
        return fail("board-bootstrap", EXIT_USAGE, f"missing README template {path}")
    body = path.read_text(encoding="utf-8")
    title = str(ssot.get("name") or "Board SSOT").strip()
    repo = str(ssot.get("default_repo") or "owner/repo").strip()
    body = body.replace("Your Board Name (board SSOT)", f"{title} (board SSOT)")
    body = body.replace("`owner/repo`", f"`{repo}`")
    # Strip HTML comment guide lines at top for cleaner Project README (keep placeholders notes)
    mutation = (
        "mutation($input:UpdateProjectV2Input!){"
        "updateProjectV2(input:$input){projectV2{id}}}"
    )
    input_obj = {"projectId": str(ssot["project_id"]), "readme": body}
    payload = {"query": mutation, "variables": {"input": input_obj}}
    proc = run_gh(
        ["api", "graphql", "--input", "-"],
        input_text=json.dumps(payload),
    )
    if proc.returncode != 0:
        return fail(
            "board-bootstrap",
            EXIT_GH,
            (proc.stderr or proc.stdout or "updateProjectV2 readme failed").strip(),
        )
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return fail("board-bootstrap", EXIT_GH, f"invalid graphql JSON: {exc}")
    if isinstance(data, dict) and data.get("errors"):
        return fail("board-bootstrap", EXIT_GH, str(data.get("errors")))
    print("board-bootstrap: apply-readme ok")
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
    queue_payload: dict[str, Any] = {"to": args.to}
    if _normalize_status(str(args.to)) == "in_progress":
        conventions = ssot.get("conventions") if isinstance(ssot.get("conventions"), dict) else {}
        fields_block = ssot.get("fields") if isinstance(ssot.get("fields"), dict) else {}
        start_cfg = fields_block.get("start_date") if isinstance(fields_block, dict) else None
        if conventions.get("set_start_date_on_claim", True) and isinstance(start_cfg, dict) and start_cfg.get(
            "field_id"
        ):
            queue_payload["start_date"] = utc_today_iso()
    # Body gate before precheck/queue so EXIT_VALIDATION never enqueues a doomed close.
    if _normalize_status(str(args.to)) in BODY_GATE_STATUSES:
        items, list_err = fetch_project_items(ssot, limit=100)
        if list_err:
            return fail("set-status", EXIT_GH, list_err)
        item = find_item_by_id(items, item_id)
        if item is None:
            return fail("set-status", EXIT_NOT_FOUND, f"item not found: {item_id}")
        ok_body, body_detail = assert_body_ready_for_status(ssot, item, str(args.to))
        if not ok_body:
            return fail("set-status", EXIT_VALIDATION, body_detail)
    pre = guard_write_or_queue(
        root,
        ssot,
        cmd="set-status",
        op="set-status",
        item_id=item_id,
        agent=(getattr(args, "agent", None) or "project-cli"),
        payload=queue_payload,
    )
    if pre is not None:
        return pre
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
            payload=queue_payload,
        )
        if queued is not None:
            return queued
        return fail("set-status", EXIT_GH, detail)
    print(f"set-status: {item_id} → {args.to} ({option_id})")
    note_successful_write(root, ssot)
    if _normalize_status(str(args.to)) == "in_progress":
        d_ok, d_detail, d_applied = ensure_start_date_if_starting(ssot, item_id)
        if not d_ok:
            print(f"set-status: WARN — start_date skipped: {d_detail}", file=sys.stderr)
        elif d_applied:
            print(f"set-status: start_date={d_detail}")
        elif "field_id missing" in d_detail:
            print(f"set-status: WARN — start_date skipped: {d_detail}", file=sys.stderr)
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
    agent = getattr(args, "agent", None) or "project-cli"
    if field == "estimate":
        try:
            num = float(str(args.to).strip())
        except ValueError:
            return fail("set-field", EXIT_USAGE, "--to must be a number for estimate")
        if num < 0:
            return fail("set-field", EXIT_USAGE, "estimate must be >= 0")
        pre = guard_write_or_queue(
            root,
            ssot,
            cmd="set-field",
            op="set-field",
            item_id=item_id,
            agent=agent,
            payload={"field": "estimate", "to": num},
        )
        if pre is not None:
            return pre
        ok, detail = set_item_number(ssot, item_id, "estimate", num)
        if not ok:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="set-field",
                err_detail=detail,
                op="set-field",
                item_id=item_id,
                agent=agent,
                payload={"field": "estimate", "to": num},
            )
            if queued is not None:
                return queued
            return fail("set-field", EXIT_GH, detail)
        print(f"set-field: {item_id} estimate → {num}")
        note_successful_write(root, ssot)
        return EXIT_OK
    try:
        field_id, option_id = resolve_field_option_id(ssot, field, args.to)
    except KeyError as exc:
        return fail("set-field", EXIT_USAGE, str(exc))
    pre = guard_write_or_queue(
        root,
        ssot,
        cmd="set-field",
        op="set-field",
        item_id=item_id,
        agent=agent,
        payload={"field": field, "to": args.to},
    )
    if pre is not None:
        return pre
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
            agent=agent,
            payload={"field": field, "to": args.to},
        )
        if queued is not None:
            return queued
        return fail("set-field", EXIT_GH, detail)
    print(f"set-field: {item_id} {field} → {args.to} ({option_id})")
    note_successful_write(root, ssot)
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
def cmd_set_section(args: argparse.Namespace) -> int:
    """Replace ## Acceptance or ## Rollback interior; optional Notes audit line when --agent set."""
    root = Path(args.directory).resolve()
    ssot, code = _load_enabled_ssot(root, "set-section")
    if ssot is None:
        return code
    item_id, id_code = resolve_item_id_arg(root, args, "set-section")
    if item_id is None:
        return id_code
    try:
        section = normalize_set_section_name(getattr(args, "section", "") or "")
    except ValueError as exc:
        return fail("set-section", EXIT_USAGE, str(exc))
    text = str(getattr(args, "text", None) or "").strip()
    if not text:
        return fail("set-section", EXIT_USAGE, "--text required (non-empty)")
    if is_placeholder_section_content(text):
        return fail(
            "set-section",
            EXIT_VALIDATION,
            "text must not be empty or (TBD) placeholder",
        )
    agent = (getattr(args, "agent", None) or "").strip()
    limit = int(getattr(args, "limit", 100) or 100)
    queue_payload: dict[str, Any] = {"section": section.casefold(), "text": text}
    pre = guard_write_or_queue(
        root,
        ssot,
        cmd="set-section",
        op="set-section",
        item_id=item_id,
        agent=agent or "project-cli",
        payload=queue_payload,
    )
    if pre is not None:
        return pre
    items, err = fetch_project_items(ssot, limit=limit)
    if err:
        queued = _try_queue_rate_limit(
            root,
            ssot,
            cmd="set-section",
            err_detail=err,
            op="set-section",
            item_id=item_id,
            agent=agent or "project-cli",
            payload=queue_payload,
        )
        if queued is not None:
            return queued
        return fail("set-section", EXIT_GH, err)
    item = find_item_by_id(items, item_id)
    if item is None:
        return fail("set-section", EXIT_NOT_FOUND, f"item not found: {item_id}")
    body = _item_body(item)
    try:
        new_body, changed = replace_section_content(body, section, text)
    except ValueError as exc:
        return fail("set-section", EXIT_VALIDATION, str(exc))
    if changed:
        ok, detail = edit_item_body(ssot, item_id, new_body)
        if not ok:
            queued = _try_queue_rate_limit(
                root,
                ssot,
                cmd="set-section",
                err_detail=detail,
                op="set-section",
                item_id=item_id,
                agent=agent or "project-cli",
                payload=queue_payload,
            )
            if queued is not None:
                return queued
            return fail("set-section", EXIT_GH, detail)
        note_successful_write(root, ssot)
        print(f"set-section: {item_id} — {section} updated")
    else:
        print(f"set-section: {item_id} — {section} unchanged (idempotent)")
    if agent:
        n_ok, n_detail, n_code = append_notes_helper(
            root,
            ssot,
            item_id,
            agent=agent,
            text=f"set-section {section}",
            limit=limit,
            skip_precheck=True,
        )
        if not n_ok:
            if n_code == EXIT_QUEUED:
                return n_code
            if n_code == EXIT_GH:
                queued = _try_queue_rate_limit(
                    root,
                    ssot,
                    cmd="set-section",
                    err_detail=n_detail,
                    op="append-notes",
                    item_id=item_id,
                    agent=agent,
                    payload={"text": f"set-section {section}"},
                )
                if queued is not None:
                    return queued
            return fail("set-section", n_code, f"section ok but Notes failed: {n_detail}")
    save_last_item_id(root, item_id, title=_item_title(item), action="set-section")
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
        if err_code == EXIT_QUEUED:
            return EXIT_QUEUED
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
    agent = getattr(args, "agent", None) or "project-cli"
    pre = guard_write_or_queue(
        root,
        ssot,
        cmd="set-assignee",
        op="set-assignee",
        item_id=item_id,
        agent=agent,
        payload={"login": login},
    )
    if pre is not None:
        return pre
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
    note_successful_write(root, ssot)
    return EXIT_OK
def cmd_claim(args: argparse.Namespace) -> int:
    from project_handlers import run_claim
    return run_claim(args)
def cmd_handoff(args: argparse.Namespace) -> int:
    from project_handlers import run_handoff
    return run_handoff(args)

def cmd_board_bootstrap(args: argparse.Namespace) -> int:
    from project_handlers import run_board_bootstrap

    return run_board_bootstrap(args)


def cmd_board_shell_init(args: argparse.Namespace) -> int:
    from project_handlers import run_board_shell_init

    return run_board_shell_init(args)


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
    problems, warnings = collect_validate_item_problems(ssot, item)
    for warning in warnings:
        print(f"project validate-item: WARN — {warning}", file=sys.stderr)
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
    from project_handlers import run_mention_pr
    return run_mention_pr(args)
def cmd_promote_to_issue(args: argparse.Namespace) -> int:
    from project_handlers import run_promote_to_issue
    return run_promote_to_issue(args)
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
        "python3 -m cursor_workflow project board-bootstrap --check  "
        "# read-only README/view shell check (human paste pack)"
    )
    print(
        'python3 -m cursor_workflow project create-from-template '
        f'--title "[SLICE] short-name" --template slice --status ready '
        f'--priority p1 --size s --estimate 1 --agent {agent}  '
        "# Issue: Assignee=owner.github_user (use --no-assignee to skip)"
    )
    print(
        f"python3 -m cursor_workflow project claim --last --agent {agent}  "
        "# In progress + Start date UTC + re-assert assignee if empty "
        "(also set-status/handoff→in_progress)"
    )
    print(
        f"python3 -m cursor_workflow project set-section --section acceptance "
        f"--text '- criteria…' --last --agent {agent}  "
        "# also --section rollback; required before handoff/set-status → in_review|done"
    )
    print(
        f"python3 -m cursor_workflow project promote-to-issue --last --agent {agent}  "
        "# Draft→Issue (same PVTI_); before PR"
    )
    print(
        "# Size↔Estimate points table: board-ssot skill (defaults s/1 if omitted)"
    )
    print(
        f"python3 -m cursor_workflow project handoff --last --agent {agent} "
        f"--next {nxt} --to in_review  "
        "# EXIT_VALIDATION (5) if Acceptance/Rollback still (TBD)"
    )
    print(
        f"python3 -m cursor_workflow project mention-pr --pr <n> --last --agent {agent}  "
        "# auto-promotes Draft when promote_to_issue_on_pr"
    )
    print("python3 -m cursor_workflow project validate-item --last")
    print("# If EXIT_QUEUED (6): python3 -m cursor_workflow project outbox flush")
    return EXIT_OK
def cmd_queue(args: argparse.Namespace) -> int:
    from project_handlers import run_queue
    return run_queue(args)
def cmd_outbox_status(args: argparse.Namespace) -> int:
    from project_handlers import run_outbox_status
    return run_outbox_status(args)
def cmd_outbox_flush(args: argparse.Namespace) -> int:
    from project_handlers import run_outbox_flush
    return run_outbox_flush(args)
def cmd_doctor(args: argparse.Namespace) -> int:
    from project_handlers import run_doctor
    return run_doctor(args)
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

from project_parser import register_project_subparser  # noqa: E402 — after cmd_*
