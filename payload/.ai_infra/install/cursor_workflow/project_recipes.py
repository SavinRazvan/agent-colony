"""
File: project_recipes.py
Path: .ai_infra/install/cursor_workflow/project_recipes.py
Role: Pattern A recipe orchestration — claim/handoff helpers, PR resolution, rate-limit queue delegate.
Used By:
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/install/cursor_workflow/project_outbox.py (via project_cli re-exports)
Depends On:
 - .ai_infra/install/cursor_workflow/project_atomics.py
 - .ai_infra/install/cursor_workflow/gh_project_adapter.py
Notes:
 - append_notes_helper and in_progress_conflicts_for_user used by cmd_claim/cmd_handoff.
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
    edit_item_body,
    fetch_project_items,
    find_item_by_id,
    run_gh,
)
from project_atomics import (
    EXIT_GH,
    EXIT_NOT_FOUND,
    EXIT_OK,
    EXIT_USAGE,
    _item_body,
    _item_title,
    _normalize_status,
    append_notes_to_body,
    attribution_required,
    format_note_line,
    normalize_github_handle,
    parse_board_item_from_text,
)



def _cli():
    """Late-bound project_cli facade for test monkeypatch compatibility."""
    import project_cli as pc

    return pc

def in_progress_conflicts_for_user(
    items: list[dict[str, Any]],
    *,
    user_handle: str,
    exclude_id: str,
) -> list[dict[str, Any]]:
    """Other In progress items attributed to the same human (@user/ in body/title or assignees)."""
    user = _cli().normalize_github_handle(user_handle)
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
    if _cli().attribution_required(ssot) and not str(agent).strip():
        return False, "--agent required (require_attribution_on_exit)", EXIT_USAGE
    note_text = text
    if str(agent).strip():
        try:
            note_text = _cli().format_note_line(root, str(agent), text)
        except ValueError as exc:
            return False, str(exc), EXIT_USAGE
    items, err = _cli().fetch_project_items(ssot, limit=limit)
    if err:
        return False, err, EXIT_GH
    item = _cli().find_item_by_id(items, item_id)
    if item is None:
        return False, f"item not found: {item_id}", EXIT_NOT_FOUND
    body = _item_body(item)
    new_body, changed = _cli().append_notes_to_body(body, note_text)
    if not changed:
        return True, "idempotent", EXIT_OK
    ok, detail = _cli().edit_item_body(ssot, item_id, new_body)
    if not ok:
        return False, detail, EXIT_GH
    return True, "updated", EXIT_OK
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
    proc = _cli().run_gh(view_args)
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
    board_item = _cli().parse_board_item_from_text(pr_body)
    if board_item:
        return board_item, [board_item], None

    items, err = _cli().fetch_project_items(ssot, limit=limit)
    if err:
        return None, [], err
    matches = find_items_mentioning_pr(items, pr_number=pr_number, pr_url=pr_url)
    ids = [str(m.get("id")) for m in matches if m.get("id")]
    if len(ids) == 1:
        return ids[0], ids, None
    if len(ids) > 1:
        return None, ids, "ambiguous: multiple project items mention this PR"
    return None, [], "no project item found for this PR (add Board-Item: PVTI_… to PR body)"
