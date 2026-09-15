"""
File: debug_cli.py
Path: .ai_infra/install/agent_colony/debug_cli.py
Role: Argparse command surface for secure debugger runtime campaigns.
Used By:
 - .ai_infra/install/agent_colony/cli.py
Depends On:
 - .ai_infra/install/agent_colony/debug_campaign.py
 - .ai_infra/install/agent_colony/debug_capture.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import debug_campaign
import debug_capture
import debug_storage

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def _ok(command: str, detail: str) -> int:
    print(f"debug {command}: PASS — {detail}")
    return EXIT_OK


def _fail(command: str, code: int, reason: str) -> int:
    print(f"debug {command}: FAIL — CODE={code} · {reason}", file=sys.stderr)
    return code


def _run(command: str, fn) -> int:  # noqa: ANN001
    try:
        return int(fn())
    except (
        debug_campaign.DebugCampaignError,
        debug_capture.DebugCaptureError,
        debug_storage.DebugStorageError,
    ) as exc:
        return _fail(command, EXIT_FAIL, str(exc))


def cmd_init(args: argparse.Namespace) -> int:
    def work() -> int:
        path = debug_campaign.init_campaign(
            root=Path(args.directory),
            slug=args.slug,
            mode=args.mode,
            item_id=args.item_id,
            lenses=[x.strip() for x in args.lenses.split(",") if x.strip()],
            supersedes=args.supersedes,
        )
        return _ok("init", f"campaign={path}")

    return _run("init", work)


def cmd_inventory(args: argparse.Namespace) -> int:
    def work() -> int:
        inv = debug_campaign.inventory_campaign(Path(args.directory), args.slug)
        cats = inv["categories"]
        return _ok("inventory", f"tracked={cats['tracked']} untracked={cats['untracked']} digest={inv['digest']}")

    return _run("inventory", work)


def cmd_capture(args: argparse.Namespace) -> int:
    def work() -> int:
        argv = list(args.argv)
        if argv and argv[0] == "--":
            argv = argv[1:]
        if not argv:
            raise debug_capture.DebugCaptureError("capture requires argv after --")
        result = debug_campaign.capture(
            Path(args.directory),
            args.slug,
            argv=argv,
            cwd=args.cwd,
            timeout_s=args.timeout,
            propagate_exit=args.propagate_exit,
        )
        print(
            "debug capture: PASS — "
            f"run={result.run_id} child_exit_code={result.child_exit_code} "
            f"termination={result.termination_reason} artifact={result.run_dir}"
        )
        if not args.propagate_exit:
            return EXIT_OK
        if result.termination_reason == "timeout":
            return 124
        if result.termination_reason == "output_limit":
            return 125
        code = result.child_exit_code or 0
        return min(255, 128 + abs(code)) if code < 0 else min(255, code)

    return _run("capture", work)


def cmd_ingest(args: argparse.Namespace) -> int:
    def work() -> int:
        stdin_bytes = None
        source = args.file
        if source is None and not sys.stdin.isatty():
            stdin_bytes = sys.stdin.buffer.read()
        result = debug_campaign.ingest(
            Path(args.directory),
            args.slug,
            file_path=str(source) if source is not None else None,
            text=stdin_bytes.decode("utf-8", errors="replace") if stdin_bytes is not None else None,
        )
        return _ok("ingest", f"run={result.run_id} bytes={result.combined_bytes} artifact={result.run_dir}")

    return _run("ingest", work)


def cmd_analyze(args: argparse.Namespace) -> int:
    def work() -> int:
        path = debug_campaign.analyze_run(Path(args.directory), args.slug, args.run, verdict=args.verdict)
        return _ok("analyze", f"summary={path}")

    return _run("analyze", work)


def cmd_note(args: argparse.Namespace) -> int:
    def work() -> int:
        debug_campaign.append_note(Path(args.directory), args.slug, args.text, agent=args.agent)
        return _ok("note", "appended")

    return _run("note", work)


def cmd_artifact_register(args: argparse.Namespace) -> int:
    def work() -> int:
        record = debug_campaign.register_artifact(Path(args.directory), args.slug, args.skill_id, args.path)
        return _ok("artifact register", f"path={record['path']} sha256={record['sha256']}")

    return _run("artifact register", work)


def cmd_probe_register(args: argparse.Namespace) -> int:
    def work() -> int:
        debug_campaign.register_probe(Path(args.directory), args.slug, args.probe_id, args.path, args.note)
        return _ok("probe register", f"probe={args.probe_id}")

    return _run("probe register", work)


def cmd_probe_resolve(args: argparse.Namespace) -> int:
    def work() -> int:
        debug_campaign.resolve_probe(Path(args.directory), args.slug, args.probe_id, args.note)
        return _ok("probe resolve", f"probe={args.probe_id}")

    return _run("probe resolve", work)


def cmd_probe_scan(args: argparse.Namespace) -> int:
    def work() -> int:
        hits = debug_campaign.scan_probes(Path(args.directory), args.slug)
        for hit in hits:
            print(hit)
        return _ok("probe scan", f"hits={len(hits)}")

    return _run("probe scan", work)


def cmd_finding_add(args: argparse.Namespace) -> int:
    def work() -> int:
        finding_id = debug_campaign.finding_add(
            Path(args.directory),
            args.slug,
            kind=args.kind,
            summary=args.summary,
            severity=args.severity,
            paths=[args.path] if args.path else [],
        )
        return _ok("finding add", f"id={finding_id}")

    return _run("finding add", work)


def cmd_finding_update(args: argparse.Namespace) -> int:
    def work() -> int:
        row = debug_campaign.update_finding(Path(args.directory), args.slug, args.id, args.status, args.child_card)
        return _ok("finding update", f"id={row['id']} status={row['status']}")

    return _run("finding update", work)


def cmd_finding_render(args: argparse.Namespace) -> int:
    def work() -> int:
        debug_campaign.render_findings(Path(args.directory), args.slug)
        return _ok("finding render", "rendered")

    return _run("finding render", work)


def cmd_handoff(args: argparse.Namespace) -> int:
    def work() -> int:
        payload = debug_campaign.handoff_campaign(Path(args.directory), args.slug, next_agent=args.next_agent, outcome=args.outcome)
        return _ok("handoff", f"campaign={payload['campaign_id']} next={payload['next_agent']} outcome={payload['outcome']}")

    return _run("handoff", work)


def cmd_status(args: argparse.Namespace) -> int:
    def work() -> int:
        digest = debug_campaign.status_digest(Path(args.directory), args.slug)
        print(digest)
        return EXIT_OK

    return _run("status", work)


def cmd_validate(args: argparse.Namespace) -> int:
    def work() -> int:
        errors = debug_campaign.validate_campaign(Path(args.directory), args.slug, final=args.final)
        if errors:
            for err in errors:
                print(f" - {err}", file=sys.stderr)
            return _fail("validate", EXIT_FAIL, f"{len(errors)} error(s)")
        return _ok("validate", f"slug={args.slug}")

    return _run("validate", work)


def cmd_block(args: argparse.Namespace) -> int:
    def work() -> int:
        reason = f"{args.reason} · evidence={args.evidence} · next={args.next_action}"
        debug_campaign.block_campaign(Path(args.directory), args.slug, reason=reason, human_status=args.human_state)
        return _ok("block", "blocked")

    return _run("block", work)


def cmd_repair(args: argparse.Namespace) -> int:
    def work() -> int:
        if args.apply:
            issues = debug_campaign.repair_apply(Path(args.directory), args.slug, args.acknowledge or "")
            return _ok("repair", f"applied issues={len(issues)}")
        issues = debug_campaign.repair_check(Path(args.directory), args.slug)
        for issue in issues:
            print(issue)
        return _ok("repair", f"check issues={len(issues)}")

    return _run("repair", work)


def cmd_close(args: argparse.Namespace) -> int:
    def work() -> int:
        debug_campaign.close_campaign(Path(args.directory), args.slug, outcome=args.outcome)
        return _ok("close", "closed")

    return _run("close", work)


def register_debug_subparser(sub: argparse._SubParsersAction) -> None:
    debug = sub.add_parser("debug", help="Secure debugger campaign runtime")
    debug_sub = debug.add_subparsers(dest="debug_command", required=True)

    init = debug_sub.add_parser("init", help="Create campaign tree")
    _common(init)
    init.add_argument("--slug", required=True)
    init.add_argument("--mode", choices=("incident", "standardize", "structural", "deep"), default="incident")
    init.add_argument("--item-id", required=True)
    init.add_argument("--lenses", default="repro,error")
    init.add_argument("--supersedes", default=None)
    init.set_defaults(func=cmd_init)

    inventory = debug_sub.add_parser("inventory", help="Record workspace inventory")
    _campaign(inventory)
    inventory.set_defaults(func=cmd_inventory)

    capture = debug_sub.add_parser("capture", help="Run command after -- with secure capture")
    _campaign(capture)
    capture.add_argument("--cwd", default=None)
    capture.add_argument("--timeout", type=int, default=debug_capture.DEFAULT_TIMEOUT_SECONDS)
    capture.add_argument("--propagate-exit", action="store_true")
    capture.add_argument("argv", nargs=argparse.REMAINDER)
    capture.set_defaults(func=cmd_capture)

    ingest = debug_sub.add_parser("ingest", help="Ingest an existing log")
    _campaign(ingest)
    ingest.add_argument("--file", type=Path, default=None)
    ingest.set_defaults(func=cmd_ingest)

    analyze = debug_sub.add_parser("analyze", help="Draft run Signals summary")
    _campaign(analyze)
    analyze.add_argument("--run", required=True)
    analyze.add_argument("--verdict", choices=("confirmed", "ruled_out", "probable", "unknown"), default="unknown")
    analyze.set_defaults(func=cmd_analyze)

    note = debug_sub.add_parser("note", help="Append attributed session note")
    _campaign(note)
    note.add_argument("--agent", default="debugger")
    note.add_argument("--text", required=True)
    note.set_defaults(func=cmd_note)

    artifact = debug_sub.add_parser("artifact", help="Artifact commands")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)
    artifact_register = artifact_sub.add_parser("register", help="Register skill artifact")
    _campaign(artifact_register)
    artifact_register.add_argument("--skill-id", required=True)
    artifact_register.add_argument("--path", required=True)
    artifact_register.set_defaults(func=cmd_artifact_register)

    probe = debug_sub.add_parser("probe", help="Probe commands")
    probe_sub = probe.add_subparsers(dest="probe_command", required=True)
    probe_register = probe_sub.add_parser("register", help="Register active probe")
    _campaign(probe_register)
    probe_register.add_argument("--probe-id", required=True)
    probe_register.add_argument("--path", required=True)
    probe_register.add_argument("--note", default="")
    probe_register.set_defaults(func=cmd_probe_register)
    probe_resolve = probe_sub.add_parser("resolve", help="Resolve probe")
    _campaign(probe_resolve)
    probe_resolve.add_argument("--probe-id", required=True)
    probe_resolve.add_argument("--note", default="")
    probe_resolve.set_defaults(func=cmd_probe_resolve)
    probe_scan = probe_sub.add_parser("scan", help="Scan workspace for DEBUG-PROBE markers")
    _campaign(probe_scan)
    probe_scan.set_defaults(func=cmd_probe_scan)

    finding = debug_sub.add_parser("finding", help="Finding commands")
    finding_sub = finding.add_subparsers(dest="finding_command", required=True)
    finding_add = finding_sub.add_parser("add", help="Add finding")
    _campaign(finding_add)
    finding_add.add_argument("--kind", choices=("DBG", "TR", "SG"), required=True)
    finding_add.add_argument("--summary", required=True)
    finding_add.add_argument("--path", default="")
    finding_add.add_argument("--severity", default="medium")
    finding_add.set_defaults(func=cmd_finding_add)
    finding_update = finding_sub.add_parser("update", help="Update finding")
    _campaign(finding_update)
    finding_update.add_argument("--id", required=True)
    finding_update.add_argument("--status", default=None)
    finding_update.add_argument("--child-card", default=None)
    finding_update.set_defaults(func=cmd_finding_update)
    finding_render = finding_sub.add_parser("render", help="Render finding markdown")
    _campaign(finding_render)
    finding_render.set_defaults(func=cmd_finding_render)

    handoff_cmd = debug_sub.add_parser("handoff", help="Render handoff and ready campaign")
    _campaign(handoff_cmd)
    handoff_cmd.add_argument("--next-agent", required=True)
    handoff_cmd.add_argument("--outcome", default="ready")
    handoff_cmd.set_defaults(func=cmd_handoff)

    status = debug_sub.add_parser("status", help="Show campaign status")
    _campaign(status)
    status.add_argument("--digest", action="store_true")
    status.set_defaults(func=cmd_status)

    validate = debug_sub.add_parser("validate", help="Validate campaign")
    _campaign(validate)
    validate.add_argument("--final", action="store_true")
    validate.set_defaults(func=cmd_validate)

    block = debug_sub.add_parser("block", help="Mark campaign blocked")
    _campaign(block)
    block.add_argument("--reason", required=True)
    block.add_argument("--evidence", required=True)
    block.add_argument("--human-state", required=True)
    block.add_argument("--next-action", required=True)
    block.set_defaults(func=cmd_block)

    repair = debug_sub.add_parser("repair", help="Check or apply approved recovery")
    _campaign(repair)
    repair.add_argument("--check", action="store_true")
    repair.add_argument("--apply", action="store_true")
    repair.add_argument("--acknowledge", default=None)
    repair.set_defaults(func=cmd_repair)

    close = debug_sub.add_parser("close", help="Close immutable campaign")
    _campaign(close)
    close.add_argument("--outcome", default="closed")
    close.set_defaults(func=cmd_close)


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--directory", type=Path, default=".")


def _campaign(parser: argparse.ArgumentParser) -> None:
    _common(parser)
    parser.add_argument("--slug", required=True)
