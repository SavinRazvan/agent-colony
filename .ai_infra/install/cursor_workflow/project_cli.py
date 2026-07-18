"""
File: project_cli.py
Path: .ai_infra/install/cursor_workflow/project_cli.py
Role: CLI for GitHub Project SSOT — load project_ssot from collab YAML; drive gh project.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - .cursor/skills/project-board-ssot/SKILL.md
 - .cursor/agents/project-board.md
Depends On:
 - .ai_infra/scripts/pr/user_settings.py (load_github_collaboration)
Notes:
 - Pattern A: one gh invocation per action; recipes (claim/handoff/create-from-template)
   are one lifecycle command each; no dual-write of local trackers.
 - DraftIssue body edits resolve PVTI_… → DI_… (+ --title); Status stays on PVTI_….
 - Notes attribution: @owner.github_user/agent · ISO-8601-UTC · text via append-notes --agent.
 - Exit codes: 0 ok; 2 usage/config; 3 gh/network; 4 not found; 5 validation; 6 queued (outbox).
 - Rate-limit outbox: project_outbox.py + project_ssot.outbox (local buffer, not SSOT).
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

# Board Pattern A exit codes
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GH = 3
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5
EXIT_QUEUED = 6

_TEMPLATE_NAMES = ("slice", "bug")
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
_SESSION_REL = Path(".local") / "generated-data" / "project-last-item.json"


def fail(cmd: str, code: int, reason: str) -> int:
    """Print structured FAIL and return exit code."""
    print(f"project {cmd}: FAIL — CODE={code} · {reason}", file=sys.stderr)
    return code


def validate_card_body(text: str, sections: list[str]) -> list[str]:
    """Return missing ## Heading names from conventions.body_sections."""
    body = text or ""
    missing: list[str] = []
    for section in sections:
        name = str(section).strip()
        if not name:
            continue
        if f"## {name}" not in body:
            missing.append(name)
    return missing


def project_templates_dir(root: Path) -> Path:
    return root / ".ai_infra" / "templates" / "project-board"


def load_card_template(root: Path, name: str) -> str:
    """Load card-body-{name}.md; raise FileNotFoundError if missing."""
    key = (name or "").strip().lower()
    if key not in _TEMPLATE_NAMES:
        raise ValueError(f"unknown template {name!r} — known: {', '.join(_TEMPLATE_NAMES)}")
    path = project_templates_dir(root) / f"card-body-{key}.md"
    if not path.is_file():
        raise FileNotFoundError(f"missing template {path}")
    return path.read_text(encoding="utf-8")


def render_card_template(
    template: str,
    *,
    acceptance: str = "(TBD)",
    rollback: str = "(TBD)",
    notes: str = "",
) -> str:
    """Replace {{acceptance}}, {{rollback}}, {{notes}} placeholders."""
    values = {
        "acceptance": (acceptance or "(TBD)").strip() or "(TBD)",
        "rollback": (rollback or "(TBD)").strip() or "(TBD)",
        "notes": (notes or "").rstrip(),
    }

    def _sub(m: re.Match[str]) -> str:
        return values.get(m.group(1), m.group(0))

    return _PLACEHOLDER_RE.sub(_sub, template).rstrip() + "\n"


def session_last_path(root: Path) -> Path:
    return root / _SESSION_REL


def save_last_item_id(root: Path, item_id: str, *, title: str = "", action: str = "") -> None:
    """Persist last board item id for --last (machine-local, not a second SSOT)."""
    path = session_last_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "project-last-item/v1",
        "item_id": item_id,
        "title": title,
        "action": action,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_last_item_id(root: Path) -> str | None:
    path = session_last_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    iid = str(data.get("item_id") or "").strip()
    return iid or None


