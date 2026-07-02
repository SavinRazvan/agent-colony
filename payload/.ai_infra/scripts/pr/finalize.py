"""
File: finalize.py
Path: .ai_infra/scripts/pr/finalize.py
Role: Performs deterministic post-merge cleanup for local and remote branches.
Used By:
 - .agents/skills/pr-workflow/SKILL.md
 - .agents/skills/merge-pr/SKILL.md
Depends On:
 - argparse
 - subprocess
Notes:
 - Safe no-op when target branches are already removed.
 - Prunes stale remote-tracking refs to avoid branch-list drift.
 - Supports --dry-run for safe workflow validation without state changes.
"""

from __future__ import annotations

import argparse
import subprocess


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
    args = parser.parse_args()

    branch = args.branch.strip()
    if not branch:
        print("[BLOCK] --branch must not be empty.")
        return 1

    failures: list[str] = []
    logs: list[str] = []

    if branch == "main":
        print("[BLOCK] Refusing to finalize with --branch main.")
        return 1

    if _current_branch() != "main":
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

    if _local_branch_exists(branch):
        _run_step(
            ["git", "branch", "-d", branch],
            f"delete-local-{branch}",
            failures,
            logs,
            dry_run=args.dry_run,
        )
    else:
        logs.append(f"[INFO] local branch already absent: {branch}")

    if _remote_branch_exists(branch):
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
    return _finish(logs, failures, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
