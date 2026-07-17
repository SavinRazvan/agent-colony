"""
File: verify_publish.py
Path: .ai_infra/scripts/pr/verify_publish.py
Role: Verifies local branch publication and upstream linkage before merge workflow.
Used By:
 - .agents/skills/pr-workflow/SKILL.md
Depends On:
 - argparse
 - subprocess
Notes:
 - Read-only verification script; does not modify git state.
 - When `--branch` is omitted, the current branch is read from `git branch --show-current`.
"""

from __future__ import annotations

import argparse
import subprocess


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify current branch publish state and upstream linkage."
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch to verify (default: current branch from git)",
    )
    args = parser.parse_args()

    branch = (args.branch or "").strip()
    if not branch:
        code, output = _run(["git", "branch", "--show-current"])
        if code != 0 or not output:
            print("Could not determine current branch; pass --branch explicitly.")
            if output:
                print(f"  detail: {output}")
            return 1
        branch = output.strip()
    if not branch:
        print("Branch name must not be empty.")
        return 1

    checks: list[tuple[str, bool, str]] = []

    current_code, current_output = _run(["git", "branch", "--show-current"])
    current_ok = current_code == 0 and current_output == branch
    checks.append(
        (
            f"current branch is {branch}",
            current_ok,
            current_output or "unable to resolve current branch",
        )
    )

    upstream_code, upstream_output = _run(
        ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"]
    )
    expected_upstream = f"origin/{branch}"
    upstream_ok = upstream_code == 0 and upstream_output == expected_upstream
    checks.append(
        (
            f"upstream is {expected_upstream}",
            upstream_ok,
            upstream_output or "missing upstream",
        )
    )

    remote_code, remote_output = _run(["git", "ls-remote", "--heads", "origin", branch])
    remote_ok = remote_code == 0 and bool(remote_output)
    checks.append(
        (
            "remote branch exists",
            remote_ok,
            remote_output or "branch not found on origin",
        )
    )

    failed = False
    for label, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {label}")
        if not ok:
            failed = True
            print(f"  detail: {detail}")

    if failed:
        print("Publish verification failed.")
        return 1

    print("Publish verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
