"""
File: verify_all.py
Path: .ai_infra/scripts/architecture/verify_all.py
Role: Maintainer verify-all matrix aligned with kit-quality.yml gate step.
Used By:
 - Makefile verify-all target
 - cursor_workflow verify all
 - workflow_mcp workflow_verify_all
Depends On:
 - subprocess, sys, pathlib (stdlib)
Notes:
 - Runs sync-plugin before check-plugin; seeds CI workspace when .local missing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ensure_paths_import(__file__)
        break


@dataclass
class StepResult:
    name: str
    command: list[str]
    exit_code: int
    output: str


def _run_step(name: str, cmd: list[str], root: Path) -> StepResult:
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
    )
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return StepResult(name=name, command=cmd, exit_code=proc.returncode, output=output)


def run_verify_all(root: Path, py: str) -> list[StepResult]:
    ci = root / ".ai_infra" / "scripts" / "ci"
    release = root / ".ai_infra" / "scripts" / "release"
    planning = root / ".local" / "index-and-planning" / "current"
    steps: list[tuple[str, list[str]]] = []
    if not planning.is_dir():
        steps.append(
            (
                "ci-seed",
                [py, str(ci / "seed_kit_workspace.py"), "--directory", str(root)],
            )
        )
    steps.extend(
        [
            ("sync-plugin", [py, str(release / "sync_plugin_bundle.py")]),
            ("gates", [py, "-m", "cursor_workflow", "gates", "--directory", str(root)]),
            (
                "drift-validate",
                [py, "-m", "cursor_workflow", "drift", "validate", "--directory", str(root)],
            ),
            (
                "integrate-validate",
                [py, "-m", "cursor_workflow", "integrate", "validate", "--directory", str(root)],
            ),
            ("check-plugin", [py, str(release / "sync_plugin_bundle.py"), "--check"]),
            ("health", [py, "-m", "cursor_workflow", "health", "--directory", str(root)]),
            (
                "contributors-validate",
                [py, "-m", "cursor_workflow", "contributors", "validate", "--directory", str(root)],
            ),
        ]
    )
    return [_run_step(name, cmd, root) for name, cmd in steps]


def format_report(results: list[StepResult]) -> str:
    lines: list[str] = []
    failed = 0
    for result in results:
        status = "PASS" if result.exit_code == 0 else "FAIL"
        if result.exit_code != 0:
            failed += 1
        lines.append(f"[{status}] {result.name}: {' '.join(result.command)}")
        if result.exit_code != 0 and result.output:
            lines.append(result.output)
    lines.append(f"summary: failed={failed} total={len(results)}")
    return "\n".join(lines)


def exit_code_for(results: list[StepResult]) -> int:
    return 1 if any(result.exit_code != 0 for result in results) else 0


def write_preflight_json(results: list[StepResult], output: Path) -> None:
    payload = {
        "command": "python -m cursor_workflow verify all",
        "steps": [
            {
                "name": r.name,
                "command": r.command,
                "exit_code": r.exit_code,
                "output_tail": r.output[-2000:] if r.output else "",
            }
            for r in results
        ],
        "exit_code": exit_code_for(results),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run maintainer verify-all matrix")
    parser.add_argument("--directory", type=Path, default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--preflight-out",
        type=Path,
        default=None,
        help="Write JSON preflight artifact under .local/workflow-artifacts/audit/",
    )
    args = parser.parse_args(argv)
    root = args.directory.resolve()
    results = run_verify_all(root, sys.executable)
    if args.preflight_out is not None:
        write_preflight_json(results, args.preflight_out)
    if args.json:
        payload = {
            "steps": [
                {
                    "name": r.name,
                    "exit_code": r.exit_code,
                    "command": r.command,
                }
                for r in results
            ],
            "exit_code": exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(results))
    return exit_code_for(results)


if __name__ == "__main__":
    raise SystemExit(main())
