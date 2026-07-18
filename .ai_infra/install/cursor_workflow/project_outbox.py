"""
File: project_outbox.py
Path: .ai_infra/install/cursor_workflow/project_outbox.py
Role: Rate-limit-safe board outbox — enqueue/flush JSONL ops from project_ssot.outbox.
Used By:
 - .ai_infra/install/cursor_workflow/project_cli.py
Depends On:
 - project_cli helpers (attribution, set_item_*, append_notes_helper) via late imports
Notes:
 - Outbox is a local buffer, never a second Status SSOT (ADR-008).
 - Flush is pull-based; refuses when GraphQL remaining < min_graphql_remaining.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GH = 3
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5
EXIT_QUEUED = 6

_OUTBOX_OPS = frozenset(
    {"append-notes", "set-status", "handoff", "claim", "set-assignee", "set-field"}
)
_DEFAULT_PATH = ".local/generated-data/board-outbox.jsonl"
_RATE_LIMIT_RE = re.compile(
    r"rate\s*limit|API rate limit exceeded|secondary rate limit",
    re.IGNORECASE,
)


def load_outbox_config(ssot: dict[str, Any]) -> dict[str, Any]:
    """Return outbox settings with defaults."""
    raw = ssot.get("outbox") if isinstance(ssot.get("outbox"), dict) else {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "path": str(raw.get("path") or _DEFAULT_PATH).strip() or _DEFAULT_PATH,
        "min_graphql_remaining": int(raw.get("min_graphql_remaining") or 200),
        "max_flush_per_run": int(raw.get("max_flush_per_run") or 10),
        "retry_backoff_seconds": int(raw.get("retry_backoff_seconds") or 30),
    }


def outbox_path(root: Path, cfg: dict[str, Any]) -> Path:
    rel = Path(str(cfg.get("path") or _DEFAULT_PATH))
    return (root / rel).resolve() if not rel.is_absolute() else rel


def is_rate_limit_error(text: str) -> bool:
    return bool(_RATE_LIMIT_RE.search(text or ""))


def graphql_rate_limit() -> dict[str, Any]:
    """
    Read GraphQL quota via gh api rate_limit (REST — cheap).
    Returns keys: remaining, limit, reset_epoch, error (optional).
    """
    try:
        proc = subprocess.run(
            ["gh", "api", "rate_limit", "--jq", ".resources.graphql"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "remaining": None,
            "limit": None,
            "reset_epoch": None,
            "error": str(exc),
        }
    if proc.returncode != 0:
        return {
            "remaining": None,
            "limit": None,
            "reset_epoch": None,
            "error": (proc.stderr or proc.stdout or "gh api rate_limit failed").strip(),
        }
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return {
            "remaining": None,
            "limit": None,
            "reset_epoch": None,
            "error": f"invalid JSON: {exc}",
        }
    if not isinstance(data, dict):
        return {
            "remaining": None,
            "limit": None,
            "reset_epoch": None,
            "error": "graphql resource not an object",
        }
    return {
        "remaining": data.get("remaining"),
        "limit": data.get("limit"),
        "reset_epoch": data.get("reset"),
        "error": None,
    }


def format_reset_iso(reset_epoch: Any) -> str:
    try:
        ts = int(reset_epoch)
    except (TypeError, ValueError):
        return "(unknown)"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_outbox_entry(entry: dict[str, Any]) -> list[str]:
    """Lightweight validation (schema fields)."""
    errs: list[str] = []
    for key in ("id", "ts", "agent", "github_user", "op", "item_id", "payload", "status"):
        if key not in entry:
            errs.append(f"missing {key}")
    op = str(entry.get("op") or "")
    if op and op not in _OUTBOX_OPS:
        errs.append(f"unknown op {op!r}")
    status = str(entry.get("status") or "")
    if status and status not in ("pending", "done", "failed"):
        errs.append(f"bad status {status!r}")
    item_id = str(entry.get("item_id") or "")
    if item_id and (
        not re.match(r"^PVTI_[A-Za-z0-9_-]+$", item_id) or len(item_id) < 20
    ):
        errs.append(f"bad item_id {item_id!r}")
    if not isinstance(entry.get("payload"), dict):
        errs.append("payload must be object")
    attempts = entry.get("attempts", 0)
    if not isinstance(attempts, int) or attempts < 0:
        errs.append("attempts must be non-negative int")
    # payload shape checks
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
    if op == "append-notes" and not str(payload.get("text") or "").strip():
        errs.append("append-notes payload.text required")
    if op == "set-status" and not str(payload.get("to") or "").strip():
        errs.append("set-status payload.to required")
    if op == "handoff":
        if not str(payload.get("next") or "").strip():
            errs.append("handoff payload.next required")
    if op == "set-assignee" and not str(payload.get("login") or "").strip():
        errs.append("set-assignee payload.login required")
    return errs


def read_outbox_entries(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            entries.append(data)
    return entries


def write_outbox_entries(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(e, ensure_ascii=False) + "\n" for e in entries]
    path.write_text("".join(lines), encoding="utf-8")


def enqueue_op(
    root: Path,
    ssot: dict[str, Any],
    *,
    op: str,
    item_id: str,
    agent: str,
    payload: dict[str, Any],
    github_user: str = "",
) -> tuple[dict[str, Any] | None, str]:
    """
    Append a pending outbox entry. Returns (entry, error_message).
    """
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"]:
        return None, "outbox.enabled is false"
    # Late import to avoid circular import at module load
    from project_cli import (  # noqa: PLC0415
        is_placeholder_item_id,
        normalize_github_handle,
        resolve_human_github_user,
    )

    if is_placeholder_item_id(item_id):
        return None, f"placeholder item_id {item_id!r}"
    op_key = (op or "").strip()
    if op_key not in _OUTBOX_OPS:
        return None, f"unknown op {op!r}"
    agent_s = (agent or "").strip()
    if not agent_s:
        return None, "agent required"
    user = (github_user or "").strip()
    if not user:
        try:
            user = resolve_human_github_user(root)
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)
    user = normalize_github_handle(user)
    if not user:
        return None, "github_user missing"
    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "ts": _utc_now(),
        "agent": agent_s,
        "github_user": user if user.startswith("@") else f"@{user}",
        "op": op_key,
        "item_id": item_id.strip(),
        "payload": dict(payload or {}),
        "status": "pending",
        "attempts": 0,
        "last_error": None,
    }
    errs = validate_outbox_entry(entry)
    if errs:
        return None, "; ".join(errs)
    path = outbox_path(root, cfg)
    entries = read_outbox_entries(path)
    entries.append(entry)
    write_outbox_entries(path, entries)
    return entry, ""


def queued_message(cmd: str, entry: dict[str, Any]) -> str:
    return (
        f"project {cmd}: QUEUED — id={entry.get('id')} op={entry.get('op')} "
        f"item={entry.get('item_id')} · run: python3 -m cursor_workflow project outbox flush"
    )


def maybe_enqueue_on_gh_fail(
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
    """
    If outbox enabled and error looks like rate-limit, enqueue and return EXIT_QUEUED.
    Otherwise return None (caller should fail as before).
    """
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"]:
        return None
    if not is_rate_limit_error(err_detail):
        return None
    entry, err = enqueue_op(
        root,
        ssot,
        op=op,
        item_id=item_id,
        agent=agent,
        payload=payload,
    )
    if entry is None:
        print(
            f"project {cmd}: FAIL — CODE={EXIT_GH} · rate-limit and enqueue failed: {err}",
            file=sys.stderr,
        )
        return EXIT_GH
    print(queued_message(cmd, entry), file=sys.stderr)
    return EXIT_QUEUED


def count_outbox(path: Path) -> dict[str, int]:
    entries = read_outbox_entries(path)
    counts = {"pending": 0, "done": 0, "failed": 0, "total": len(entries)}
    for e in entries:
        st = str(e.get("status") or "")
        if st in counts:
            counts[st] += 1
    return counts


def apply_outbox_entry(
    root: Path,
    ssot: dict[str, Any],
    entry: dict[str, Any],
    *,
    limit: int = 100,
) -> tuple[bool, str]:
    """Apply one pending entry to the live board. Returns (ok, detail)."""
    from project_cli import (  # noqa: PLC0415
        append_notes_helper,
        format_agent_attribution,
        set_item_assignee,
        set_item_status,
    )

    op = str(entry.get("op") or "")
    item_id = str(entry.get("item_id") or "")
    agent = str(entry.get("agent") or "")
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}

    if op == "append-notes":
        ok, detail, _code = append_notes_helper(
            root,
            ssot,
            item_id,
            agent=agent,
            text=str(payload.get("text") or ""),
            limit=limit,
        )
        return ok, detail

    if op == "set-status":
        ok, detail = set_item_status(ssot, item_id, str(payload.get("to") or ""))
        return ok, detail

    if op == "set-assignee":
        login = str(payload.get("login") or "").lstrip("@")
        ok, detail = set_item_assignee(ssot, item_id, login)
        return ok, detail

    if op == "claim":
        to = str(payload.get("to") or "in_progress")
        ok, detail = set_item_status(ssot, item_id, to)
        if not ok:
            return False, detail
        start = str(payload.get("start_date") or "").strip()
        if start:
            from project_cli import set_item_date  # noqa: PLC0415

            d_ok, d_detail = set_item_date(ssot, item_id, "start_date", start)
            if not d_ok:
                return False, f"status set but start_date failed: {d_detail}"
        note = str(payload.get("text") or "claimed (outbox flush)")
        n_ok, n_detail, _ = append_notes_helper(
            root, ssot, item_id, agent=agent, text=note, limit=limit
        )
        if not n_ok:
            return False, f"status set but Notes failed: {n_detail}"
        return True, "claimed"

    if op == "set-field":
        from project_cli import (  # noqa: PLC0415
            resolve_field_option_id,
            run_gh,
            set_item_number,
        )

        field = str(payload.get("field") or "").strip().lower()
        to_val = payload.get("to")
        if field == "estimate":
            try:
                num = float(to_val)
            except (TypeError, ValueError):
                return False, "estimate payload.to must be a number"
            return set_item_number(ssot, item_id, "estimate", num)
        if field in ("priority", "size"):
            try:
                field_id, option_id = resolve_field_option_id(
                    ssot, field, str(to_val or "")
                )
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
                return False, (
                    proc.stderr or proc.stdout or "gh project item-edit failed"
                ).strip()
            return True, f"{field}={to_val}"
        return False, f"unsupported set-field {field!r}"

    if op == "handoff":
        next_agent = str(payload.get("next") or "").strip().lstrip("@")
        status_to = str(payload.get("to") or "").strip()
        extra = str(payload.get("note") or payload.get("text") or "").strip()
        if status_to:
            ok, detail = set_item_status(ssot, item_id, status_to)
            if not ok:
                return False, detail
        try:
            next_attr = format_agent_attribution(root, next_agent)
        except ValueError as exc:
            return False, str(exc)
        note_core = f"next={next_attr}"
        if extra:
            note_core = f"{extra} · {note_core}"
        n_ok, n_detail, _ = append_notes_helper(
            root, ssot, item_id, agent=agent, text=note_core, limit=limit
        )
        return n_ok, n_detail

    return False, f"unsupported op {op!r}"


def flush_outbox(
    root: Path,
    ssot: dict[str, Any],
    *,
    max_ops: int | None = None,
    limit: int = 100,
) -> tuple[int, str]:
    """
    Flush pending entries. Returns (exit_code, summary).
    """
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"]:
        return EXIT_USAGE, "outbox.enabled is false"
    path = outbox_path(root, cfg)
    rl = graphql_rate_limit()
    remaining = rl.get("remaining")
    min_rem = int(cfg["min_graphql_remaining"])
    if rl.get("error"):
        return EXIT_GH, f"cannot read rate_limit: {rl['error']}"
    try:
        rem_i = int(remaining) if remaining is not None else -1
    except (TypeError, ValueError):
        rem_i = -1
    if rem_i < min_rem:
        reset = format_reset_iso(rl.get("reset_epoch"))
        return (
            EXIT_GH,
            f"GraphQL remaining={rem_i} < min={min_rem}; refuse flush until {reset}",
        )

    cap = int(max_ops if max_ops is not None else cfg["max_flush_per_run"])
    if cap < 1:
        cap = 1
    entries = read_outbox_entries(path)
    pending_idxs = [i for i, e in enumerate(entries) if str(e.get("status")) == "pending"]
    done_n = fail_n = 0
    stopped_early = False
    backoff = int(cfg["retry_backoff_seconds"])

    applied = 0
    for idx in pending_idxs:
        if applied >= cap:
            break
        # Re-check remaining mid-batch
        rl2 = graphql_rate_limit()
        try:
            rem2 = int(rl2.get("remaining")) if rl2.get("remaining") is not None else rem_i
        except (TypeError, ValueError):
            rem2 = rem_i
        if rem2 < min_rem:
            stopped_early = True
            break

        entry = entries[idx]
        entry["attempts"] = int(entry.get("attempts") or 0) + 1
        ok, detail = apply_outbox_entry(root, ssot, entry, limit=limit)
        if ok:
            entry["status"] = "done"
            entry["last_error"] = None
            done_n += 1
        else:
            entry["last_error"] = detail
            if is_rate_limit_error(detail):
                entry["status"] = "pending"
                stopped_early = True
                write_outbox_entries(path, entries)
                return (
                    EXIT_GH,
                    f"flush stopped on rate-limit after done={done_n}; detail={detail}",
                )
            entry["status"] = "failed"
            fail_n += 1
            if backoff > 0:
                time.sleep(backoff)
        entries[idx] = entry
        applied += 1
        write_outbox_entries(path, entries)

    write_outbox_entries(path, entries)
    left = sum(1 for e in entries if str(e.get("status")) == "pending")
    summary = (
        f"flushed done={done_n} failed={fail_n} pending_left={left}"
        + (" (stopped early: low quota)" if stopped_early else "")
    )
    return EXIT_OK, summary
