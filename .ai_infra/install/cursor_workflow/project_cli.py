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
 - Pattern A: one gh invocation per action; no dual-write of local trackers.
 - DraftIssue body edits resolve PVTI_… → DI_… (+ --title); Status stays on PVTI_….
 - Notes attribution: @owner.github_user/agent via append-notes --agent.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


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


def format_note_line(root: Path, agent: str, text: str) -> str:
    """
    Prefix note with @user/agent · text.
    Idempotent if text already starts with that attribution.
    """
    attr = format_agent_attribution(root, agent)
    body = (text or "").strip()
    if body.startswith(attr):
        return body
    # Also accept without requiring exact agent if already @user/something
    if re.match(r"^@[^\s/]+/[^\s·]+", body):
        return body
    if not body:
        return attr
    return f"{attr} · {body}"


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


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project status: FAIL — {e}", file=sys.stderr)
        return 1
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
    return 0 if enabled else 2


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project list: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project list: FAIL — {e}", file=sys.stderr)
        return 2
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
        print(proc.stderr or proc.stdout or "gh project item-list failed", file=sys.stderr)
        return proc.returncode or 1
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        print(f"project list: FAIL — invalid JSON from gh: {exc}", file=sys.stderr)
        return 1
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
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project create: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project create: FAIL — {e}", file=sys.stderr)
        return 2
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    body = args.body or ""
    sections = (ssot.get("conventions") or {}).get("body_sections") or []
    if not body and sections:
        body = "\n\n".join(f"## {s}\n\n(TBD)" for s in sections)
    gh_args = [
        "project",
        "item-create",
        str(number),
        "--owner",
        owner,
        "--title",
        args.title,
        "--format",
        "json",
    ]
    if body:
        gh_args.extend(["--body", body])
    proc = run_gh(gh_args)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-create failed", file=sys.stderr)
        return proc.returncode or 1
    print(proc.stdout.strip())
    return 0


