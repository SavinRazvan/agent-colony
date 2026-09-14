"""
File: project_outbox.py
Path: .ai_infra/install/agent_colony/project_outbox.py
Role: Rate-limit-safe board outbox — enqueue/flush JSONL ops + API cooldown circuit-breaker.
Used By:
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/project_handlers.py
Depends On:
 - project_cli helpers (attribution, set_item_*, append_notes_helper) via late imports
Notes:
 - Outbox is a local buffer, never a second Status SSOT (ADR-008).
 - Flush is pull-based; refuses when GraphQL remaining < min_graphql_remaining.
 - Cached REST rate_limit precheck (TTL) before Pattern A writes; pending-op dedupe.
 - board-api-cooldown.json hard-skips live API while limited_until is in the future (EXIT_QUEUED=6).
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
    {
        "append-notes",
        "set-status",
        "set-section",
        "handoff",
        "claim",
        "set-assignee",
        "set-field",
        "promote-to-issue",
    }
)
_DEFAULT_PATH = ".local/generated-data/board-outbox.jsonl"
_DEFAULT_QUOTA_CACHE = ".local/generated-data/graphql-quota-cache.json"
_DEFAULT_COOLDOWN = ".local/generated-data/board-api-cooldown.json"
_RATE_LIMIT_RE = re.compile(
    r"rate\s*limit|API rate limit exceeded|secondary rate limit|"
    r"\b429\b|retry\s*later|wait a few minutes|too many requests",
    re.IGNORECASE,
)
_SECONDARY_LIMIT_RE = re.compile(
    r"secondary\s*rate\s*limit|abuse.?detection|too many requests",
    re.IGNORECASE,
)
_RETRY_AFTER_RE = re.compile(
    r"(?:retry[_-]?after|wait)\s*[:=]?\s*(\d+)\s*(?:s|sec|seconds)?",
    re.IGNORECASE,
)
_FORBIDDEN_RE = re.compile(r"\b403\b|\bForbidden\b", re.IGNORECASE)
_PERM_FORBIDDEN_RE = re.compile(
    r"resource not accessible|not authorized|permission|access denied|"
    r"must have .+ permission|insufficient",
    re.IGNORECASE,
)
_SCOPE_MISS_RE = re.compile(
    r"missing required scopes|required scopes|authentication token is missing",
    re.IGNORECASE,
)
_DEDUPE_PAYLOAD_KEYS: dict[str, tuple[str, ...]] = {
    "append-notes": ("text",),
    "set-status": (
        "to",
        "start_date",
        "end_date",
        "allow_skip_verifier",
        "skip_verifier_rationale",
    ),
    "set-section": ("section", "text"),
    "claim": ("to", "text", "start_date"),
    "handoff": (
        "next",
        "to",
        "note",
        "text",
        "allow_skip_verifier",
        "skip_verifier_rationale",
    ),
    "set-assignee": ("login",),
    "set-field": ("field", "to", "name", "value"),
    "promote-to-issue": ("repo",),
}


def load_outbox_config(ssot: dict[str, Any]) -> dict[str, Any]:
    """Return outbox settings with defaults."""
    raw = ssot.get("outbox") if isinstance(ssot.get("outbox"), dict) else {}
    return {
        "enabled": bool(raw.get("enabled", True)),
        "path": str(raw.get("path") or _DEFAULT_PATH).strip() or _DEFAULT_PATH,
        "min_graphql_remaining": int(raw.get("min_graphql_remaining") or 200),
        "max_flush_per_run": int(raw.get("max_flush_per_run") or 10),
        "retry_backoff_seconds": int(raw.get("retry_backoff_seconds") or 30),
        "precheck_writes": bool(raw.get("precheck_writes", True)),
        "quota_cache_ttl_seconds": int(raw.get("quota_cache_ttl_seconds") or 45),
        "quota_cache_path": str(raw.get("quota_cache_path") or _DEFAULT_QUOTA_CACHE).strip()
        or _DEFAULT_QUOTA_CACHE,
        "dedupe_pending": bool(raw.get("dedupe_pending", True)),
        "cooldown_path": str(raw.get("cooldown_path") or _DEFAULT_COOLDOWN).strip()
        or _DEFAULT_COOLDOWN,
        "cooldown_floor_seconds": int(raw.get("cooldown_floor_seconds") or 60),
        "secondary_limit_floor_seconds": int(
            raw.get("secondary_limit_floor_seconds") or 120
        ),
        "coalesce_pending_notes": bool(raw.get("coalesce_pending_notes", True)),
        "max_pending_notes_per_item": int(raw.get("max_pending_notes_per_item") or 3),
    }


def outbox_path(root: Path, cfg: dict[str, Any]) -> Path:
    rel = Path(str(cfg.get("path") or _DEFAULT_PATH))
    return (root / rel).resolve() if not rel.is_absolute() else rel


def quota_cache_path(root: Path, cfg: dict[str, Any]) -> Path:
    rel = Path(str(cfg.get("quota_cache_path") or _DEFAULT_QUOTA_CACHE))
    return (root / rel).resolve() if not rel.is_absolute() else rel


def cooldown_path(root: Path, cfg: dict[str, Any]) -> Path:
    rel = Path(str(cfg.get("cooldown_path") or _DEFAULT_COOLDOWN))
    return (root / rel).resolve() if not rel.is_absolute() else rel


def is_secondary_rate_limit(text: str) -> bool:
    """True when stderr suggests GitHub secondary / abuse throttle."""
    return bool(_SECONDARY_LIMIT_RE.search(text or ""))


def is_rate_limit_probe_throttle(text: str) -> bool:
    """
    Throttle for REST rate_limit *probe* errors only.
    Bare Forbidden/403 alone is fail-open (scope/network); real rate-limit text fails closed.
    """
    blob = text or ""
    if _SCOPE_MISS_RE.search(blob):
        return False
    if _RATE_LIMIT_RE.search(blob) or _SECONDARY_LIMIT_RE.search(blob):
        return True
    return False


def parse_retry_after_seconds(text: str) -> int | None:
    """
    Extract Retry-After / wait-N-seconds from gh stderr or JSON snippets when present.
    Returns seconds to wait, or None when not found.
    """
    blob = text or ""
    # Explicit HTTP-style header fragments gh sometimes echoes.
    m = re.search(r"retry[_-]?after[\"'\s:=]+(\d+)", blob, re.IGNORECASE)
    if m:
        try:
            return max(0, int(m.group(1)))
        except (TypeError, ValueError):
            pass
    m2 = _RETRY_AFTER_RE.search(blob)
    if m2:
        try:
            return max(0, int(m2.group(1)))
        except (TypeError, ValueError):
            return None
    return None


def is_queueable_gh_throttle(text: str) -> bool:
    """
    True when stderr suggests transient GitHub throttle (queue to outbox).
    Excludes permanent auth/scope failures and permanent permission Forbidden.
    """
    blob = text or ""
    if _SCOPE_MISS_RE.search(blob):
        return False
    if _RATE_LIMIT_RE.search(blob):
        return True
    if _FORBIDDEN_RE.search(blob):
        # Bare Forbidden/403 may be transient; permanent permission text is not.
        if _PERM_FORBIDDEN_RE.search(blob) and not is_secondary_rate_limit(blob):
            return False
        return True
    return False


def is_rate_limit_error(text: str) -> bool:
    """Alias for is_queueable_gh_throttle (back-compat)."""
    return is_queueable_gh_throttle(text)


def read_cooldown(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_cooldown(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clear_cooldown(root: Path, ssot: dict[str, Any]) -> Path:
    """Write state=closed cooldown artifact (maintainer escape / recovered)."""
    cfg = load_outbox_config(ssot)
    path = cooldown_path(root, cfg)
    write_cooldown(
        path,
        {
            "state": "closed",
            "limited_at": None,
            "limited_until": None,
            "limited_until_epoch": None,
            "reason": None,
            "source_cmd": None,
            "reset_epoch": None,
            "cleared_at": _utc_now(),
        },
    )
    return path


def open_cooldown(
    root: Path,
    ssot: dict[str, Any],
    *,
    reason: str,
    source_cmd: str,
    reset_epoch: Any = None,
    secondary: bool = False,
    retry_after_seconds: int | None = None,
) -> dict[str, Any]:
    """
    Open circuit-breaker until max(reset_epoch, now+floor, now+Retry-After).
    Reuses EXIT_QUEUED(6) semantics for agents — do not retry until limited_until.
    """
    cfg = load_outbox_config(ssot)
    now = _utc_now_epoch()
    floor = int(
        cfg["secondary_limit_floor_seconds"]
        if secondary
        else cfg["cooldown_floor_seconds"]
    )
    until_epoch = now + max(floor, 1)
    if retry_after_seconds is not None:
        try:
            ra = int(retry_after_seconds)
        except (TypeError, ValueError):
            ra = 0
        if ra > 0:
            until_epoch = max(until_epoch, now + ra)
    try:
        reset_i = int(reset_epoch) if reset_epoch is not None else None
    except (TypeError, ValueError):
        reset_i = None
    if reset_i is None:
        cached = read_quota_cache(quota_cache_path(root, cfg))
        if cached:
            try:
                reset_i = int(cached["reset_epoch"]) if cached.get("reset_epoch") is not None else None
            except (TypeError, ValueError):
                reset_i = None
    if reset_i is not None and reset_i > until_epoch:
        until_epoch = float(reset_i)
    payload = {
        "state": "open",
        "limited_at": _utc_now(),
        "limited_until": format_reset_iso(until_epoch),
        "limited_until_epoch": until_epoch,
        "reason": reason,
        "source_cmd": source_cmd,
        "reset_epoch": reset_i,
        "retry_after_seconds": retry_after_seconds,
    }
    write_cooldown(cooldown_path(root, cfg), payload)
    return payload


def cooldown_active(
    root: Path,
    ssot: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    """
    Return (active, cooldown_dict).
    Active when state=open and now < limited_until_epoch.
    """
    cfg = load_outbox_config(ssot)
    data = read_cooldown(cooldown_path(root, cfg))
    if not data or str(data.get("state") or "") != "open":
        return False, data
    try:
        until = float(data.get("limited_until_epoch") or 0)
    except (TypeError, ValueError):
        until = 0.0
    if until <= 0:
        return False, data
    if _utc_now_epoch() < until:
        return True, data
    return False, data


def maybe_close_expired_cooldown(
    root: Path,
    ssot: dict[str, Any],
    *,
    probe: bool = True,
) -> tuple[bool, str]:
    """
    If cooldown expired, optionally probe quota and close or extend.
    Returns (may_proceed, message).
    """
    active, data = cooldown_active(root, ssot)
    if active and data is not None:
        until = data.get("limited_until") or format_reset_iso(data.get("limited_until_epoch"))
        return False, f"cooldown open until {until} reason={data.get('reason')}"
    if data is None or str(data.get("state") or "") != "open":
        return True, "cooldown closed"
    # Expired open → probe once
    if not probe:
        clear_cooldown(root, ssot)
        return True, "cooldown expired (no probe)"
    below, info = remaining_below_min(root, ssot, force_refresh=True)
    if below:
        open_cooldown(
            root,
            ssot,
            reason=f"precheck remaining={info.get('remaining')}",
            source_cmd="cooldown-probe",
            reset_epoch=info.get("reset_epoch"),
            secondary=False,
        )
        return False, "cooldown extended after probe (still low remaining)"
    clear_cooldown(root, ssot)
    return True, "cooldown cleared after probe"


def api_ready(
    root: Path,
    ssot: dict[str, Any],
    *,
    force_probe: bool = False,
) -> tuple[bool, int, str]:
    """
    Agent gate: True/EXIT_OK when board writes may proceed.
    False/EXIT_QUEUED when cooldown open or GraphQL remaining below min.
    Probe errors that look like throttle → open cooldown (fail closed).
    Other probe errors → fail open (allow live write; live path still queues).
    """
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"]:
        return True, EXIT_OK, "outbox disabled — api-ready N/A (live allowed)"
    ok, msg = maybe_close_expired_cooldown(root, ssot, probe=True)
    if not ok:
        return False, EXIT_QUEUED, f"api-ready=no · {msg} · do not retry; later: project outbox status"
    info = get_cached_graphql_remaining(root, ssot, force_refresh=force_probe)
    err = str(info.get("error") or "")
    # Probe path: bare Forbidden fail-open; only explicit rate-limit text opens cooldown.
    if err and is_rate_limit_probe_throttle(err):
        open_cooldown(
            root,
            ssot,
            reason=f"rate_limit_probe:{err[:80]}",
            source_cmd="api-ready",
            reset_epoch=info.get("reset_epoch"),
            secondary=is_secondary_rate_limit(err),
            retry_after_seconds=parse_retry_after_seconds(err),
        )
        return (
            False,
            EXIT_QUEUED,
            f"api-ready=no · rate_limit probe throttled · do not retry; later: project outbox status",
        )
    below, info = remaining_below_min(root, ssot, force_refresh=False)
    if below:
        open_cooldown(
            root,
            ssot,
            reason=f"graphql_remaining={info.get('remaining')}",
            source_cmd="api-ready",
            reset_epoch=info.get("reset_epoch"),
        )
        return (
            False,
            EXIT_QUEUED,
            f"api-ready=no · remaining={info.get('remaining')}<{cfg['min_graphql_remaining']} "
            f"reset={format_reset_iso(info.get('reset_epoch'))} · do not retry",
        )
    rem = info.get("remaining")
    rem_disp = "?" if rem is None and info.get("error") else rem
    return (
        True,
        EXIT_OK,
        f"api-ready=yes · remaining={rem_disp} "
        f"reset={format_reset_iso(info.get('reset_epoch'))}",
    )

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


def _utc_now_epoch() -> float:
    return datetime.now(timezone.utc).timestamp()


def read_quota_cache(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_quota_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refresh_graphql_quota(root: Path, ssot: dict[str, Any]) -> dict[str, Any]:
    """Fetch GraphQL remaining via REST and write TTL cache."""
    cfg = load_outbox_config(ssot)
    rl = graphql_rate_limit()
    payload = {
        "remaining": rl.get("remaining"),
        "limit": rl.get("limit"),
        "reset_epoch": rl.get("reset_epoch"),
        "error": rl.get("error"),
        "fetched_at": _utc_now_epoch(),
        "fetched_at_iso": _utc_now(),
    }
    write_quota_cache(quota_cache_path(root, cfg), payload)
    return payload


def get_cached_graphql_remaining(
    root: Path,
    ssot: dict[str, Any],
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Return quota dict with remaining/limit/reset_epoch/error/from_cache.
    Uses TTL cache; refreshes via REST when stale or force_refresh.
    """
    cfg = load_outbox_config(ssot)
    path = quota_cache_path(root, cfg)
    ttl = int(cfg["quota_cache_ttl_seconds"])
    if not force_refresh:
        cached = read_quota_cache(path)
        if cached is not None:
            try:
                fetched = float(cached.get("fetched_at") or 0)
            except (TypeError, ValueError):
                fetched = 0.0
            if fetched and (_utc_now_epoch() - fetched) <= ttl and cached.get("error") is None:
                out = dict(cached)
                out["from_cache"] = True
                return out
    fresh = refresh_graphql_quota(root, ssot)
    fresh["from_cache"] = False
    return fresh


