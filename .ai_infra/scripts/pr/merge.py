"""
File: merge.py
Path: .ai_infra/scripts/pr/merge.py
Role: Verifies merge prerequisites and writes merge summary artifact; optional board SSOT close.
Used By:
 - .agents/skills/merge-pr/SKILL.md
Depends On:
 - argparse
 - pathlib
 - scripts/pr/local_workflow_paths.py
 - .ai_infra/install/cursor_workflow/project_cli.py (board sync when project_ssot enabled)
Notes:
 - This script does not perform git merge; it verifies readiness and logs evidence.
 - Call AFTER gh pr merge with --merge-sha <oid> so the artifact records the correct merge commit.
 - --branch is optional; if omitted the script reads the current git branch.
 - Checks for alignment artifact presence when --arch-impacting flag is set.
 - When project_ssot is operational, sets card Status → done and appends Notes (non-blocking on failure).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_PR_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PR_DIR.parents[2]
_INSTALL_CW = _REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PR_DIR) not in sys.path:
    sys.path.insert(0, str(_PR_DIR))
if _INSTALL_CW.is_dir() and str(_INSTALL_CW) not in sys.path:
    sys.path.insert(0, str(_INSTALL_CW))

from local_workflow_paths import (
    ALIGNMENT_AUDIT_MD,
    ALIGNMENT_TODOS_MD,
    MERGE_MD,
    PREP_MD,
    REVIEW_MD,
    ensure_workflow_artifacts_dir,
)
from user_settings import add_pr_attribution_arguments, resolve_pr_attribution


def _head_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip() or "unknown"


def _current_branch() -> str:
    proc = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    return proc.stdout.strip() or "unknown"


def _artifact_matches_pr(file_path: Path, pr_ref: str) -> tuple[bool, str]:
    if not file_path.exists():
        return False, f"missing {file_path}"
    first_line = ""
    try:
        content = file_path.read_text(encoding="utf-8")
        first_line = (content.splitlines()[0] if content else "").strip()
    except OSError as exc:
        return False, f"unable to read {file_path}: {exc}"

    if f"({pr_ref})" not in first_line:
        return False, (
            f"stale or mismatched artifact in {file_path}: "
            f"expected header containing ({pr_ref}), got: {first_line or '<empty>'}"
        )
    return True, "ok"


def _pr_url(root: Path, pr: str, default_repo: str = "") -> str:
    """Best-effort PR URL for Notes."""
    pr_number = pr.rstrip("/").split("/")[-1] if "/" in pr else pr.lstrip("#")
    if pr.startswith("http"):
        return pr
    repo = default_repo
    if not repo:
        proc = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True,
            text=True,
            cwd=root,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            repo = proc.stdout.strip()
    if repo:
        return f"https://github.com/{repo}/pull/{pr_number}"
    return f"PR #{pr_number}"


def sync_board_after_merge(
    *,
    root: Path,
    pr: str,
    merge_sha: str,
    item_id: str | None = None,
    skip: bool = False,
) -> str:
    """
    Set project card to done and append merge Notes when project_ssot is operational.
    Returns a short status line for merge.md. Never raises for board failures.
    """
    if skip:
        return "board sync: skipped (--skip-board-sync)"
    try:
        import project_cli
    except ImportError:
        return "board sync: skipped (project_cli unavailable)"

    ssot, errs = project_cli.load_project_ssot(root)
    if errs or ssot is None:
        return "board sync: skipped (no project_ssot config)"
    enabled_errs = project_cli.require_enabled(ssot)
    if enabled_errs:
        return "board sync: skipped (project_ssot not operational)"

    resolved = item_id
    candidates: list[str] = []
    if not resolved:
        resolved, candidates, find_err = project_cli.resolve_item_id_for_pr(
            ssot, pr=pr, repo=str(ssot.get("default_repo") or "") or None
        )
        if not resolved:
            detail = find_err or "no item"
            if candidates:
                detail += f"; candidates={','.join(candidates)}"
            print(f"[WARN] board sync: {detail}", file=sys.stderr)
            return f"board sync: warn — {detail}"

    conventions = ssot.get("conventions") or {}
    done_logical = str(conventions.get("done_status") or "done")
    ok, detail = project_cli.set_item_status(ssot, resolved, done_logical)
    if not ok:
        print(f"[WARN] board sync set-status failed: {detail}", file=sys.stderr)
        return f"board sync: warn — set-status failed ({detail})"

    pr_url = _pr_url(root, pr, str(ssot.get("default_repo") or ""))
    note = f"Merged: {pr_url} @ {merge_sha}"
    try:
        note = project_cli.format_note_line(root, "merge.py", note)
    except Exception:  # noqa: BLE001 — never block merge on attribution
        pass
    items, list_err = project_cli.fetch_project_items(ssot, limit=100)
    if list_err:
        print(f"[WARN] board sync append-notes list failed: {list_err}", file=sys.stderr)
        return f"board sync: status→{done_logical} on {resolved}; notes warn ({list_err})"
    item = project_cli.find_item_by_id(items, resolved)
    body = project_cli._item_body(item) if item else ""
    new_body, changed = project_cli.append_notes_to_body(body, note)
    if changed:
        nok, ndetail = project_cli.edit_item_body(ssot, resolved, new_body)
        if not nok:
            print(f"[WARN] board sync append-notes failed: {ndetail}", file=sys.stderr)
            return f"board sync: status→{done_logical} on {resolved}; notes warn ({ndetail})"
    print(f"[PASS] board sync: {resolved} → {done_logical}; Notes updated")
    return f"board sync: {resolved} → {done_logical}; Notes: {note}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify merge readiness and emit merge artifact.")
    parser.add_argument("--pr", required=True, help="PR number or URL")
    add_pr_attribution_arguments(parser)
    parser.add_argument(
        "--merge-sha",
        default=None,
        help=(
            "Merge commit SHA from gh pr merge / gh pr view. "
            "Pass this after merge is complete so the artifact records the correct oid."
        ),
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Feature branch name (defaults to current git branch if omitted).",
    )
    parser.add_argument(
        "--arch-impacting",
        action="store_true",
        default=False,
        help="Set for architecture-impacting PRs; enforces alignment artifact presence check.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        default=False,
        help=(
            "Run prerequisite checks only and do not write workflow merge.md. "
            "Use this for pre-merge validation."
        ),
    )
    parser.add_argument(
        "--item-id",
        default=None,
        help="Project item id (PVTI_…) to close after merge; else find-by-pr / Board-Item.",
    )
    parser.add_argument(
        "--skip-board-sync",
        action="store_true",
        default=False,
        help="Do not update GitHub Project Status/Notes after merge.",
    )
    args = parser.parse_args()

    try:
        actor, agents, github_user = resolve_pr_attribution(
            root=Path.cwd(),
            actor=args.actor,
            agents=args.agents,
            pipeline=args.pipeline,
            arch_impacting=args.arch_impacting,
            agents_from_session=args.agents_from_session,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ensure_workflow_artifacts_dir()
    review_file = REVIEW_MD
    prep_file = PREP_MD
    alignment_audit_file = ALIGNMENT_AUDIT_MD
    alignment_todos_file = ALIGNMENT_TODOS_MD
    merge_file = MERGE_MD

    errors: list[str] = []
    review_ok, review_detail = _artifact_matches_pr(review_file, args.pr)
    if not review_ok:
        errors.append(review_detail)

    prep_ok, prep_detail = _artifact_matches_pr(prep_file, args.pr)
    if not prep_ok:
        errors.append(prep_detail)

    if args.arch_impacting:
        if not alignment_audit_file.exists():
            errors.append(
                "missing .local/workflow-artifacts/alignment/alignment-audit.md "
                "(required for architecture-impacting PRs)"
            )
        if not alignment_todos_file.exists():
            errors.append(
                "missing .local/workflow-artifacts/alignment/alignment-todos.md "
                "(required for architecture-impacting PRs)"
            )

    if errors:
        for err in errors:
            print(f"[BLOCK] {err}")
        return 1

    if args.check_only:
        print("[PASS] merge precheck passed.")
        return 0

    branch = args.branch or _current_branch()
    merge_sha = args.merge_sha or _head_sha()
    sha_source = "provided" if args.merge_sha else "git HEAD (fallback — prefer passing --merge-sha)"

    board_line = sync_board_after_merge(
        root=Path.cwd(),
        pr=args.pr,
        merge_sha=merge_sha,
        item_id=args.item_id,
        skip=args.skip_board_sync,
    )

    merge_file.write_text(
        "\n".join(
            [
                f"# Merge Artifact ({args.pr})",
                "",
                "## Attribution",
                f"- Action-By: {actor}",
                f"- Merged-By: {actor}",
                f"- GitHub-User: {github_user}",
                f"- Agent/s: {agents}",
                f"- Branch: {branch}",
                "",
                "## Preconditions",
                f"- review artifact present: {review_file.exists()}",
                f"- prepare artifact present: {prep_file.exists()}",
                f"- alignment audit present: {alignment_audit_file.exists()}",
                f"- alignment todos present: {alignment_todos_file.exists()}",
                "",
                "## Merge Summary",
                f"- merge SHA: {merge_sha} ({sha_source})",
                "- merge execution: completed via gh pr merge",
                f"- {board_line}",
                "",
                "## Agent Notes",
                "- (agent: add merge method, checks used as evidence, and follow-up work items below)",
                f"- {board_line}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Created {merge_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
