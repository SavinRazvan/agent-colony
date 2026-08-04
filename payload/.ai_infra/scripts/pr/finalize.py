"""
File: finalize.py
Path: .ai_infra/scripts/pr/finalize.py
Role: Performs deterministic post-merge cleanup for local and remote branches.
Used By:
 - .agents/skills/full-pr-workflow/SKILL.md
 - .agents/skills/pr-workflow/SKILL.md (optional manual cleanup)
 - .agents/skills/merge-pr/SKILL.md (defers cleanup to full-pr-workflow)
Depends On:
 - argparse
 - subprocess
 - local_workflow_paths.FINALIZE_MD
 - user_settings (optional attribution)
Notes:
 - Safe no-op when target branches are already removed.
 - Prunes stale remote-tracking refs to avoid branch-list drift.
 - Supports --dry-run for safe workflow validation without state changes.
 - Writes `.local/workflow-artifacts/pr/finalize.md` best-effort (does not block cleanup).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_PR_DIR = Path(__file__).resolve().parent
if str(_PR_DIR) not in sys.path:
    sys.path.insert(0, str(_PR_DIR))

from local_workflow_paths import FINALIZE_MD, ensure_workflow_artifacts_dir
from user_settings import add_pr_attribution_arguments, resolve_pr_attribution


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _current_branch() -> str:
    code, out = _run(["git", "branch", "--show-current"])
    if code != 0:
        return "unknown"
    return out.strip() or "unknown"


def _local_branch_exists(branch: str) -> bool:
    code, _ = _run(["git", "show-ref", "--verify", f"refs/heads/{branch}"])
    return code == 0


def _remote_branch_exists(branch: str) -> bool:
    code, out = _run(["git", "ls-remote", "--heads", "origin", branch])
    return code == 0 and bool(out.strip())


def _list_local_merged_branches() -> list[str]:
    code, out = _run(["git", "branch", "--merged", "main"])
    if code != 0:
        return []
    branches: list[str] = []
    for raw in out.splitlines():
        cleaned = raw.replace("*", "").strip()
        if cleaned:
            branches.append(cleaned)
    return branches


def _run_step(
    cmd: list[str],
    step_name: str,
    failures: list[str],
    logs: list[str],
    dry_run: bool = False,
) -> bool:
    logs.append(f"[STEP] {step_name}: {' '.join(cmd)}")
    if dry_run:
        logs.append("[DRY-RUN] skipped execution")
        return True
    code, out = _run(cmd)
    if out:
        logs.append(out)
    if code != 0:
        failures.append(f"{step_name} failed (exit={code})")
        return False
    return True


def _finish(logs: list[str], failures: list[str], dry_run: bool = False) -> int:
    for line in logs:
        print(line)
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    if dry_run:
        print("[PASS] finalize workflow dry-run completed.")
    else:
        print("[PASS] finalize workflow cleanup completed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize merged PR workflow and clean branches.")
    parser.add_argument(
        "--branch",
        required=True,
        help="Merged feature/chore/fix branch to remove locally/remotely.",
    )
    parser.add_argument(
        "--pr",
        default=None,
        help="PR number or URL (optional; used only for finalize artifact header).",
    )
    parser.add_argument(
        "--delete-merged-local",
        action="store_true",
        default=False,
        help="Also delete other local branches already merged into main.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print planned steps without executing git mutations.",
    )
    add_pr_attribution_arguments(parser)
    args = parser.parse_args()

    branch = args.branch.strip()
    if not branch:
        print("[BLOCK] --branch must not be empty.")
        return 1

    failures: list[str] = []
    logs: list[str] = []

    current_branch = _current_branch()
    checkout_attempted = current_branch != "main"

    if branch == "main":
        print("[BLOCK] Refusing to finalize with --branch main.")
        return 1

    if checkout_attempted:
        if not _run_step(
            ["git", "checkout", "main"],
            "checkout-main",
            failures,
            logs,
            dry_run=args.dry_run,
        ):
            return _finish(logs, failures, dry_run=args.dry_run)

    if not _run_step(
        ["git", "pull", "--ff-only", "origin", "main"],
        "pull-main",
        failures,
        logs,
        dry_run=args.dry_run,
    ):
        return _finish(logs, failures, dry_run=args.dry_run)
    if not _run_step(
        ["git", "fetch", "--prune", "origin"],
        "fetch-prune-origin",
        failures,
        logs,
        dry_run=args.dry_run,
    ):
        return _finish(logs, failures, dry_run=args.dry_run)

    local_exists_before = _local_branch_exists(branch)
    remote_exists_before = _remote_branch_exists(branch)

    if local_exists_before:
        _run_step(
            ["git", "branch", "-d", branch],
            f"delete-local-{branch}",
            failures,
            logs,
            dry_run=args.dry_run,
        )
    else:
        logs.append(f"[INFO] local branch already absent: {branch}")

    if remote_exists_before:
        _run_step(
            ["git", "push", "origin", "--delete", branch],
            f"delete-remote-{branch}",
            failures,
            logs,
            dry_run=args.dry_run,
        )
    else:
        logs.append(f"[INFO] remote branch already absent: origin/{branch}")

    if args.delete_merged_local:
        for merged_branch in _list_local_merged_branches():
            if merged_branch in {"main", branch}:
                continue
            _run_step(
                ["git", "branch", "-d", merged_branch],
                f"delete-local-merged-{merged_branch}",
                failures,
                logs,
                dry_run=args.dry_run,
            )

    if not args.dry_run:
        if _local_branch_exists(branch):
            failures.append(f"local branch still exists after finalize: {branch}")
        if _remote_branch_exists(branch):
            failures.append(f"remote branch still exists after finalize: origin/{branch}")

    _run_step(
        ["git", "status", "--short", "--branch"],
        "final-status",
        failures,
        logs,
        dry_run=args.dry_run,
    )

    # Always try to write finalize artifact as best-effort evidence for other agents.
    _write_finalize_artifact(
        finalize_md=FINALIZE_MD,
        branch=branch,
        pr_ref=args.pr,
        dry_run=args.dry_run,
        delete_merged_local=args.delete_merged_local,
        failures=failures,
        logs=logs,
        checkout_attempted=checkout_attempted,
        local_exists_before=local_exists_before,
        remote_exists_before=remote_exists_before,
        actor=args.actor,
        agents=args.agents,
        pipeline=args.pipeline,
        agents_from_session=args.agents_from_session,
    )

    return _finish(logs, failures, dry_run=args.dry_run)


def _step_failed(failures: list[str], step_prefix: str) -> bool:
    return any(line.startswith(step_prefix) for line in failures)


def _resolve_attribution_best_effort(
    *,
    root: Path,
    actor: str | None,
    agents: str | None,
    pipeline: str | None,
    agents_from_session: bool,
) -> tuple[str, str, str]:
    actor_fallback = (actor or "").strip() or "unknown"
    agents_fallback = (agents or "").strip() or "unknown"
    github_user_fallback = "unknown"

    try:
        resolved_actor, resolved_agents, github_user = resolve_pr_attribution(
            root=root,
            actor=actor,
            agents=agents,
            pipeline=pipeline,
            agents_from_session=agents_from_session,
        )
        return resolved_actor, resolved_agents, github_user
    except Exception:  # noqa: BLE001 - best-effort attribution only
        return actor_fallback, agents_fallback, github_user_fallback


def _write_finalize_artifact(
    *,
    finalize_md: Path,
    branch: str,
    pr_ref: str | None,
    dry_run: bool,
    delete_merged_local: bool,
    failures: list[str],
    logs: list[str],
    checkout_attempted: bool,
    local_exists_before: bool,
    remote_exists_before: bool,
    actor: str | None,
    agents: str | None,
    pipeline: str | None,
    agents_from_session: bool,
) -> None:
    try:
        ensure_workflow_artifacts_dir()

        pr_head = (pr_ref or "").strip() or "unknown"
        root = Path.cwd()
        resolved_actor, resolved_agents, resolved_github_user = (
            _resolve_attribution_best_effort(
                root=root,
                actor=actor,
                agents=agents,
                pipeline=pipeline,
                agents_from_session=agents_from_session,
            )
        )

        status = "DRY-RUN" if dry_run else ("PASS" if not failures else "FAIL")

        checkout_main = (
            "already on main" if not checkout_attempted else "executed"
        )
        if checkout_attempted and _step_failed(failures, "checkout-main"):
            checkout_main = "FAIL"

        pull_main = "skipped (checkout-main fail)" if _step_failed(failures, "checkout-main") else (
            "FAIL" if _step_failed(failures, "pull-main") else "ok"
        )
        fetch_main = "FAIL" if _step_failed(failures, "fetch-prune-origin") else "ok"

        local_delete_status: str
        local_delete_step = f"delete-local-{branch}"
        if not local_exists_before:
            local_delete_status = "already absent"
        elif _step_failed(failures, local_delete_step):
            local_delete_status = "FAIL"
        else:
            local_delete_status = "ok"

        remote_delete_status: str
        remote_delete_step = f"delete-remote-{branch}"
        if not remote_exists_before:
            remote_delete_status = "already absent"
        elif _step_failed(failures, remote_delete_step):
            remote_delete_status = "FAIL"
        else:
            remote_delete_status = "ok"

        # Keep artifact compact: store only the most recent log lines.
        tail_logs = logs[-25:]

        finalize_md.write_text(
            "\n".join(
                [
                    f"# Finalize Artifact ({pr_head})",
                    "",
                    "## Attribution",
                    f"- Action-By: {resolved_actor}",
                    f"- GitHub-User: {resolved_github_user}",
                    f"- Agent/s: {resolved_agents}",
                    f"- Branch: {branch}",
                    "",
                    "## Cleanup Results",
                    f"- checkout main: {checkout_main}",
                    f"- pull main: {pull_main}",
                    f"- fetch --prune origin: {fetch_main}",
                    f"- delete local branch ({branch}): {local_delete_status}",
                    f"- delete remote branch ({branch}): {remote_delete_status}",
                    f"- delete-merged-local: {delete_merged_local}",
                    f"- dry-run: {dry_run}",
                    "",
                    "## Evidence (compact logs)",
                    "```text",
                    *tail_logs,
                    "```",
                    "",
                    f"## Status",
                    f"- {status}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"Created {finalize_md}")
    except Exception:  # noqa: BLE001 - finalize artifact must not block cleanup
        print("[WARN] finalize artifact write failed (best-effort).", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