def remaining_below_min(root: Path, ssot: dict[str, Any], *, force_refresh: bool = False) -> tuple[bool, dict[str, Any]]:
    """Return (below_min, quota_info). On read error, treat as not below (fail open to live write)."""
    cfg = load_outbox_config(ssot)
    info = get_cached_graphql_remaining(root, ssot, force_refresh=force_refresh)
    if info.get("error"):
        return False, info
    try:
        rem = int(info["remaining"]) if info.get("remaining") is not None else -1
    except (TypeError, ValueError):
        return False, info
    min_rem = int(cfg["min_graphql_remaining"])
    return rem >= 0 and rem < min_rem, info


def _payload_fingerprint(op: str, payload: dict[str, Any]) -> tuple[Any, ...]:
    keys = _DEDUPE_PAYLOAD_KEYS.get(op, tuple(sorted(payload.keys())))
    parts: list[Any] = []
    for key in keys:
        val = payload.get(key)
        if isinstance(val, str):
            parts.append(val.strip())
        else:
            parts.append(val)
    return tuple(parts)


def find_duplicate_pending(
    entries: list[dict[str, Any]],
    *,
    op: str,
    item_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    want = _payload_fingerprint(op, payload)
    for entry in entries:
        if str(entry.get("status") or "") != "pending":
            continue
        if str(entry.get("op") or "") != op:
            continue
        if str(entry.get("item_id") or "") != item_id:
            continue
        existing_payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
        if _payload_fingerprint(op, existing_payload) == want:
            return entry
    return None


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
    if op == "set-section":
        if not str(payload.get("section") or "").strip():
            errs.append("set-section payload.section required")
        if not str(payload.get("text") or "").strip():
            errs.append("set-section payload.text required")
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
    if cfg.get("dedupe_pending", True):
        dup = find_duplicate_pending(
            entries, op=op_key, item_id=item_id.strip(), payload=dict(payload or {})
        )
        if dup is not None:
            return dup, ""
    # Coalesce pending append-notes for the same item (newest wins; cap count).
    if (
        op_key == "append-notes"
        and cfg.get("coalesce_pending_notes", True)
        and isinstance(payload, dict)
    ):
        item_key = item_id.strip()
        pending_notes = [
            e
            for e in entries
            if str(e.get("status") or "") == "pending"
            and str(e.get("op") or "") == "append-notes"
            and str(e.get("item_id") or "") == item_key
        ]
        max_n = max(1, int(cfg.get("max_pending_notes_per_item") or 3))
        if pending_notes:
            # Replace oldest pending notes beyond max-1 slots so new note fits.
            drop = pending_notes[:- (max_n - 1)] if max_n > 1 else pending_notes
            if max_n == 1:
                drop = pending_notes
            drop_ids = {str(e.get("id")) for e in drop}
            if drop_ids:
                entries = [e for e in entries if str(e.get("id")) not in drop_ids]
    entries.append(entry)
    write_outbox_entries(path, entries)
    return entry, ""


def queued_message(cmd: str, entry: dict[str, Any], *, reason: str = "throttle") -> str:
    return (
        f"project {cmd}: QUEUED — CODE=6 · reason={reason} · id={entry.get('id')} "
        f"op={entry.get('op')} item={entry.get('item_id')} · "
        f"do not retry; later: python3 -m agent_colony project outbox flush"
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
    If outbox enabled and error is queueable throttle, enqueue and return EXIT_QUEUED.
    Otherwise return None (caller should fail as before).
    """
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"]:
        return None
    if not is_queueable_gh_throttle(err_detail):
        return None
    secondary = is_secondary_rate_limit(err_detail)
    open_cooldown(
        root,
        ssot,
        reason="secondary_throttle" if secondary else "stderr_throttle",
        source_cmd=cmd,
        secondary=secondary,
        retry_after_seconds=parse_retry_after_seconds(err_detail),
    )
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
            f"project {cmd}: FAIL — CODE={EXIT_GH} · throttle and enqueue failed: {err}",
            file=sys.stderr,
        )
        return EXIT_GH
    print(queued_message(cmd, entry, reason="throttle"), file=sys.stderr)
    return EXIT_QUEUED


def maybe_enqueue_on_low_quota(
    root: Path,
    ssot: dict[str, Any],
    *,
    cmd: str,
    op: str,
    item_id: str,
    agent: str,
    payload: dict[str, Any],
) -> int | None:
    """
    If precheck enabled and cached GraphQL remaining < min, enqueue and EXIT_QUEUED.
    Returns None when write may proceed (or precheck disabled / quota unreadable).
    """
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"] or not cfg.get("precheck_writes", True):
        return None
    below, info = remaining_below_min(root, ssot)
    if not below:
        return None
    open_cooldown(
        root,
        ssot,
        reason=f"graphql_remaining={info.get('remaining')}",
        source_cmd=cmd,
        reset_epoch=info.get("reset_epoch"),
    )
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
            f"project {cmd}: FAIL — CODE={EXIT_GH} · low-quota enqueue failed: {err}",
            file=sys.stderr,
        )
        return EXIT_GH
    rem = info.get("remaining")
    min_rem = cfg["min_graphql_remaining"]
    print(
        queued_message(cmd, entry, reason=f"precheck remaining={rem}<{min_rem}"),
        file=sys.stderr,
    )
    return EXIT_QUEUED


def guard_write_or_queue(
    root: Path,
    ssot: dict[str, Any],
    *,
    cmd: str,
    op: str,
    item_id: str,
    agent: str,
    payload: dict[str, Any],
) -> int | None:
    """
    Call before Pattern A GraphQL writes.
    Returns EXIT_QUEUED to skip the live write; None to proceed.
    Hard-skips while board-api-cooldown.json is open (no REST/GraphQL).
    """
    cfg = load_outbox_config(ssot)
    if cfg["enabled"]:
        ok, msg = maybe_close_expired_cooldown(root, ssot, probe=False)
        if not ok:
            # Still within limited_until — enqueue without probing API.
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
                    f"project {cmd}: FAIL — CODE={EXIT_GH} · cooldown enqueue failed: {err}",
                    file=sys.stderr,
                )
                return EXIT_GH
            print(
                queued_message(cmd, entry, reason=f"cooldown · {msg}"),
                file=sys.stderr,
            )
            return EXIT_QUEUED
    return maybe_enqueue_on_low_quota(
        root,
        ssot,
        cmd=cmd,
        op=op,
        item_id=item_id,
        agent=agent,
        payload=payload,
    )


def note_successful_write(root: Path, ssot: dict[str, Any]) -> None:
    """Refresh quota cache after a successful live write (respects TTL)."""
    cfg = load_outbox_config(ssot)
    if not cfg["enabled"]:
        return
    # Soft refresh only when cache missing/stale — avoids REST spam
    get_cached_graphql_remaining(root, ssot, force_refresh=False)


def count_outbox(path: Path) -> dict[str, int]:
    entries = read_outbox_entries(path)
    counts = {"pending": 0, "done": 0, "failed": 0, "total": len(entries)}
    for e in entries:
        st = str(e.get("status") or "")
        if st in counts:
            counts[st] += 1
    return counts


def purge_outbox_entries(
    path: Path,
    *,
    status: str,
    archive: bool = True,
    archive_path: Path | None = None,
) -> tuple[int, int, Path | None]:
    """
    Remove outbox rows with the given status from *path*.

    Only ``failed`` or ``done`` may be purged (never ``pending``).
    When *archive* is True, write removed rows to *archive_path* (or a
    timestamped sibling of *path*) before rewriting the live file.

    Returns ``(removed_count, kept_count, archive_path_or_none)``.
    """
    want = str(status or "").strip().lower()
    if want not in ("failed", "done"):
        raise ValueError("purge status must be 'failed' or 'done' (pending forbidden)")
    entries = read_outbox_entries(path)
    remove = [e for e in entries if str(e.get("status") or "") == want]
    keep = [e for e in entries if str(e.get("status") or "") != want]
    if not remove:
        return 0, len(keep), None
    dest: Path | None = None
    if archive:
        if archive_path is None:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            dest = path.with_name(f"{path.stem}-purged-{want}-{stamp}{path.suffix}")
        else:
            dest = archive_path
        write_outbox_entries(dest, remove)
    write_outbox_entries(path, keep)
    return len(remove), len(keep), dest


def apply_outbox_entry(
    root: Path,
    ssot: dict[str, Any],
    entry: dict[str, Any],
    *,
    limit: int = 100,
) -> tuple[bool, str]:
    """Apply one pending entry to the live board. Returns (ok, detail)."""
    # Late imports avoid circular import with project_cli (documented exception).
    from project_atomics import (  # noqa: PLC0415
        BODY_GATE_STATUSES,
        _item_body,
        _normalize_status,
        assert_body_ready_for_status,
        ensure_start_date_if_starting,
        ensure_end_date_if_done,
        done_status_logical,
        is_placeholder_section_content,
        normalize_set_section_name,
        replace_section_content,
    )
    from project_cli import (  # noqa: PLC0415
        append_notes_helper,
        edit_item_body,
        fetch_project_items,
        find_item_by_id,
        format_agent_attribution,
        promote_draft_item_to_issue,
        resolve_field_option_id,
        run_gh,
        set_item_assignee,
        set_item_date,
        set_item_number,
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
            skip_precheck=True,
        )
        return ok, detail

    if op == "set-section":
        try:
            section = normalize_set_section_name(str(payload.get("section") or ""))
        except ValueError as exc:
            return False, str(exc)
        text = str(payload.get("text") or "").strip()
        if not text or is_placeholder_section_content(text):
            return False, "set-section text must not be empty or (TBD)"
        items, err = fetch_project_items(ssot, limit=limit)
        if err:
            return False, err
        item = find_item_by_id(items, item_id)
        if item is None:
            return False, f"item not found: {item_id}"
        body = _item_body(item)
        try:
            new_body, changed = replace_section_content(body, section, text)
        except ValueError as exc:
            return False, str(exc)
        if changed:
            ok, detail = edit_item_body(ssot, item_id, new_body)
            if not ok:
                return False, detail
        if agent:
            n_ok, n_detail, _ = append_notes_helper(
                root,
                ssot,
                item_id,
                agent=agent,
                text=f"set-section {section}",
                limit=limit,
                skip_precheck=True,
            )
            if not n_ok:
                return False, f"section ok but Notes failed: {n_detail}"
        return True, f"{section} updated" if changed else f"{section} unchanged"

    if op == "set-status":
        to = str(payload.get("to") or "")
        if _normalize_status(to) in BODY_GATE_STATUSES:
            items, err = fetch_project_items(ssot, limit=limit)
            if err:
                return False, err
            item = find_item_by_id(items, item_id)
            if item is None:
                return False, f"item not found: {item_id}"
            allow_skip = bool(payload.get("allow_skip_verifier"))
            skip_rationale = str(payload.get("skip_verifier_rationale") or "").strip()
            if allow_skip and not skip_rationale:
                return False, (
                    "allow_skip_verifier requires skip_verifier_rationale TEXT"
                )
            ok_body, body_detail = assert_body_ready_for_status(
                ssot,
                item,
                to,
                agent=agent,
                allow_skip_verifier=allow_skip,
                skip_verifier_rationale=skip_rationale,
            )
            if not ok_body:
                return False, body_detail
        ok, detail = set_item_status(ssot, item_id, to)
        if not ok:
            return False, detail
        if _normalize_status(to) == "in_progress":
            start = str(payload.get("start_date") or "").strip()
            if start:
                d_ok, d_detail = set_item_date(ssot, item_id, "start_date", start)
                if not d_ok:
                    return False, f"status set but start_date failed: {d_detail}"
            else:
                d_ok, d_detail, _applied = ensure_start_date_if_starting(ssot, item_id)
                if not d_ok:
                    return False, f"status set but start_date failed: {d_detail}"
        if _normalize_status(to) == done_status_logical(ssot):
            end = str(payload.get("end_date") or "").strip()
            if end:
                e_ok, e_detail = set_item_date(ssot, item_id, "end_date", end)
                if not e_ok:
                    return False, f"status set but end_date failed: {e_detail}"
            else:
                e_ok, e_detail, _applied = ensure_end_date_if_done(ssot, item_id)
                if not e_ok:
                    return False, f"status set but end_date failed: {e_detail}"
        return True, detail

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

    if op == "promote-to-issue":
        repo = str(payload.get("repo") or ssot.get("default_repo") or "")
        ok, detail, meta = promote_draft_item_to_issue(ssot, item_id, repo=repo)
        if not ok:
            return False, detail
        note = str(payload.get("text") or "").strip()
        if not note:
            n = meta.get("issue_number")
            url = meta.get("url") or ""
            note = f"promoted to Issue #{n}: {url}" if url else f"promoted to Issue #{n}"
        if agent and note:
            n_ok, n_detail, _ = append_notes_helper(
                root, ssot, str(meta.get("item_id") or item_id),
                agent=agent, text=note, limit=limit,
            )
            if not n_ok:
                return False, f"promoted but Notes failed: {n_detail}"
        return True, detail

    if op == "handoff":
        next_agent = str(payload.get("next") or "").strip().lstrip("@")
        status_to = str(payload.get("to") or "").strip()
        extra = str(payload.get("note") or payload.get("text") or "").strip()
        if status_to and _normalize_status(status_to) in BODY_GATE_STATUSES:
            items, err = fetch_project_items(ssot, limit=limit)
            if err:
                return False, err
            item = find_item_by_id(items, item_id)
            if item is None:
                return False, f"item not found: {item_id}"
            allow_skip = bool(payload.get("allow_skip_verifier"))
            skip_rationale = str(payload.get("skip_verifier_rationale") or "").strip()
            if allow_skip and not skip_rationale:
                return False, (
                    "allow_skip_verifier requires skip_verifier_rationale TEXT"
                )
            ok_body, body_detail = assert_body_ready_for_status(
                ssot,
                item,
                status_to,
                agent=agent,
                allow_skip_verifier=allow_skip,
                skip_verifier_rationale=skip_rationale,
            )
            if not ok_body:
                return False, body_detail
        if status_to:
            ok, detail = set_item_status(ssot, item_id, status_to)
            if not ok:
                return False, detail
            if _normalize_status(status_to) == "in_progress":
                d_ok, d_detail, _applied = ensure_start_date_if_starting(ssot, item_id)
                if not d_ok:
                    return False, f"status set but start_date failed: {d_detail}"
            if _normalize_status(status_to) == done_status_logical(ssot):
                e_ok, e_detail, _applied = ensure_end_date_if_done(ssot, item_id)
                if not e_ok:
                    return False, f"status set but end_date failed: {e_detail}"
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
    ok_cd, cd_msg = maybe_close_expired_cooldown(root, ssot, probe=True)
    if not ok_cd:
        return EXIT_QUEUED, f"refuse flush · {cd_msg}"
    path = outbox_path(root, cfg)
    # Prefer TTL cache; force refresh at flush start for accurate gate
    rl = get_cached_graphql_remaining(root, ssot, force_refresh=True)
    remaining = rl.get("remaining")
    min_rem = int(cfg["min_graphql_remaining"])
    if rl.get("error"):
        err = str(rl["error"])
        if is_rate_limit_probe_throttle(err):
            open_cooldown(
                root,
                ssot,
                reason=f"rate_limit_probe:{err[:80]}",
                source_cmd="outbox flush",
                secondary=is_secondary_rate_limit(err),
                retry_after_seconds=parse_retry_after_seconds(err),
            )
            return EXIT_QUEUED, f"refuse flush · rate_limit probe throttled: {err}"
        return EXIT_GH, f"cannot read rate_limit: {err}"
    try:
        rem_i = int(remaining) if remaining is not None else -1
    except (TypeError, ValueError):
        rem_i = -1
    if rem_i < min_rem:
        reset = format_reset_iso(rl.get("reset_epoch"))
        open_cooldown(
            root,
            ssot,
            reason=f"graphql_remaining={rem_i}",
            source_cmd="outbox flush",
            reset_epoch=rl.get("reset_epoch"),
        )
        return (
            EXIT_QUEUED,
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
        # Mid-batch: re-read REST quota (flush is rare + capped; prefer accuracy)
        rl2 = get_cached_graphql_remaining(root, ssot, force_refresh=True)
        try:
            rem2 = int(rl2.get("remaining")) if rl2.get("remaining") is not None else rem_i
        except (TypeError, ValueError):
            rem2 = rem_i
        if rem2 < min_rem:
            stopped_early = True
            open_cooldown(
                root,
                ssot,
                reason=f"graphql_remaining={rem2}",
                source_cmd="outbox flush",
                reset_epoch=rl2.get("reset_epoch"),
            )
            break

        entry = entries[idx]
        entry["attempts"] = int(entry.get("attempts") or 0) + 1
        ok, detail = apply_outbox_entry(root, ssot, entry, limit=limit)
        if ok:
            entry["status"] = "done"
            entry["last_error"] = None
            done_n += 1
            # Drop local remaining by 1 without REST when cache present
            cached = read_quota_cache(quota_cache_path(root, cfg))
            if cached and cached.get("remaining") is not None:
                try:
                    cached["remaining"] = max(0, int(cached["remaining"]) - 1)
                    write_quota_cache(quota_cache_path(root, cfg), cached)
                except (TypeError, ValueError):
                    pass
        else:
            entry["last_error"] = detail
            if is_queueable_gh_throttle(detail):
                entry["status"] = "pending"
                stopped_early = True
                open_cooldown(
                    root,
                    ssot,
                    reason="secondary_throttle"
                    if is_secondary_rate_limit(detail)
                    else "stderr_throttle",
                    source_cmd="outbox flush",
                    secondary=is_secondary_rate_limit(detail),
                    retry_after_seconds=parse_retry_after_seconds(detail),
                )
                write_outbox_entries(path, entries)
                return (
                    EXIT_QUEUED,
                    f"flush stopped on rate-limit/throttle after done={done_n}; detail={detail}",
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
    if done_n > 0 and left == 0 and not stopped_early:
        clear_cooldown(root, ssot)
    summary = (
        f"flushed done={done_n} failed={fail_n} pending_left={left}"
        + (" (stopped early: low quota)" if stopped_early else "")
    )
    return EXIT_OK, summary
