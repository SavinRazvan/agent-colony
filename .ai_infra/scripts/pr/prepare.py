"""
File: prepare.py
Path: .ai_infra/scripts/pr/prepare.py
Role: Runs preparation gates and emits local prepare artifact.
Used By:
 - .agents/skills/prepare-pr/SKILL.md
Depends On:
 - argparse
 - pathlib
 - subprocess
 - scripts/pr/local_workflow_paths.py
Notes:
 - Gate subprocesses use `sys.executable` (same interpreter as this script), not a bare `python` on PATH.
 - By default runs `resolve_gates()` (universal: check_testing_artifacts, pytest).
 - Kit-dev repos auto-append drift validate + doc facts when
   `.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md` exists (see `GATES_KIT_DEV_APPEND`).
 - Consumer projects keep universal gates only; append more at install time if needed.
 - Pass --skip-gates when the agent has already run and verified gates independently; the script
   then only writes the attribution/stamp block and marks gates as externally verified.
 - The script is the canonical source of the prep artifact; agent writes resolved findings,
   HEAD SHA, and residual risks into the file after the script creates the header.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_PR_DIR = Path(__file__).resolve().parent
if str(_PR_DIR) not in sys.path:
    sys.path.insert(0, str(_PR_DIR))

from local_workflow_paths import PREP_MD, ensure_workflow_artifacts_dir
from user_settings import add_pr_attribution_arguments, resolve_pr_attribution


GATES_UNIVERSAL = [
    ["python", ".ai_infra/scripts/pr/check_testing_artifacts.py"],
    ["python", "-m", "pytest", "-q"],
]

# Kit-dev only — appended when `is_kit_dev_root()` (same signal as doc-facts DOC-000 skip).
GATES_KIT_DEV_APPEND = [
    ["python", "-m", "cursor_workflow", "drift", "validate", "--directory", "."],
    ["python", ".ai_infra/scripts/architecture/check_doc_facts.py"],
]

# Back-compat alias for doc parsers and overlays that reference `GATES`.
GATES = GATES_UNIVERSAL


def is_kit_dev_root(root: Path) -> bool:
    return (root / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md").is_file()


def resolve_gates(root: Path | None = None) -> list[list[str]]:
    """Universal gates plus kit-dev append when IMPLEMENTATION-STATUS is present."""
    base = root or Path.cwd()
    gates = list(GATES_UNIVERSAL)
    if is_kit_dev_root(base):
        gates.extend(GATES_KIT_DEV_APPEND)
    return gates


def _resolve_gate_cmd(cmd: list[str]) -> list[str]:
    """Run gates with the same interpreter that executed this script (e.g. project venv)."""
    resolved = list(cmd)
    if resolved and resolved[0] == "python":
        resolved[0] = sys.executable
    return resolved


def _run(cmd: list[str]) -> tuple[int, str]:
    normalized = _resolve_gate_cmd(cmd)
    proc = subprocess.run(normalized, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def _current_branch() -> str:
    proc = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    return proc.stdout.strip() or "unknown"


def _head_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip() or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PR prepare gates and artifact generation.")
    parser.add_argument("--pr", required=True, help="PR number or URL")
    add_pr_attribution_arguments(parser)
    parser.add_argument(
        "--skip-gates",
        action="store_true",
        default=False,
        help=(
            "Skip running gates inside the script. Use when the agent already ran and "
            "verified all gates; the artifact will record gates as externally verified."
        ),
    )
    args = parser.parse_args()

    try:
        actor, agents, github_user = resolve_pr_attribution(
            root=Path.cwd(),
            actor=args.actor,
            agents=args.agents,
            pipeline=args.pipeline,
            agents_from_session=args.agents_from_session,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ensure_workflow_artifacts_dir()
    prep_file = PREP_MD

    branch = _current_branch()
    head_sha = _head_sha()

    lines = [
        f"# Prepare Artifact ({args.pr})",
        "",
        "## Attribution",
        f"- Action-By: {actor}",
        f"- Prepared-By: {actor}",
        f"- GitHub-User: {github_user}",
        f"- Agent/s: {agents}",
        f"- Branch: {branch}",
        f"- HEAD SHA: {head_sha}",
        "",
        "## Gate Results",
    ]

    failed = False
    if args.skip_gates:
        lines.append("- gates: externally verified by agent before this script call")
    else:
        for gate in resolve_gates(Path.cwd()):
            code, output = _run(gate)
            label = "PASS" if code == 0 else "FAIL"
            lines.append(f"- `{ ' '.join(_resolve_gate_cmd(gate)) }` -> {label}")
            if code != 0:
                failed = True
                lines.append("")
                lines.append("```text")
                lines.append(output)
                lines.append("```")

    lines.extend(
        [
            "",
            "## Status",
            "- PR is ready for /merge-pr" if not failed else "- NOT READY",
            "",
            "## Agent Notes",
            "- (agent: add resolved findings, residual risks, and follow-ups below)",
        ]
    )
    prep_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Created {prep_file}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
