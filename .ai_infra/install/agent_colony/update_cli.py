"""
File: update_cli.py
Path: .ai_infra/install/agent_colony/update_cli.py
Role: Version-gated consumer kit upgrade — heal when current, full scaffold when newer.
Used By:
 - .ai_infra/install/agent_colony/cli.py
 - .cursor/skills/update-agent-colony/SKILL.md
Depends On:
 - .ai_infra/install/agent_colony/activate_cli.py
 - .ai_infra/scripts/install/plane_status.py
 - .ai_infra/scripts/install/scaffold.py (via activate force path)
Notes:
 - First install remains activate; update is for already-activated apps after plugin/kit bump.
 - ensure_kit_version_stamp: fallback when scaffold exits 0 but leaves stale .kit-version.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

import activate_cli


_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[.-].*)?$")
# Same marker scaffold uses to detect the kit product repo (not a consumer app).
KIT_TESTS_MARKER = Path("tests") / "modules" / "install" / "test_scaffold.py"


def is_kit_dev_repo(target: Path) -> bool:
    """True when target is the Agent Colony product repo (full kit tests present)."""
    return (target / KIT_TESTS_MARKER).is_file()


def read_installed_version(target: Path) -> str | None:
    path = target / ".ai_infra" / ".kit-version"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def read_source_version(source: Path) -> str:
    manifest = source / ".ai_infra" / "manifest.yaml"
    if not manifest.is_file():
        raise FileNotFoundError(f"missing manifest: {manifest}")
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid manifest (not a mapping): {manifest}")
    version = str(raw.get("kit_version", "")).strip()
    if not version:
        raise ValueError(f"manifest missing kit_version: {manifest}")
    return version


def ensure_kit_version_stamp(target: Path, available: str) -> None:
    """Write `.ai_infra/.kit-version` when scaffold skipped or left a stale stamp."""
    stamp_path = target / ".ai_infra" / ".kit-version"
    current = stamp_path.read_text(encoding="utf-8").strip() if stamp_path.is_file() else ""
    if current != available:
        stamp_path.parent.mkdir(parents=True, exist_ok=True)
        stamp_path.write_text(f"{available}\n", encoding="utf-8")


def _parse_version_tuple(version: str) -> tuple[int, ...] | None:
    match = _VERSION_RE.match(version.strip())
    if not match:
        return None
    parts = [int(p) if p is not None else 0 for p in match.groups()]
    return tuple(parts)


def compare_versions(installed: str, available: str) -> int:
    """Return -1 if installed < available, 0 if equal, 1 if installed > available."""
    left = _parse_version_tuple(installed)
    right = _parse_version_tuple(available)
    if left is not None and right is not None:
        if left < right:
            return -1
        if left > right:
            return 1
        return 0
    if installed == available:
        return 0
    return -1 if installed < available else 1


def decide_action(*, installed: str | None, available: str, force: bool) -> str:
    """Return heal | upgrade | missing."""
    if installed is None:
        return "missing"
    if force:
        return "upgrade"
    if compare_versions(installed, available) < 0:
        return "upgrade"
    return "heal"


def _run_scaffold_upgrade(
    target: Path,
    source: Path,
    *,
    profile: str,
    with_venv: bool,
    with_mcp_json: bool,
    verify: bool,
) -> int:
    from paths import kit_root, scripts_dir

    script = scripts_dir("install", kit_root()) / "scaffold.py"
    cmd = [
        sys.executable,
        str(script),
        "--target",
        str(target),
        "--source",
        str(source),
        "--profile",
        profile,
    ]
    if with_venv:
        cmd.append("--with-venv")
    if with_mcp_json:
        cmd.append("--with-mcp-json")
    if verify:
        cmd.append("--verify")
    proc = subprocess.run(cmd, cwd=kit_root())
    return int(proc.returncode)


def _run_light_heal(target: Path, source: Path, *, with_venv: bool) -> None:
    from paths import kit_root

    if is_kit_dev_repo(target):
        # Do not copy payload install/scripts onto kit-dev authoring SSOT.
        scaffold = activate_cli._import_scaffold_refresh()
        for line in scaffold.sync_kit_ui_templates(source, target):
            print(line)
        ui_root = scaffold.ui_local_workspace(source)
        log: list[str] = []
        scaffold._scaffold_dashboards(ui_root, target, False, log)
        for line in log:
            print(line)
        activate_cli._heal_consumer_runtime(target, with_venv=with_venv)
        return

    activate_cli._refresh_dashboard_templates(target, source, kit_root())
    activate_cli._heal_consumer_runtime(target, with_venv=with_venv)


def _refuse_kit_dev_upgrade() -> int:
    print(
        "update: FAIL — full upgrade is for consumer apps, not the kit-dev product repo.\n"
        "  Kit-dev: edit sources → make sync-plugin (updates payload/) → commit/push.\n"
        "  Consumer apps: python3 -m agent_colony update --directory . "
        "(after updating the Agent Colony plugin).",
        file=sys.stderr,
    )
    return 1


KIT_AGENT_RELPATHS: tuple[str, ...] = tuple(
    f".cursor/agents/{agent_id}.md" for agent_id in (
        "auditor",
        "board",
        "drift-guard",
        "implementer",
        "integrator",
        "researcher",
        "test-runner",
        "verifier",
    )
)


def load_kit_managed_globs(source: Path) -> tuple[str, ...]:
    """Read kit_managed_globs from install-contract on the payload source."""
    contract = source / ".ai_infra" / "install-contract.json"
    if not contract.is_file():
        return KIT_AGENT_RELPATHS
    raw = json.loads(contract.read_text(encoding="utf-8"))
    profiles = raw.get("profiles") if isinstance(raw, dict) else None
    default = profiles.get("default") if isinstance(profiles, dict) else None
    globs = default.get("kit_managed_globs") if isinstance(default, dict) else None
    if isinstance(globs, list) and globs:
        return tuple(str(item) for item in globs)
    return KIT_AGENT_RELPATHS


def _managed_files_under(root: Path, globs: tuple[str, ...]) -> set[str]:
    if not root.is_dir():
        return set()
    found: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(fnmatch.fnmatch(rel, pattern) for pattern in globs):
            found.add(rel)
    return found


def scan_kit_agent_deltas(target: Path, source: Path) -> tuple[list[str], list[str]]:
    """
    Diff kit-managed paths (install-contract kit_managed_globs) vs payload source.
    Returns (hard_fail_paths, warn_extra_agent_paths).
    """
    globs = load_kit_managed_globs(source)
    failures: list[str] = []
    kit_ids = {Path(p).name.replace(".md", "") for p in KIT_AGENT_RELPATHS}
    source_files = _managed_files_under(source, globs)
    target_files = _managed_files_under(target, globs)
    for rel in sorted(source_files | target_files):
        installed = target / rel
        payload = source / rel
        if installed.is_file() and payload.is_file():
            if installed.read_bytes() != payload.read_bytes():
                failures.append(rel)
        elif installed.is_file() and not payload.is_file():
            failures.append(f"{rel} (missing in source payload)")
    warnings: list[str] = []
    agents_dir = target / ".cursor" / "agents"
    if agents_dir.is_dir():
        for path in sorted(agents_dir.glob("*.md")):
            if path.stem not in kit_ids:
                warnings.append(str(path.relative_to(target)))
    return failures, warnings


def _print_kit_delta_check(
    target: Path, source: Path, *, action: str, force: bool
) -> int:
    del action, force  # --check always fails on managed deltas
    failures, warnings = scan_kit_agent_deltas(target, source)
    for rel in warnings:
        print(f"check: warn integrator agent {rel}")
    for rel in failures:
        print(f"check: kit-managed delta {rel}")
    if failures:
        print(
            "check: FAIL — local kit-managed edits would be overwritten on full refresh; "
            "stash or commit intentionally before update --force",
            file=sys.stderr,
        )
        return 1
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    from paths import kit_root

    target = Path(args.directory).resolve()
    if not (target / ".ai_infra").is_dir():
        print(
            "update: FAIL — workspace not activated (.ai_infra missing). "
            "Run: python3 -m agent_colony activate --directory .",
            file=sys.stderr,
        )
        return 1

    try:
        source = activate_cli.resolve_activate_source(args.source, target, kit_root())
    except FileNotFoundError as exc:
        print(f"update: FAIL — {exc}", file=sys.stderr)
        return 1

    if source.resolve() == target.resolve():
        print(
            "update: FAIL — cannot upgrade a workspace from itself; "
            "pass --source <kit-root|payload/> or set WORKFLOW_KIT_PAYLOAD",
            file=sys.stderr,
        )
        return 1

    try:
        available = read_source_version(source)
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"update: FAIL — {exc}", file=sys.stderr)
        return 1

    installed = read_installed_version(target)
    action = decide_action(
        installed=installed,
        available=available,
        force=bool(args.force),
    )
    kit_dev = is_kit_dev_repo(target)

    print(f"installed={installed or '(none)'}")
    print(f"available={available}")
    print(f"source={source}")
    print(f"action={action}")
    if kit_dev:
        print("target_kind=kit-dev")

    if args.check:
        if action == "missing":
            print("check: would_activate (no .kit-version — run activate first)")
            return 1
        if action == "upgrade" and kit_dev:
            print("check: would_refuse_kit_dev (full upgrade not allowed here)")
            return 1
        if action == "upgrade":
            print("check: would_upgrade (full kit-managed refresh)")
        else:
            print("check: would_heal (dashboards + runtime gitignore/STARTER/venv)")
        return _print_kit_delta_check(
            target, source, action=action, force=bool(args.force)
        )

    if action == "missing":
        print(
            "update: FAIL — missing .ai_infra/.kit-version. "
            "First install: python3 -m agent_colony activate --directory .",
            file=sys.stderr,
        )
        return 1

    if action == "upgrade" and kit_dev:
        return _refuse_kit_dev_upgrade()

    plane_status = activate_cli._import_plane_status()

    if action == "heal":
        print("\nKit up to date — light heal (dashboards + runtime).")
        _run_light_heal(target, source, with_venv=bool(args.with_venv))
        status = plane_status.assess_planes(
            target, profile=args.profile, require_venv=bool(args.with_venv)
        )
        print(plane_status.format_plane_report(status))
        if not status.all_ready:
            print("update: FAIL — runtime still incomplete after heal", file=sys.stderr)
            return 1
        print("update: OK — healed (no version bump)")
        return 0

    print(f"\nUpgrading three planes from {source} → {target}")
    code = _run_scaffold_upgrade(
        target,
        source,
        profile=args.profile,
        with_venv=bool(args.with_venv),
        with_mcp_json=bool(args.with_mcp_json),
        verify=bool(args.verify),
    )
    if code != 0:
        return code

    ensure_kit_version_stamp(target, available)
    activate_cli._heal_consumer_runtime(target, with_venv=bool(args.with_venv))
    status = plane_status.assess_planes(
        target, profile=args.profile, require_venv=bool(args.with_venv)
    )
    print("\nPost-update plane status:")
    print(plane_status.format_plane_report(status))
    if not status.all_ready:
        print("update: FAIL — planes still incomplete after upgrade", file=sys.stderr)
        return 1

    new_installed = read_installed_version(target)
    print(f"update: OK — upgraded to {new_installed or available}")
    print("Preserved: AGENTS.md (if present), mcp.user.json, .local/user_settings/, trackers.")
    print("Next: python3 -m agent_colony health && python3 -m agent_colony mcp validate")
    return 0


def register_update_subparser(sub: argparse._SubParsersAction) -> None:
    update = sub.add_parser(
        "update",
        help="Version-gated kit upgrade (heal if current; full refresh if newer)",
    )
    update.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Target workspace (default: current directory)",
    )
    update.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Kit root or payload/ (default: same auto-resolve as activate)",
    )
    update.add_argument(
        "--profile",
        default="with_mcp",
        choices=("default", "with_mcp"),
        help="Install profile (default: with_mcp)",
    )
    update.add_argument("--with-venv", action="store_true", default=True)
    update.add_argument("--no-venv", action="store_false", dest="with_venv")
    update.add_argument("--with-mcp-json", action="store_true", default=True)
    update.add_argument("--no-mcp-json", action="store_false", dest="with_mcp_json")
    update.add_argument("--verify", action="store_true", default=True)
    update.add_argument("--no-verify", action="store_false", dest="verify")
    update.add_argument(
        "--check",
        action="store_true",
        help="Report installed vs available and planned action; no writes",
    )
    update.add_argument(
        "--force",
        action="store_true",
        help="Full kit-managed refresh even when versions match",
    )
    update.set_defaults(func=cmd_update)
