"""
File: generate_coverage_index.py
Path: .ai_infra/scripts/ci/generate_coverage_index.py
Role: Regenerate `.local/index-and-planning/current/coverage-index.md` from pytest coverage JSON.
Used By:
 - Makefile coverage-index target
 - implementer slice closure
Depends On:
 - paths.resolve_project_python
Notes:
 - Scope: `--cov=.ai_infra --cov=cursor_workflow` (shipped kit surface).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        kit = _candidate
        if str(kit / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(kit / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ensure_paths_import(kit)
        break

from paths import kit_root, resolve_project_python  # noqa: E402

LOW_THRESHOLD = 90.0
COV_SOURCES = (".ai_infra", "cursor_workflow")


def _run_coverage_json(root: Path) -> dict:
    cov_file = root / "coverage.json"
    py = resolve_project_python(root)
    cmd = [
        py,
        "-m",
        "pytest",
        "--cov=.ai_infra",
        "--cov=cursor_workflow",
        f"--cov-report=json:{cov_file}",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"pytest coverage failed:\n{proc.stdout}\n{proc.stderr}")
    return json.loads(cov_file.read_text(encoding="utf-8"))


def _collect_test_count(root: Path) -> int:
    py = resolve_project_python(root)
    proc = subprocess.run(
        [py, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pytest collect failed:\n{proc.stderr}")
    line = proc.stdout.strip().splitlines()[-1]
    # "603 tests collected in 0.19s"
    return int(line.split()[0])


def _module_key(path: str) -> str:
    parts = Path(path).parts
    if parts[0] == "cursor_workflow":
        return "cursor_workflow"
    if parts[0] == ".ai_infra":
        if len(parts) >= 3 and parts[1] == "scripts":
            return f".ai_infra/scripts/{parts[2]}"
        if len(parts) >= 3 and parts[1] == "install":
            return ".ai_infra/install/cursor_workflow"
        if len(parts) >= 3 and parts[1] == "mcp_servers":
            return ".ai_infra/mcp_servers/workflow_mcp"
        if len(parts) == 2:
            return f".ai_infra/{parts[1]}"
        return ".ai_infra/other"
    return path


def _aggregate(data: dict) -> tuple[int, int, int, dict[str, dict[str, int]]]:
    files = data.get("files", {})
    modules: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "stmts": 0, "miss": 0})
    total_stmts = 0
    total_miss = 0
    for rel, entry in files.items():
        if not any(rel.startswith(src) for src in COV_SOURCES):
            continue
        stmts = int(entry.get("summary", {}).get("num_statements", 0))
        miss = int(entry.get("summary", {}).get("missing_lines", 0))
        total_stmts += stmts
        total_miss += miss
        key = _module_key(rel)
        modules[key]["files"] += 1
        modules[key]["stmts"] += stmts
        modules[key]["miss"] += miss
    return total_stmts, total_miss, len(files), dict(modules)


def render_markdown(root: Path, data: dict, test_count: int) -> str:
    total_stmts, total_miss, file_count, modules = _aggregate(data)
    covered = total_stmts - total_miss
    pct = (covered / total_stmts * 100.0) if total_stmts else 0.0
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    lines = [
        "<!--",
        "File: coverage-index.md",
        "Path: .local/index-and-planning/current/coverage-index.md",
        "Role: Generated index of source coverage status by module and file.",
        "Used By:",
        " - .local/index-and-planning/current/test-plan.md",
        " - .local/index-and-planning/current/test-index.md",
        "Depends On:",
        " - .ai_infra/scripts/ci/generate_coverage_index.py",
        "Notes:",
        " - Regenerate via `make coverage-index` after coverage runs.",
        " - Scope is shipped source only (.ai_infra/** import surface + cursor_workflow/**).",
        "-->",
        "",
        "# Coverage Index",
        "",
        f"- Generated at (UTC): `{now}`",
        f"- Source files indexed: `{file_count}`",
        f"- Total statements: `{total_stmts}`",
        f"- Covered lines: `{covered}`",
        f"- Missing lines: `{total_miss}`",
        f"- Total coverage: `{pct:.2f}%`",
        f"- Low threshold: `{LOW_THRESHOLD}%`",
        f"- Test run: `{test_count} passed` (pytest, `{resolve_project_python(root)}`)",
        "",
        "## Module Coverage",
        "",
        "| Module | Files | Statements | Missing | Coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in sorted(modules):
        m = modules[key]
        mod_pct = ((m["stmts"] - m["miss"]) / m["stmts"] * 100.0) if m["stmts"] else 100.0
        lines.append(
            f"| `{key}` | {m['files']} | {m['stmts']} | {m['miss']} | {mod_pct:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## Files Below Threshold",
            "",
            "| File | Statements | Missing | Coverage |",
            "|---|---:|---:|---:|",
        ]
    )
    below = []
    for rel, entry in sorted(data.get("files", {}).items()):
        if not any(rel.startswith(src) for src in COV_SOURCES):
            continue
        stmts = int(entry.get("summary", {}).get("num_statements", 0))
        miss = int(entry.get("summary", {}).get("missing_lines", 0))
        if stmts and (stmts - miss) / stmts * 100.0 < LOW_THRESHOLD:
            below.append((rel, stmts, miss))
    if below:
        for rel, stmts, miss in below:
            file_pct = (stmts - miss) / stmts * 100.0
            lines.append(f"| `{rel}` | {stmts} | {miss} | {file_pct:.2f}% |")
    else:
        lines.append("| _(none)_ | 0 | 0 | 100.00% |")
    lines.extend(
        [
            "",
            "## Notes on the `tests/**` self-coverage residue",
            "",
            "Running with `--cov=.` (rather than scoped to shipped source) shows ~99% overall because a",
            "handful of defensive branches inside test-helper cleanup code (e.g. \"insert only if not",
            "already present\" guards, order-dependent `sys.path` restore paths) don't fire on every",
            "collection order. These are test-of-tests scaffolding, not part of the installable kit",
            "surface. Scope `--cov=.ai_infra --cov=cursor_workflow` for marketplace readiness claims.",
            "",
        ]
    )
    return "\n".join(lines)


def generate(root: Path, output: Path) -> None:
    data = _run_coverage_json(root)
    test_count = _collect_test_count(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(root, data, test_count), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate coverage-index.md from pytest coverage.")
    parser.add_argument("--directory", type=Path, default=kit_root(), help="Kit root")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: .local/index-and-planning/current/coverage-index.md)",
    )
    args = parser.parse_args(argv)
    root = args.directory.resolve()
    output = args.output or (root / ".local/index-and-planning/current/coverage-index.md")
    try:
        generate(root, output)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
