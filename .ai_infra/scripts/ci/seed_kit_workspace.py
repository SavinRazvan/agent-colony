"""
File: seed_kit_workspace.py
Path: .ai_infra/scripts/ci/seed_kit_workspace.py
Role: Seed gitignored .local/ workspace from versioned CI fixtures for kit-quality gates.
Used By:
 - .github/workflows/kit-quality.yml
 - Makefile ci-seed target
Depends On:
 - .ai_infra/templates/local-workspace/ci/kit-dev/
Notes:
 - CI-only; consumers scaffold via install. Idempotent overwrite of fixture paths.
"""

from __future__ import annotations

import argparse
import shutil
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


def fixture_root(root: Path, profile: str) -> Path:
    path = root / ".ai_infra" / "templates" / "local-workspace" / "ci" / profile
    if not path.is_dir():
        raise FileNotFoundError(f"missing CI fixtures: {path}")
    return path


def seed_kit_workspace(root: Path, profile: str = "kit-dev") -> list[str]:
    root = root.resolve()
    fixtures = fixture_root(root, profile)
    log: list[str] = []

    current = root / ".local" / "index-and-planning" / "current"
    history = root / ".local" / "index-and-planning" / "history"
    user_settings = root / ".local" / "user_settings"
    for directory in (
        current,
        history,
        root / ".local" / "workflow-artifacts" / "pr",
        root / ".local" / "workflow-artifacts" / "drift",
        root / ".local" / "workflow-artifacts" / "alignment",
        root / ".local" / "agents-control-center" / "config",
    ):
        directory.mkdir(parents=True, exist_ok=True)
        log.append(f"mkdir {directory.relative_to(root)}")

    for name in FIXTURE_TRACKERS:
        src = fixtures / name
        dst = current / name
        if not src.is_file():
            raise FileNotFoundError(f"missing fixture tracker: {src}")
        shutil.copy2(src, dst)
        log.append(f"copy {src.relative_to(root)} -> {dst.relative_to(root)}")

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