def cmd_set_status(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project set-status: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project set-status: FAIL — {e}", file=sys.stderr)
        return 2
    try:
        option_id = resolve_status_option_id(ssot, args.to)
        field_id = status_field_id(ssot)
    except KeyError as exc:
        print(f"project set-status: FAIL — {exc}", file=sys.stderr)
        return 1
    project_id = str(ssot["project_id"])
    proc = run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            args.id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-edit failed", file=sys.stderr)
        return proc.returncode or 1
    print(f"set-status: {args.id} → {args.to} ({option_id})")
    return 0


def cmd_set_field(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project set-field: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project set-field: FAIL — {e}", file=sys.stderr)
        return 2
    field = args.field.strip().lower()
    if field not in ("priority", "size"):
        print("project set-field: FAIL — --field must be priority or size", file=sys.stderr)
        return 1
    try:
        field_id, option_id = resolve_field_option_id(ssot, field, args.to)
    except KeyError as exc:
        print(f"project set-field: FAIL — {exc}", file=sys.stderr)
        return 1
    project_id = str(ssot["project_id"])
    proc = run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            args.id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-edit failed", file=sys.stderr)
        return proc.returncode or 1
    print(f"set-field: {args.id} {field} → {args.to} ({option_id})")
    return 0


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
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project get: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project get: FAIL — {e}", file=sys.stderr)
        return 2
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        print(f"project get: FAIL — {err}", file=sys.stderr)
        return 1
    item = find_item_by_id(items, args.id)
    if item is None:
        print(f"project get: FAIL — item not found: {args.id}", file=sys.stderr)
        return 1
    payload = {
        "id": item.get("id"),
        "title": _item_title(item),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "size": item.get("size"),
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
        print("--- body ---")
        print(payload["body"] or "(empty)")
    return 0


def cmd_append_notes(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project append-notes: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project append-notes: FAIL — {e}", file=sys.stderr)
        return 2
    agent = getattr(args, "agent", None) or ""
    if attribution_required(ssot) and not str(agent).strip():
        print(
            "project append-notes: FAIL — --agent required "
            "(project_ssot.conventions.require_attribution_on_exit)",
            file=sys.stderr,
        )
        return 2
    note_text = args.text
    if str(agent).strip():
        try:
            note_text = format_note_line(root, str(agent), args.text)
        except ValueError as exc:
            print(f"project append-notes: FAIL — {exc}", file=sys.stderr)
            return 2
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        print(f"project append-notes: FAIL — {err}", file=sys.stderr)
        return 1
    item = find_item_by_id(items, args.id)
    if item is None:
        print(f"project append-notes: FAIL — item not found: {args.id}", file=sys.stderr)
        return 1
    body = _item_body(item)
    new_body, changed = append_notes_to_body(body, note_text)
    if not changed:
        print(f"append-notes: {args.id} — already present (idempotent skip)")
        return 0
    ok, detail = edit_item_body(ssot, args.id, new_body)
    if not ok:
        print(f"project append-notes: FAIL — {detail}", file=sys.stderr)
        return 1
    print(f"append-notes: {args.id} — updated")
    return 0


def cmd_set_assignee(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project set-assignee: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project set-assignee: FAIL — {e}", file=sys.stderr)
        return 2
    login = (getattr(args, "login", None) or "").strip()
    if not login:
        try:
            login = resolve_human_github_user(root).lstrip("@")
        except Exception as exc:  # noqa: BLE001
            print(f"project set-assignee: FAIL — {exc}", file=sys.stderr)
            return 2
    if not login:
        print(
            "project set-assignee: FAIL — no login "
            "(pass --login or set owner.github_user)",
            file=sys.stderr,
        )
        return 2
    ok, detail = set_item_assignee(ssot, args.id, login)
    if not ok:
        print(f"project set-assignee: FAIL — {detail}", file=sys.stderr)
        return 1
    print(f"set-assignee: {args.id} → @{detail.lstrip('@')}")
    return 0


def cmd_find_by_pr(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project find-by-pr: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project find-by-pr: FAIL — {e}", file=sys.stderr)
        return 2
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
            print(f"project find-by-pr: FAIL — {err}", file=sys.stderr)
            if candidates:
                print("candidates:", ", ".join(candidates), file=sys.stderr)
            return 1
    return 0 if item_id else 1


def cmd_export(args: argparse.Namespace) -> int:
    """Read-only snapshot — never mutates the board."""
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project export: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project export: FAIL — {e}", file=sys.stderr)
        return 2
    items, err = fetch_project_items(ssot, limit=args.limit)
    if err:
        print(f"project export: FAIL — {err}", file=sys.stderr)
        return 1
    snapshot = build_export_snapshot(ssot, items)
    text = json.dumps(snapshot, indent=2) + "\n"
    if args.stdout:
        print(text, end="")
        return 0
    out_path = Path(args.output) if args.output else (
        root / ".local" / "generated-data" / "project-board-snapshot.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path} ({snapshot['totalCount']} items)")
    if args.json:
        print(text, end="")
    return 0


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

    create_cmd = project_sub.add_parser("create", help="Create a DraftIssue on the project")
    create_cmd.add_argument("--directory", type=Path, default=".")
    create_cmd.add_argument("--title", required=True)
    create_cmd.add_argument("--body", default="")
    create_cmd.set_defaults(func=cmd_create)

    set_status = project_sub.add_parser("set-status", help="Set item Status from YAML option ids")
    set_status.add_argument("--directory", type=Path, default=".")
    set_status.add_argument("--id", required=True, help="Project item id (PVTI_…)")
    set_status.add_argument(
        "--to",
        required=True,
        help="Logical status: backlog|ready|in_progress|in_review|done",
    )
    set_status.set_defaults(func=cmd_set_status)

    set_field = project_sub.add_parser("set-field", help="Set Priority or Size from YAML option ids")
    set_field.add_argument("--directory", type=Path, default=".")
    set_field.add_argument("--id", required=True)
    set_field.add_argument("--field", required=True, choices=("priority", "size"))
    set_field.add_argument("--to", required=True, help="e.g. p1 or s")
    set_field.set_defaults(func=cmd_set_field)

    get_cmd = project_sub.add_parser("get", help="Get one project item by id")
    get_cmd.add_argument("--directory", type=Path, default=".")
    get_cmd.add_argument("--id", required=True, help="Project item id (PVTI_…)")
    get_cmd.add_argument("--limit", type=int, default=100)
    get_cmd.add_argument("--json", action="store_true")
    get_cmd.set_defaults(func=cmd_get)

    notes_cmd = project_sub.add_parser(
        "append-notes",
        help="Append a line under ## Notes (prefix @user/agent when --agent set)",
    )
    notes_cmd.add_argument("--directory", type=Path, default=".")
    notes_cmd.add_argument("--id", required=True)
    notes_cmd.add_argument("--text", required=True)
    notes_cmd.add_argument(
        "--agent",
        default="",
        help="Agent id for attribution (required when require_attribution_on_exit)",
    )
    notes_cmd.add_argument("--limit", type=int, default=100)
    notes_cmd.set_defaults(func=cmd_append_notes)

    assignee_cmd = project_sub.add_parser(
        "set-assignee",
        help="Assign GitHub human user (Issue-backed); default owner.github_user",
    )
    assignee_cmd.add_argument("--directory", type=Path, default=".")
    assignee_cmd.add_argument("--id", required=True, help="Project item id (PVTI_…)")
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
