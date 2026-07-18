"""
File: project_atomics.py
Path: .ai_infra/install/cursor_workflow/project_atomics.py
Role: Pure helpers for GitHub Project SSOT — config, templates, session, status/field resolvers, notes formatting.
Used By:
 - .ai_infra/install/cursor_workflow/gh_project_adapter.py
 - .ai_infra/install/cursor_workflow/project_recipes.py
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_outbox.py (via project_cli re-exports)
Depends On:
 - .ai_infra/scripts/pr/user_settings.py (load_github_collaboration)
Notes:
 - EXIT_* codes shared across project CLI package; no gh subprocess calls here.
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


def _cli():
    """Late-bound project_cli facade for test monkeypatch compatibility."""
    import project_cli as pc

    return pc


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GH = 3
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5
EXIT_QUEUED = 6
_TEMPLATE_NAMES = ("slice", "bug", "research")
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
    user = _cli().resolve_human_github_user(root)
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
    attr = _cli().format_agent_attribution(root, agent)
    body = (text or "").strip()
    if NOTE_LINE_WITH_TIMESTAMP_RE.match(body):
        return body
    attr_match = NOTE_ATTRIBUTION_PREFIX_RE.match(body)
    if attr_match:
        prefix = attr_match.group(1)
        rest = body[len(prefix) :].lstrip()
        if rest.startswith("·"):
            rest = rest[1:].strip()
        ts = _cli().utc_note_timestamp()
        if rest:
            return f"{prefix} · {ts} · {rest}"
        return f"{prefix} · {ts}"
    ts = _cli().utc_note_timestamp()
    if not body:
        return f"{attr} · {ts}"
    return f"{attr} · {ts} · {body}"
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
def status_field_id(ssot: dict[str, Any]) -> str:
    fields = ssot.get("fields") or {}
    status = fields.get("status") or {}
    fid = status.get("field_id")
    if not fid:
        raise KeyError("project_ssot.fields.status.field_id missing")
    return str(fid)
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