def is_placeholder_item_id(raw: str) -> bool:
    """True for docs ellipsis / truncated ids agents must never paste."""
    s = (raw or "").strip()
    if not s:
        return True
    if "…" in s or "..." in s:
        return True
    if s in ("<id>", "$ITEM_ID", "ITEM_ID", "PVTI_", "DI_"):
        return True
    # Docs form with only punctuation after prefix
    if re.match(r"^(PVTI_|DI_)[\.…_-]*$", s):
        return True
    # Real GitHub Project item ids are long (e.g. PVTI_lAHO…); reject stubs
    if re.match(r"^PVTI_", s) and len(s) < 20:
        return True
    if re.match(r"^DI_", s) and len(s) < 12:
        return True
    return False


def resolve_item_id_arg(
    root: Path, args: argparse.Namespace, cmd: str
) -> tuple[str | None, int]:
    """Resolve --id or --last. Rejects placeholder ids (CODE=2)."""
    use_last = bool(getattr(args, "last", False))
    raw = str(getattr(args, "id", None) or "").strip()
    if use_last and raw:
        return None, fail(cmd, EXIT_USAGE, "pass --last OR --id, not both")
    if use_last:
        lid = load_last_item_id(root)
        if not lid:
            return None, fail(
                cmd,
                EXIT_USAGE,
                "no last item — run create-from-template (or claim) first, then --last",
            )
        return lid, EXIT_OK
    if not raw:
        return None, fail(cmd, EXIT_USAGE, "--id required (or use --last after create)")
    if is_placeholder_item_id(raw):
        return None, fail(
            cmd,
            EXIT_USAGE,
            f"placeholder id {raw!r} — never paste PVTI_… from docs; "
            f"use --last or the real item_id= from create output",
        )
    return raw, EXIT_OK


def _add_id_or_last(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--id",
        default="",
        help="Real PVTI_ id from create output. Prefer --last.",
    )
    parser.add_argument(
        "--last",
        action="store_true",
        help="Use item_id saved by last create/claim (.local/generated-data/project-last-item.json)",
    )


def _import_user_settings(root: Path):
    pr_dir = root / ".ai_infra" / "scripts" / "pr"
    if not pr_dir.is_dir():
        raise FileNotFoundError(f"missing {pr_dir}")
    pr_str = str(pr_dir)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import importlib

    return importlib.import_module("user_settings")


