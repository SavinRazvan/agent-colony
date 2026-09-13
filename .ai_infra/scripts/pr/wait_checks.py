"""
File: wait_checks.py
Path: .ai_infra/scripts/pr/wait_checks.py
Role: Poll GitHub PR checks via ``gh pr checks`` (REST-backed CLI) without
  Projects GraphQL / statusCheckRollup loops that can Forbidden-storm.
Used By:
 - .agents/skills/merge-pr/SKILL.md
 - .agents/skills/full-pr-workflow/SKILL.md
 - .agents/skills/pr-workflow/SKILL.md
Depends On:
 - argparse
 - subprocess
 - re
Notes:
 - On Forbidden / 429 / rate-limit in stderr: exit immediately (do not retry-loop).
 - Do not call ``project api-ready`` (board-scoped GraphQL).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time

_THROTTLE_RE = re.compile(
    r"\b(403|Forbidden|429|rate[\s_-]?limit|API rate limit)\b",
    re.IGNORECASE,
)


def is_throttle_output(text: str) -> bool:
    return bool(_THROTTLE_RE.search(text or ""))


def _run_gh_pr_checks(pr: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["gh", "pr", "checks", str(pr)],
        capture_output=True,
        text=True,
    )
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, out


def wait_pr_checks(
    pr: str,
    *,
    timeout_sec: int = 600,
    interval_sec: int = 15,
    sleeper=time.sleep,
    runner=_run_gh_pr_checks,
) -> int:
    """
    Poll until checks pass (gh exit 0), fail hard on throttle, or timeout.

    Returns process-style exit code: 0 pass, 1 fail/timeout, 2 throttle.
    """
    if timeout_sec < 1:
        print("[BLOCK] --timeout-sec must be >= 1", file=sys.stderr)
        return 1
    if interval_sec < 1:
        print("[BLOCK] --interval-sec must be >= 1", file=sys.stderr)
        return 1

    deadline = time.monotonic() + timeout_sec
    while True:
        code, out = runner(pr)
        if is_throttle_output(out):
            print(
                "[BLOCK] gh pr checks hit Forbidden/429/rate-limit — "
                "do not retry; wait and re-run once.",
                file=sys.stderr,
            )
            if out:
                print(out, file=sys.stderr)
            return 2
        if code == 0:
            if out:
                print(out)
            print(f"[PASS] checks green for PR {pr}")
            return 0
        # Pending checks often exit non-zero with pending lines; keep polling
        # until timeout unless output clearly failed.
        lower = (out or "").lower()
        if "fail" in lower and "pending" not in lower and "pass" not in lower:
            print(out or f"[FAIL] gh pr checks exited {code}", file=sys.stderr)
            return 1
        if time.monotonic() >= deadline:
            print(
                f"[FAIL] timed out after {timeout_sec}s waiting for PR {pr} checks",
                file=sys.stderr,
            )
            if out:
                print(out, file=sys.stderr)
            return 1
        if out:
            print(out)
        print(f"[INFO] checks not green yet (exit={code}); sleep {interval_sec}s")
        sleeper(interval_sec)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Wait for GitHub PR checks via gh pr checks (REST-backed; no GraphQL)."
    )
    parser.add_argument("--pr", required=True, help="PR number")
    parser.add_argument("--timeout-sec", type=int, default=600)
    parser.add_argument("--interval-sec", type=int, default=15)
    args = parser.parse_args()
    return wait_pr_checks(
        str(args.pr).strip(),
        timeout_sec=args.timeout_sec,
        interval_sec=args.interval_sec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
