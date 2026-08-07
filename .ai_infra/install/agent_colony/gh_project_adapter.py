"""
File: gh_project_adapter.py
Path: .ai_infra/install/agent_colony/gh_project_adapter.py
Role: gh CLI and GraphQL/REST adapters for GitHub Project board operations.
Used By:
 - .ai_infra/install/agent_colony/project_recipes.py
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/project_outbox.py (via project_cli re-exports)
Depends On:
 - .ai_infra/install/agent_colony/project_atomics.py
Notes:
 - One gh invocation per adapter function; DraftIssue body edits use DI_ id + --title.
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

from project_atomics import (
    resolve_plain_field_id,
    resolve_status_option_id,
    status_field_id,
)

_REPO_ID_CACHE: dict[str, str] = {}


def _cli():
    """Late-bound project_cli facade for test monkeypatch compatibility."""
    import project_cli as pc

    return pc


def set_item_assignee(
    ssot: dict[str, Any], item_id: str, login: str
) -> tuple[bool, str]:
    """
    Assign a GitHub human user to an Issue-backed project item.
    DraftIssue: not supported — return False with hint to use Notes or promote.
    """
    kind, cid, meta, err = _cli().resolve_item_content(ssot, item_id)
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
        proc = _cli().run_gh(gh_args)
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
    proc = _cli().run_gh(
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
    proc = _cli().run_gh(
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
def run_gh(
    args: list[str],
    *,
    timeout_s: float = 60.0,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = ["gh", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
        input=input_text,
    )
def _parse_pvti_from_gh_json(raw: str) -> str | None:
    try:
        data = json.loads(raw or "{}")
        if isinstance(data, dict):
            item_id = str(data.get("id") or data.get("itemId") or "") or None
            if item_id and item_id.startswith("PVTI_"):
                return item_id
    except json.JSONDecodeError:
        pass
    m = re.search(r"(PVTI_[A-Za-z0-9_-]+)", raw or "")
    return m.group(1) if m else None
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
    proc = _cli().run_gh(gh_args)
    if proc.returncode != 0:
        return None, None, (proc.stderr or proc.stdout or "gh project item-create failed").strip()
    raw = (proc.stdout or "").strip()
    return _parse_pvti_from_gh_json(raw), raw, None
def create_issue_item(ssot: dict[str, Any], title: str, body: str) -> tuple[str | None, str | None, str | None]:
    """
    Create a GitHub Issue then add it to the Project.
    Returns (item_id PVTI_, raw_stdout, error).
    """
    repo = str(ssot.get("default_repo") or "").strip()
    if not repo or "/" not in repo:
        return None, None, "project_ssot.default_repo required for item_kind_default=issue"
    create_args = ["issue", "create", "--repo", repo, "--title", title]
    if body:
        create_args.extend(["--body", body])
    proc = _cli().run_gh(create_args)
    if proc.returncode != 0:
        return None, None, (proc.stderr or proc.stdout or "gh issue create failed").strip()
    out = (proc.stdout or "").strip()
    url_m = re.search(r"(https://github\.com/[^\s]+/issues/\d+)", out)
    if not url_m:
        return None, out, f"gh issue create succeeded but no issue URL in output: {out!r}"
    issue_url = url_m.group(1)
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    add_args = [
        "project",
        "item-add",
        str(number),
        "--owner",
        owner,
        "--url",
        issue_url,
        "--format",
        "json",
    ]
    add_proc = _cli().run_gh(add_args)
    if add_proc.returncode != 0:
        return (
            None,
            None,
            (
                f"issue created ({issue_url}) but item-add failed: "
                + (add_proc.stderr or add_proc.stdout or "gh project item-add failed").strip()
            ),
        )
    raw = (add_proc.stdout or "").strip()
    item_id = _parse_pvti_from_gh_json(raw)
    if not item_id:
        return None, raw, f"item-add ok but no PVTI_ in output (issue={issue_url})"
    return item_id, raw or issue_url, None
def create_board_item(ssot: dict[str, Any], title: str, body: str) -> tuple[str | None, str | None, str | None]:
    """Route create by conventions.item_kind_default: issue (product default) | draft."""
    conventions = ssot.get("conventions") if isinstance(ssot.get("conventions"), dict) else {}
    kind = str((conventions or {}).get("item_kind_default") or "issue").strip().lower()
    if kind == "draft":
        return _cli().create_draft_item(ssot, title, body)
    return _cli().create_issue_item(ssot, title, body)
def resolve_repository_id(ssot: dict[str, Any], repo: str = "") -> tuple[str | None, str | None]:
    """
    Resolve GitHub repository node id (R_…) for promote / issue create.
    Returns (repository_id, error).
    """
    repo_s = (repo or str(ssot.get("default_repo") or "")).strip()
    if not repo_s or "/" not in repo_s:
        return None, "repository required as owner/repo (set project_ssot.default_repo or --repo)"
    if repo_s in _REPO_ID_CACHE:
        return _REPO_ID_CACHE[repo_s], None
    owner, _, name = repo_s.partition("/")
    owner, name = owner.strip(), name.strip()
    if not owner or not name:
        return None, f"invalid repository {repo_s!r}"
    query = (
        "query($owner:String!,$name:String!){repository(owner:$owner,name:$name){id}}"
    )
    proc = _cli().run_gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"owner={owner}",
            "-f",
            f"name={name}",
        ]
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "graphql repository id failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, f"invalid graphql JSON: {exc}"
    errors = data.get("errors")
    if errors:
        msg = errors[0].get("message") if isinstance(errors[0], dict) else errors
        return None, str(msg)
    node = ((data.get("data") or {}).get("repository")) or {}
    rid = str(node.get("id") or "") if isinstance(node, dict) else ""
    if not rid:
        return None, f"repository not found: {repo_s}"
    _REPO_ID_CACHE[repo_s] = rid
    return rid, None
def promote_draft_item_to_issue(
    ssot: dict[str, Any],
    item_id: str,
    *,
    repo: str = "",
) -> tuple[bool, str, dict[str, Any]]:
    """
    Convert Project DraftIssue → Issue via convertProjectV2DraftIssueItemToIssue.
    Same PVTI_ is preserved. Returns (ok, detail, meta) with issue_number/url/repo when ok.
    Already-Issue is a successful no-op.
    """
    kind, cid, meta, err = _cli().resolve_item_content(ssot, item_id)
    if err:
        return False, err, {}
    if kind == "issue":
        repo_s = str((meta or {}).get("repo") or ssot.get("default_repo") or "")
        return (
            True,
            f"already Issue #{cid}",
            {
                "item_id": item_id,
                "issue_number": cid,
                "repo": repo_s,
                "url": f"https://github.com/{repo_s}/issues/{cid}" if repo_s and cid else "",
                "noop": True,
            },
        )
    if kind != "draft":
        return False, f"cannot promote content kind {kind!r}", {}

    repo_s = (repo or str(ssot.get("default_repo") or "")).strip()
    repo_id, rerr = resolve_repository_id(ssot, repo_s)
    if not repo_id:
        return False, rerr or "repositoryId missing", {}

    mutation = (
        "mutation($input: ConvertProjectV2DraftIssueItemToIssueInput!) {"
        " convertProjectV2DraftIssueItemToIssue(input: $input) {"
        "  item { id content { __typename"
        "   ... on Issue { number url repository { nameWithOwner } }"
        "  } } } }"
    )
    proc = _cli().run_gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={mutation}",
            "-F",
            f"input[itemId]={item_id}",
            "-F",
            f"input[repositoryId]={repo_id}",
        ]
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "convertProjectV2DraftIssueItemToIssue failed").strip()
        if "fine-grained" in detail.lower() or "Resource not accessible" in detail:
            detail += (
                " · hint: convertProjectV2DraftIssueItemToIssue often needs classic PAT "
                "(project+repo), not fine-grained"
            )
        return False, detail, {}
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return False, f"invalid promote JSON: {exc}", {}
    errors = data.get("errors")
    if errors:
        msg = errors[0].get("message") if isinstance(errors[0], dict) else errors
        return False, str(msg), {}
    item = (
        ((data.get("data") or {}).get("convertProjectV2DraftIssueItemToIssue") or {}).get("item")
    )
    if not isinstance(item, dict):
        return False, "promote mutation returned no item", {}
    out_id = str(item.get("id") or item_id)
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    number = content.get("number")
    url = str(content.get("url") or "")
    rmeta = content.get("repository") if isinstance(content.get("repository"), dict) else {}
    repo_out = str(rmeta.get("nameWithOwner") or repo_s)
    if number is None:
        kind2, cid2, meta2, err2 = _cli().resolve_item_content(ssot, out_id)
        if err2 or kind2 != "issue":
            return False, err2 or "promote succeeded but content is not Issue", {}
        number = cid2
        repo_out = str((meta2 or {}).get("repo") or repo_out)
        url = f"https://github.com/{repo_out}/issues/{number}" if repo_out else url
    return (
        True,
        f"Issue #{number}",
        {
            "item_id": out_id,
            "issue_number": str(number),
            "repo": repo_out,
            "url": url or f"https://github.com/{repo_out}/issues/{number}",
            "noop": False,
        },
    )
def fetch_project_items(ssot: dict[str, Any], *, limit: int = 100) -> tuple[list[dict[str, Any]], str | None]:
    """Return (items, error). Each item keeps gh JSON fields plus normalized helpers."""
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    proc = _cli().run_gh(
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

def fetch_project_item_by_id(
    ssot: dict[str, Any], item_id: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Fetch a single ProjectV2Item by its PVTI_… id.

    Normalizes a small subset of fields to match the `gh project item-list` item
    shape expected by downstream validators (status, priority, size, estimate,
    start date, and content.body).
    """
    iid = (item_id or "").strip()
    if not iid:
        return None, "empty item id"

    query = (
        "query($id:ID!){node(id:$id){...on ProjectV2Item{id content{"
        "__typename "
        "...on DraftIssue{id title body} "
        "...on Issue{id number title body repository{nameWithOwner}}"
        "}"
        "fieldValues(first:50){nodes{__typename "
        "...on ProjectV2ItemFieldSingleSelectValue{name field{name}} "
        "...on ProjectV2ItemFieldTextValue{text field{name}} "
        "...on ProjectV2ItemFieldDateValue{date field{name}} "
        "}}}}}"
    )
    proc = _cli().run_gh(
        ["api", "graphql", "-f", f"query={query}", "-f", f"id={iid}"]
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "gh graphql node query failed").strip()
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return None, f"invalid graphql JSON: {exc}"

    errors = data.get("errors")
    if errors:
        msg = errors[0].get("message") if isinstance(errors[0], dict) else errors
        return None, str(msg)

    node = (data.get("data") or {}).get("node")
    if not isinstance(node, dict):
        return None, f"project item not found: {iid}"

    content = node.get("content")
    body = ""
    if isinstance(content, dict):
        maybe_body = content.get("body")
        if isinstance(maybe_body, str):
            body = maybe_body

    out: dict[str, Any] = {
        "id": str(node.get("id") or iid),
        "content": {"body": body},
    }

    field_values = node.get("fieldValues") or {}
    if isinstance(field_values, dict):
        nodes = field_values.get("nodes") or []
        if isinstance(nodes, list):
            for v in nodes:
                if not isinstance(v, dict):
                    continue
                field = v.get("field")
                field_name = ""
                if isinstance(field, dict):
                    field_name = str(field.get("name") or "").strip()
                if not field_name:
                    continue
                normalized = field_name.strip().lower().replace(" ", "_").replace("-", "_")

                if normalized in ("status",):
                    val = v.get("name")
                    if isinstance(val, str):
                        out["status"] = val
                elif normalized in ("priority",):
                    val = v.get("name")
                    if isinstance(val, str):
                        out["priority"] = val
                elif normalized in ("size",):
                    val = v.get("name")
                    if isinstance(val, str):
                        out["size"] = val
                elif normalized in ("estimate",):
                    val = v.get("text") if "text" in v else v.get("name")
                    if val is not None:
                        out["estimate"] = str(val).strip()
                elif normalized in ("start_date", "startdate", "start_date_utc", "startdateutc", "start_date_time", "start_date_time_utc", "start_date_datetime"):
                    val = v.get("date")
                    if val is not None:
                        out["start date"] = str(val).strip()

    return out, None
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
        proc = _cli().run_gh(["api", "graphql", "-f", f"query={query}", "-f", f"id={iid}"])
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
    proc = _cli().run_gh(["api", "graphql", "-f", f"query={query}", "-f", f"id={iid}"])
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
def resolve_draft_content(
    ssot: dict[str, Any], item_id: str
) -> tuple[str | None, str | None, str | None]:
    """Return (content_id, title, error) for DraftIssue; error if not a draft."""
    kind, cid, meta, err = _cli().resolve_item_content(ssot, item_id)
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
    kind, cid, meta, err = _cli().resolve_item_content(ssot, item_id)
    if err or not kind or not cid:
        return False, err or "could not resolve content id for body edit"
    meta = meta or {}
    project_id = str(ssot["project_id"])

    if kind == "draft":
        title = str(meta.get("title") or "").strip() or "(untitled)"
        proc = _cli().run_gh(
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
        proc = _cli().run_gh(gh_args)
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
    proc = _cli().run_gh(
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