def load_project_ssot(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Return (project_ssot dict or None, error messages)."""
    errors: list[str] = []
    try:
        us = _import_user_settings(root)
    except FileNotFoundError as exc:
        return None, [str(exc)]
    cfg = us.load_github_collaboration(root)
    if cfg is None:
        return None, [f"missing or empty {us.GITHUB_COLLAB_REL}"]
    ssot = cfg.get("project_ssot")
    if not isinstance(ssot, dict):
        return None, ["project_ssot: missing block in github.collaboration.yaml"]
    return ssot, errors


def require_enabled(ssot: dict[str, Any]) -> list[str]:
    if not ssot.get("enabled"):
        fallback = ssot.get("fallback", "local_trackers")
        msg = "project_ssot.enabled is false — board SSOT inactive"
        if fallback == "local_trackers":
            msg += "; fallback: local_trackers (.local/index-and-planning/current/)"
        return [msg]
    for key in ("owner", "number", "project_id"):
        if ssot.get(key) in (None, ""):
            return [f"project_ssot.{key} is required when enabled"]
    return []


def normalize_github_handle(raw: str) -> str:
    """Ensure leading @ on a GitHub login."""
    s = (raw or "").strip()
    if not s:
        return ""
    return s if s.startswith("@") else f"@{s}"


def resolve_human_github_user(root: Path) -> str:
    """Human identity from owner.github_user (not project_ssot.owner)."""
    us = _import_user_settings(root)
    handle = us.resolve_github_user(root)
    return normalize_github_handle(str(handle or ""))


def attribution_required(ssot: dict[str, Any]) -> bool:
    conventions = ssot.get("conventions") or {}
    return bool(conventions.get("require_attribution_on_exit", True))


def format_agent_attribution(root: Path, agent: str) -> str:
    """Return @github_user/agent for board Notes."""
    user = resolve_human_github_user(root)
    agent_key = (agent or "").strip().lstrip("@")
    if not user:
        raise ValueError("owner.github_user missing — set github.collaboration.yaml")
    if not agent_key:
        raise ValueError("agent name required for attribution")
    return f"{user}/{agent_key}"


NOTE_LINE_WITH_TIMESTAMP_RE = re.compile(
    r"^@[^\s/]+/[^\s·]+\s*·\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z(?:\s*·\s*|$)"
)
NOTE_ATTRIBUTION_PREFIX_RE = re.compile(r"^(@[^\s/]+/[^\s·]+)")


def utc_note_timestamp() -> str:
    """Return current UTC timestamp for board Notes (test hook)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_note_line(root: Path, agent: str, text: str) -> str:
    """
    Prefix note with @user/agent · ISO-8601-UTC · text.
    Idempotent if text already has a UTC timestamp after attribution.
    """
    attr = format_agent_attribution(root, agent)
    body = (text or "").strip()
    if NOTE_LINE_WITH_TIMESTAMP_RE.match(body):
        return body
    attr_match = NOTE_ATTRIBUTION_PREFIX_RE.match(body)
    if attr_match:
        prefix = attr_match.group(1)
        rest = body[len(prefix) :].lstrip()
        if rest.startswith("·"):
            rest = rest[1:].strip()
        ts = utc_note_timestamp()
        if rest:
            return f"{prefix} · {ts} · {rest}"
        return f"{prefix} · {ts}"
    ts = utc_note_timestamp()
    if not body:
        return f"{attr} · {ts}"
    return f"{attr} · {ts} · {body}"


def set_item_assignee(
    ssot: dict[str, Any], item_id: str, login: str
) -> tuple[bool, str]:
    """
    Assign a GitHub human user to an Issue-backed project item.
    DraftIssue: not supported — return False with hint to use Notes or promote.
    """
    kind, cid, meta, err = resolve_item_content(ssot, item_id)
    if err or not kind or not cid:
        return False, err or "could not resolve content for assignee"
    login_clean = (login or "").strip().lstrip("@")
    if not login_clean:
        return False, "assignee login empty"

    if kind == "issue":
        meta = meta or {}
        repo = str(meta.get("repo") or ssot.get("default_repo") or "")
        gh_args = ["issue", "edit", cid, "--add-assignee", login_clean]
        if repo:
            gh_args.extend(["--repo", repo])
        proc = run_gh(gh_args)
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "gh issue edit --add-assignee failed").strip()
        return True, login_clean

    if kind == "draft":
        return (
            False,
            "DraftIssue has no GitHub Assignees; use Notes @user/agent "
            "or promote to Issue (promote_to_issue_on_pr)",
        )
    return False, f"unsupported content kind {kind!r} for assignee"


def resolve_status_option_id(ssot: dict[str, Any], logical: str) -> str:
    fields = ssot.get("fields") or {}
    status = fields.get("status") or {}
    options = status.get("options") or {}
    key = logical.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "inprogress": "in_progress",
        "in_review": "in_review",
        "review": "in_review",
    }
    key = aliases.get(key, key)
    if key not in options:
        known = ", ".join(sorted(options)) or "(none)"
        raise KeyError(f"unknown status '{logical}' — known: {known}")
    return str(options[key])


def resolve_field_option_id(ssot: dict[str, Any], field: str, logical: str) -> tuple[str, str]:
    """Return (field_id, option_id) for priority or size."""
    fields = ssot.get("fields") or {}
    block = fields.get(field)
    if not isinstance(block, dict):
        raise KeyError(f"project_ssot.fields.{field} missing")
    field_id = block.get("field_id")
    if not field_id:
        raise KeyError(f"project_ssot.fields.{field}.field_id missing")
    options = block.get("options") or {}
    key = logical.strip().lower().replace("-", "_")
    if key not in options:
        known = ", ".join(sorted(options)) or "(none)"
        raise KeyError(f"unknown {field} '{logical}' — known: {known}")
    return str(field_id), str(options[key])


