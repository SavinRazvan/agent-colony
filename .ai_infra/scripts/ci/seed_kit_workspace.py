"""
File: seed_kit_workspace.py
Path: .ai_infra/scripts/ci/seed_kit_workspace.py
Role: Seed gitignored .local/ workspace from versioned CI fixtures for kit-quality gates.
Used By:
 - .github/workflows/kit-quality.yml
 - Makefile ci-seed target
Depends On:
 - .ai_infra/templates/local-workspace/ci/kit-dev/
 - .ai_infra/scripts/pr/local_workflow_paths.py
Notes:
 - CI-only; consumers scaffold via install. Idempotent overwrite of fixture paths.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

FIXTURE_TRACKERS = (
    "session-pointer.md",
    "change-index.md",
    "plan.md",
    "work-tracker.md",
    "test-plan.md",
    "test-index.md",
)

USER_SETTINGS_FILES = (
    "github.collaboration.yaml",
    "mcp.agents.yaml",
)

DASHBOARD_HTML = ("index.html", "implementation-control-center.html")
DASHBOARD_ASSETS = ("site-nav.js", "local-shell.css", "local-markdown.js")


def _import_local_workflow_paths(root: Path):
    pr_scripts = root / ".ai_infra" / "scripts" / "pr"
    pr_str = str(pr_scripts)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import local_workflow_paths

    return local_workflow_paths


def fixture_root(root: Path, profile: str) -> Path:
    path = root / ".ai_infra" / "templates" / "local-workspace" / "ci" / profile
    if not path.is_dir():
        raise FileNotFoundError(f"missing CI fixtures: {path}")
    return path


def _copy_artifact_readme_stubs(root: Path, bucket_names: tuple[str, ...], log: list[str]) -> None:
    stubs_root = root / ".ai_infra" / "templates" / "local-workspace" / "artifact-stubs"
    for bucket in bucket_names:
        src = stubs_root / bucket / "README.md"
        dst = root / ".local" / "workflow-artifacts" / bucket / "README.md"
        if not src.is_file():
            continue
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        log.append(f"copy {src.relative_to(root)} -> {dst.relative_to(root)}")


def _seed_dashboards(root: Path, log: list[str]) -> None:
    ui_root = root / ".ai_infra" / "templates" / "local-workspace"
    dash = root / ".local" / "agents-control-center" / "dashboards"
    dash.mkdir(parents=True, exist_ok=True)
    log.append(f"mkdir {dash.relative_to(root)}")
    for name in DASHBOARD_HTML:
        src = ui_root / name
        dst = dash / name
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)
            log.append(f"copy {src.relative_to(root)} -> {dst.relative_to(root)}")
    for name in DASHBOARD_ASSETS:
        src = ui_root / name
        dst = dash / name
        if src.is_file():
            shutil.copy2(src, dst)
            log.append(f"copy+ {src.relative_to(root)} -> {dst.relative_to(root)}")


def seed_kit_workspace(root: Path, profile: str = "kit-dev") -> list[str]:
    root = root.resolve()
    fixtures = fixture_root(root, profile)
    log: list[str] = []

    current = root / ".local" / "index-and-planning" / "current"
    history = root / ".local" / "index-and-planning" / "history"
    user_settings = root / ".local" / "user_settings"
    for directory in (current, history, user_settings):
        directory.mkdir(parents=True, exist_ok=True)
        log.append(f"mkdir {directory.relative_to(root)}")

    lwp = _import_local_workflow_paths(root)
    lwp.ensure_workflow_artifacts_tree(root=root)
    for bucket in lwp.WORKFLOW_ARTIFACT_BUCKETS:
        log.append(f"mkdir {bucket}")

    _copy_artifact_readme_stubs(root, lwp.ARTIFACT_STUB_BUCKET_NAMES, log)
    _seed_dashboards(root, log)

    for name in FIXTURE_TRACKERS:
        src = fixtures / name
        dst = current / name
        if not src.is_file():
            raise FileNotFoundError(f"missing fixture tracker: {src}")
        shutil.copy2(src, dst)
        log.append(f"copy {src.relative_to(root)} -> {dst.relative_to(root)}")

    coverage_exemplar = (
        root / ".ai_infra" / "templates" / "local-workspace" / "exemplars" / "coverage-index.md"
    )
    coverage_dst = current / "coverage-index.md"
    if coverage_exemplar.is_file() and not coverage_dst.exists():
        shutil.copy2(coverage_exemplar, coverage_dst)
        log.append(f"copy {coverage_exemplar.relative_to(root)} -> {coverage_dst.relative_to(root)}")

    updates_src = fixtures / "updates-log.md"
    updates_current = current / "updates-log.md"
    if updates_src.is_file():
        shutil.copy2(updates_src, updates_current)
        log.append(f"copy {updates_src.relative_to(root)} -> {updates_current.relative_to(root)}")
        updates_history = history / "updates-log.md"
        shutil.copy2(updates_src, updates_history)
        log.append(f"copy {updates_src.relative_to(root)} -> {updates_history.relative_to(root)}")

    settings_fixtures = fixtures / "user_settings"
    if settings_fixtures.is_dir():
        user_settings.mkdir(parents=True, exist_ok=True)
        for name in USER_SETTINGS_FILES:
            src = settings_fixtures / name
            if src.is_file():
                dst = user_settings / name
                shutil.copy2(src, dst)
                log.append(f"copy {src.relative_to(root)} -> {dst.relative_to(root)}")

    pages = root / ".ai_infra" / "templates" / "local-workspace" / "pages.json"
    if pages.is_file():
        dst = root / ".local" / "agents-control-center" / "config" / "pages.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(pages, dst)
            log.append(f"copy {pages.relative_to(root)} -> {dst.relative_to(root)}")

    arch_stub = current / "architecture.md"
    if not arch_stub.is_file():
        arch_stub.write_text(
            "# Architecture\n\nCI workspace stub — project architecture under `docs/architecture/`.\n",
            encoding="utf-8",
        )
        log.append(f"write {arch_stub.relative_to(root)}")

    return log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed .local workspace for kit CI gates")
    parser.add_argument("--directory", type=Path, default=".", help="Kit repo root")
    parser.add_argument(
        "--profile",
        default="kit-dev",
        help="CI fixture profile under templates/local-workspace/ci/",
    )
    args = parser.parse_args(argv)

    try:
        log = seed_kit_workspace(args.directory, args.profile)
    except FileNotFoundError as exc:
        print(f"seed_kit_workspace: FAIL — {exc}")
        return 1

    print(f"seed_kit_workspace: PASS profile={args.profile}")
    for line in log:
        print(f" - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