def resolve_plain_field_id(ssot: dict[str, Any], field: str) -> str:
    """Return field_id for date/number fields (start_date, end_date, estimate)."""
    fields = ssot.get("fields") or {}
    block = fields.get(field)
    if not isinstance(block, dict):
        raise KeyError(f"project_ssot.fields.{field} missing")
    field_id = block.get("field_id")
    if not field_id:
        raise KeyError(f"project_ssot.fields.{field}.field_id missing")
    return str(field_id)


def utc_today_iso() -> str:
    """UTC calendar date YYYY-MM-DD for Project date fields."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def set_item_date(
    ssot: dict[str, Any], item_id: str, field_key: str, date_iso: str
) -> tuple[bool, str]:
    """Set a DATE Project field via gh project item-edit --date."""
    try:
        field_id = resolve_plain_field_id(ssot, field_key)
    except KeyError as exc:
        return False, str(exc)
    date_iso = str(date_iso or "").strip()
    if len(date_iso) != 10 or date_iso[4] != "-" or date_iso[7] != "-":
        return False, f"date must be YYYY-MM-DD, got {date_iso!r}"
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
            "--date",
            date_iso,
        ]
    )
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "gh project item-edit --date failed").strip()
    return True, date_iso


def set_item_number(
    ssot: dict[str, Any], item_id: str, field_key: str, value: float
) -> tuple[bool, str]:
    """Set a NUMBER Project field via gh project item-edit --number."""
    try:
        field_id = resolve_plain_field_id(ssot, field_key)
    except KeyError as exc:
        return False, str(exc)
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
            "--number",
            str(value),
        ]
    )
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "gh project item-edit --number failed").strip()
    return True, str(value)


def status_field_id(ssot: dict[str, Any]) -> str:
    fields = ssot.get("fields") or {}
    status = fields.get("status") or {}
    fid = status.get("field_id")
    if not fid:
        raise KeyError("project_ssot.fields.status.field_id missing")
    return str(fid)


def run_gh(args: list[str], *, timeout_s: float = 60.0) -> subprocess.CompletedProcess[str]:
    cmd = ["gh", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
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


def create_draft_item(ssot: dict[str, Any], title: str, body: str) -> tuple[str | None, str | None, str | None]:
    """
    Create DraftIssue. Returns (item_id, raw_stdout, error).
    item_id parsed from gh JSON when possible.
    """
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    gh_args = [
        "project",
        "item-create",
        str(number),
        "--owner",
        owner,
        "--title",
        title,
        "--format",
        "json",
    ]
    if body:
        gh_args.extend(["--body", body])
    proc = run_gh(gh_args)
    if proc.returncode != 0:
        return None, None, (proc.stderr or proc.stdout or "gh project item-create failed").strip()
    raw = (proc.stdout or "").strip()
    item_id: str | None = None
    try:
        data = json.loads(raw or "{}")
        if isinstance(data, dict):
            item_id = str(data.get("id") or data.get("itemId") or "") or None
    except json.JSONDecodeError:
        m = re.search(r"(PVTI_[A-Za-z0-9_-]+)", raw)
        if m:
            item_id = m.group(1)
    return item_id, raw, None


def in_progress_conflicts_for_user(
    items: list[dict[str, Any]],
    *,
    user_handle: str,
    exclude_id: str,
) -> list[dict[str, Any]]:
    """Other In progress items attributed to the same human (@user/ in body/title or assignees)."""
    user = normalize_github_handle(user_handle)
    login = user.lstrip("@").lower()
    conflicts: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("id") or "") == exclude_id:
            continue
        if _normalize_status(str(item.get("status") or "")) != "in_progress":
            continue
        blob = f"{_item_title(item)}\n{_item_body(item)}".lower()
        assignees = item.get("assignees") or item.get("assignees.login") or []
        assignee_blob = ""
        if isinstance(assignees, list):
            parts: list[str] = []
            for a in assignees:
                if isinstance(a, dict):
                    parts.append(str(a.get("login") or ""))
                else:
                    parts.append(str(a))
            assignee_blob = " ".join(parts).lower()
        else:
            assignee_blob = str(assignees).lower()
        if login and (f"@{login}/" in blob or login in assignee_blob.split()):
            conflicts.append(item)
    return conflicts


def append_notes_helper(
    root: Path,
    ssot: dict[str, Any],
    item_id: str,
    *,
    agent: str,
    text: str,
    limit: int = 100,
) -> tuple[bool, str, int]:
    """
    Append attributed Notes. Returns (ok, detail, exit_code_on_fail).
    detail is human message; on success may be 'updated' or 'idempotent'.
    """
    if attribution_required(ssot) and not str(agent).strip():
        return False, "--agent required (require_attribution_on_exit)", EXIT_USAGE
    note_text = text
    if str(agent).strip():
        try:
            note_text = format_note_line(root, str(agent), text)
        except ValueError as exc:
            return False, str(exc), EXIT_USAGE
    items, err = fetch_project_items(ssot, limit=limit)
    if err:
        return False, err, EXIT_GH
    item = find_item_by_id(items, item_id)
    if item is None:
        return False, f"item not found: {item_id}", EXIT_NOT_FOUND
    body = _item_body(item)
    new_body, changed = append_notes_to_body(body, note_text)
    if not changed:
        return True, "idempotent", EXIT_OK
    ok, detail = edit_item_body(ssot, item_id, new_body)
    if not ok:
        return False, detail, EXIT_GH
    return True, "updated", EXIT_OK


def latest_notes_line(body: str) -> str | None:
    """Last bullet under ## Notes, or None."""
    if "## Notes" not in (body or ""):
        return None
    idx = body.find("## Notes")
    rest = body[idx + len("## Notes") :]
    next_h = rest.find("\n## ")
    block = rest if next_h < 0 else rest[:next_h]
    lines = [ln.strip() for ln in block.splitlines() if ln.strip().startswith("- ")]
    if not lines:
        return None
    return lines[-1][2:].strip()


def notes_line_attributed(line: str | None) -> bool:
    if not line:
        return False
    return bool(re.match(r"^@[^\s/]+/[^\s·]+", line.strip()))


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
    """Create DraftIssue; --template routes to create-from-template."""
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
    item_id, raw, err = create_draft_item(ssot, args.title, body)
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
    item_id, raw, err = create_draft_item(ssot, args.title, body)
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


def _try_queue_rate_limit(
    root: Path,
    ssot: dict[str, Any],
    *,
    cmd: str,
    err_detail: str,
    op: str,
    item_id: str,
    agent: str,
    payload: dict[str, Any],
) -> int | None:
    """Delegate to project_outbox.maybe_enqueue_on_gh_fail."""
    import project_outbox as _outbox  # noqa: PLC0415

    return _outbox.maybe_enqueue_on_gh_fail(
        root,
        ssot,
        cmd=cmd,
        err_detail=err_detail,
        op=op,
        item_id=item_id,
        agent=agent,
        payload=payload,
    )


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


def _normalize_status(raw: str) -> str:
    key = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in ("inprogress",):
        return "in_progress"
    if key in ("review",):
        return "in_review"
    return key


def _item_body(item: dict[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, dict):
        body = content.get("body")
        if isinstance(body, str):
            return body
    body = item.get("body")
    return body if isinstance(body, str) else ""


def _item_title(item: dict[str, Any]) -> str:
    title = item.get("title")
    if isinstance(title, str) and title:
        return title
    content = item.get("content")
    if isinstance(content, dict):
        t = content.get("title")
        if isinstance(t, str):
            return t
    return ""


def fetch_project_items(ssot: dict[str, Any], *, limit: int = 100) -> tuple[list[dict[str, Any]], str | None]:
    """Return (items, error). Each item keeps gh JSON fields plus normalized helpers."""
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
            str(limit),
        ]
    )
    if proc.returncode != 0:
        return [], (proc.stderr or proc.stdout or "gh project item-list failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return [], f"invalid JSON from gh: {exc}"
    raw = data.get("items") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return [], None
    items: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            items.append(item)
    return items, None


def find_item_by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    for item in items:
        if str(item.get("id") or "") == item_id:
            return item
    return None


def append_notes_to_body(body: str, text: str) -> tuple[str, bool]:
    """
    Append text under ## Notes. Returns (new_body, changed).
    Idempotent when the exact text line is already present.
    """
    note_line = text.strip()
    if not note_line:
        return body, False
    if note_line in (body or ""):
        return body, False
    body = body or ""
    marker = "## Notes"
    if marker in body:
        # Append after the Notes heading block (before next ## or end).
        idx = body.find(marker)
        rest = body[idx + len(marker) :]
        next_h = rest.find("\n## ")
        if next_h >= 0:
            insert_at = idx + len(marker) + next_h
            new_body = body[:insert_at].rstrip() + f"\n\n- {note_line}\n" + body[insert_at:]
        else:
            new_body = body.rstrip() + f"\n\n- {note_line}\n"
    else:
        new_body = body.rstrip() + f"\n\n## Notes\n\n- {note_line}\n"
    return new_body, True


def parse_board_item_from_text(text: str) -> str | None:
    """Extract PVTI_… from a Board-Item: line in PR or card body."""
    m = re.search(r"(?i)Board-Item:\s*(PVTI_[A-Za-z0-9_-]+)", text or "")
    return m.group(1) if m else None


def find_items_mentioning_pr(
    items: list[dict[str, Any]],
    *,
    pr_number: str,
    pr_url: str = "",
) -> list[dict[str, Any]]:
    """Items whose body/title mention the PR number or URL; prefer in_review/in_progress."""
    needle_num = str(pr_number).strip().lstrip("#")
    needles = [n for n in (pr_url, f"#{needle_num}", f"/pull/{needle_num}", needle_num) if n]
    matches: list[dict[str, Any]] = []
    for item in items:
        blob = f"{_item_title(item)}\n{_item_body(item)}"
        if not any(n and n in blob for n in needles):
            continue
        status = _normalize_status(str(item.get("status") or ""))
        if status in ("in_review", "in_progress", "ready"):
            matches.append(item)
        else:
            matches.append(item)
    # Prefer in_review then in_progress
    def rank(it: dict[str, Any]) -> int:
        s = _normalize_status(str(it.get("status") or ""))
        return {"in_review": 0, "in_progress": 1, "ready": 2}.get(s, 9)

    matches.sort(key=rank)
    return matches


def resolve_item_id_for_pr(
    ssot: dict[str, Any],
    *,
    pr: str,
    repo: str | None = None,
    limit: int = 100,
) -> tuple[str | None, list[str], str | None]:
    """
    Resolve project item id for a PR.
    Returns (item_id | None, candidate_ids, error | None).
    Prefers Board-Item in PR body; else body/URL scan of active cards.
    """
    pr_ref = str(pr).strip()
    # Accept URL or number
    pr_number = pr_ref.rstrip("/").split("/")[-1] if "/" in pr_ref else pr_ref.lstrip("#")
    repo_flag = repo or str(ssot.get("default_repo") or "")
    view_args = ["pr", "view", pr_number, "--json", "body,url,number"]
    if repo_flag:
        view_args.extend(["--repo", repo_flag])
    proc = run_gh(view_args)
    pr_body = ""
    pr_url = ""
    if proc.returncode == 0:
        try:
            pdata = json.loads(proc.stdout or "{}")
            pr_body = str(pdata.get("body") or "")
            pr_url = str(pdata.get("url") or "")
            if pdata.get("number") is not None:
                pr_number = str(pdata["number"])
        except json.JSONDecodeError:
            pass
    board_item = parse_board_item_from_text(pr_body)
    if board_item:
        return board_item, [board_item], None

    items, err = fetch_project_items(ssot, limit=limit)
    if err:
        return None, [], err
    matches = find_items_mentioning_pr(items, pr_number=pr_number, pr_url=pr_url)
    ids = [str(m.get("id")) for m in matches if m.get("id")]
    if len(ids) == 1:
        return ids[0], ids, None
    if len(ids) > 1:
        return None, ids, "ambiguous: multiple project items mention this PR"
    return None, [], "no project item found for this PR (add Board-Item: PVTI_… to PR body)"


def resolve_item_content(
    ssot: dict[str, Any], item_id: str
) -> tuple[str | None, str | None, dict[str, Any] | None, str | None]:
    """
    Resolve project item content for body edits.

    Returns (kind, content_id_or_number, meta, error) where kind is:
      - "draft" → content_id is DI_…, meta has title
      - "issue" → content_id is issue number str, meta has title/repo hints
      - None on error
    If item_id already starts with DI_, treat as draft content id (title fetched if possible).
    """
    iid = (item_id or "").strip()
    if not iid:
        return None, None, None, "empty item id"

    if iid.startswith("DI_"):
        query = "query($id:ID!){node(id:$id){...on DraftIssue{id title}}}"
        proc = run_gh(["api", "graphql", "-f", f"query={query}", "-f", f"id={iid}"])
        title = ""
        if proc.returncode == 0:
            try:
                data = json.loads(proc.stdout or "{}")
                node = (data.get("data") or {}).get("node") or {}
                if isinstance(node, dict) and node.get("title"):
                    title = str(node["title"])
            except json.JSONDecodeError:
                pass
        return "draft", iid, {"title": title}, None

    query = (
        "query($id:ID!){node(id:$id){...on ProjectV2Item{id content{"
        "__typename "
        "...on DraftIssue{id title body} "
        "...on Issue{id number title body repository{nameWithOwner}}"
        "}}}}"
    )
    proc = run_gh(["api", "graphql", "-f", f"query={query}", "-f", f"id={iid}"])
    if proc.returncode != 0:
        return None, None, None, (proc.stderr or proc.stdout or "graphql resolve failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, None, None, f"invalid graphql JSON: {exc}"
    errors = data.get("errors")
    if errors:
        return None, None, None, str(errors[0].get("message") if isinstance(errors[0], dict) else errors)
    node = (data.get("data") or {}).get("node")
    if not isinstance(node, dict):
        return None, None, None, f"project item not found: {iid}"
    content = node.get("content")
    if not isinstance(content, dict):
        return None, None, None, f"project item has no content: {iid}"
    typename = str(content.get("__typename") or "")
    if typename == "DraftIssue":
        di = str(content.get("id") or "")
        if not di.startswith("DI_"):
            return None, None, None, f"unexpected draft id: {di!r}"
        return "draft", di, {"title": str(content.get("title") or "")}, None
    if typename == "Issue":
        number = content.get("number")
        if number is None:
            return None, None, None, "issue content missing number"
        repo = ""
        repository = content.get("repository")
        if isinstance(repository, dict):
            repo = str(repository.get("nameWithOwner") or "")
        if not repo:
            repo = str(ssot.get("default_repo") or "")
        return (
            "issue",
            str(number),
            {
                "title": str(content.get("title") or ""),
                "repo": repo,
                "body": str(content.get("body") or ""),
            },
            None,
        )
    return None, None, None, f"unsupported content type {typename!r} for body edit"


# Back-compat alias used in plan / docs
def resolve_draft_content(
    ssot: dict[str, Any], item_id: str
) -> tuple[str | None, str | None, str | None]:
    """Return (content_id, title, error) for DraftIssue; error if not a draft."""
    kind, cid, meta, err = resolve_item_content(ssot, item_id)
    if err:
        return None, None, err
    if kind != "draft":
        return None, None, f"not a DraftIssue (got {kind})"
    title = (meta or {}).get("title") or ""
    return cid, title, None


def edit_item_body(ssot: dict[str, Any], item_id: str, body: str) -> tuple[bool, str]:
    """
    Update card body. Agents pass PVTI_…; DraftIssue edits require DI_… + --title.
    Issue-backed items use gh issue edit.
    """
    kind, cid, meta, err = resolve_item_content(ssot, item_id)
    if err or not kind or not cid:
        return False, err or "could not resolve content id for body edit"
    meta = meta or {}
    project_id = str(ssot["project_id"])

    if kind == "draft":
        title = str(meta.get("title") or "").strip() or "(untitled)"
        proc = run_gh(
            [
                "project",
                "item-edit",
                "--project-id",
                project_id,
                "--id",
                cid,
                "--title",
                title,
                "--body",
                body,
            ]
        )
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "gh project item-edit --body failed").strip()
        return True, "ok"

    if kind == "issue":
        repo = str(meta.get("repo") or ssot.get("default_repo") or "")
        gh_args = ["issue", "edit", cid, "--body", body]
        if repo:
            gh_args.extend(["--repo", repo])
        proc = run_gh(gh_args)
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "gh issue edit --body failed").strip()
        return True, "ok"

    return False, f"unsupported content kind {kind!r}"


def set_item_status(ssot: dict[str, Any], item_id: str, logical: str) -> tuple[bool, str]:
    try:
        option_id = resolve_status_option_id(ssot, logical)
        field_id = status_field_id(ssot)
    except KeyError as exc:
        return False, str(exc)
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
        return False, (proc.stderr or proc.stdout or "gh project item-edit failed").strip()
    return True, option_id


def build_export_snapshot(ssot: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    """Read-only snapshot shape for project export / DRIFT-010."""
    out_items: list[dict[str, Any]] = []
    for item in items:
        body = _item_body(item)
        excerpt = body if len(body) <= 500 else body[:497] + "..."
        out_items.append(
            {
                "id": item.get("id"),
                "title": _item_title(item),
                "status": item.get("status"),
                "status_normalized": _normalize_status(str(item.get("status") or "")),
                "priority": item.get("priority"),
                "size": item.get("size"),
                "start_date": item.get("start date")
                or item.get("Start date")
                or item.get("start_date"),
                "estimate": item.get("estimate") or item.get("Estimate"),
                "body_excerpt": excerpt,
                "updated_at": item.get("updatedAt") or item.get("updated_at"),
            }
        )
    return {
        "schema": "project-board-snapshot/v1",
        "project": {
            "name": ssot.get("name"),
            "owner": ssot.get("owner"),
            "number": ssot.get("number"),
            "url": ssot.get("url"),
            "project_id": ssot.get("project_id"),
            "default_repo": ssot.get("default_repo"),
        },
        "items": out_items,
        "totalCount": len(out_items),
    }


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
    # DraftIssue warn (Linked PRs column needs Issue)
    kind, _cid, _meta, kerr = resolve_item_content(ssot, item_id)
    conventions = ssot.get("conventions") or {}
    if kind == "draft" or (kerr and "Draft" in str(kerr)):
        print(
            "mention-pr: WARN — card looks DraftIssue; GitHub Linked pull requests "
            "fills for Issue-backed items. Promote/convert to Issue when linking a PR "
            f"(promote_to_issue_on_pr={conventions.get('promote_to_issue_on_pr', True)}).",
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
    # Verification print (find-by-pr style)
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
        "# In progress + assignee + Start date (UTC)"
    )
    print(
        "python3 -m cursor_workflow project set-field --field estimate --to 3 --last"
    )
    print(
        f"python3 -m cursor_workflow project handoff --last --agent {agent} "
        f"--next {nxt} --to in_review"
    )
    print(
        f"python3 -m cursor_workflow project mention-pr --pr <n> --last --agent {agent}"
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
        help="Notes with PR URL + find-by-pr check (Linked PRs column is derived)",
    )
    mention_cmd.add_argument("--directory", type=Path, default=".")
    _add_id_or_last(mention_cmd)
    mention_cmd.add_argument("--pr", required=True, help="PR number or URL")
    mention_cmd.add_argument("--agent", required=True)
    mention_cmd.add_argument("--limit", type=int, default=100)
    mention_cmd.set_defaults(func=cmd_mention_pr)

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
