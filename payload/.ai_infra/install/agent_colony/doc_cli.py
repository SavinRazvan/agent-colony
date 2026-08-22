"""
File: doc_cli.py
Path: .ai_infra/install/agent_colony/doc_cli.py
Role: CLI handlers for doc subcommands (canonical doc fact validation + digests).
Used By:
 - .ai_infra/install/agent_colony/cli.py
Depends On:
 - .ai_infra/scripts/architecture/check_doc_facts.py
Notes:
 - Adds scripts/architecture to sys.path for consumer installs.
 - roster-digest / summarize support token-efficient agent Entry.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from markdown_sections import extract_section, list_h2_sections, slugify_heading


def _import_check_doc_facts(root: Path):
    arch_dir = root / ".ai_infra" / "scripts" / "architecture"
    if not arch_dir.is_dir():
        raise FileNotFoundError(f"missing {arch_dir}")
    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import check_doc_facts

    return check_doc_facts


def cmd_doc_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        check_doc_facts = _import_check_doc_facts(root)
    except FileNotFoundError as exc:
        print(f"doc validate: FAIL — {exc}", file=sys.stderr)
        return 1

    preflight = args.preflight_out
    if preflight is None and args.write_preflight:
        preflight = (
            root
            / ".local"
            / "workflow-artifacts"
            / "audit"
            / "doc-facts-preflight.json"
        )

    results = check_doc_facts.run_checks(root)
    if preflight is not None:
        check_doc_facts.write_preflight_json(results, preflight)
    exit_code = check_doc_facts.exit_code_for(results)
    if getattr(args, "summary", False):
        failed = sum(1 for r in results if not r.passed)
        status = "PASS" if exit_code == 0 else "FAIL"
        print(f"doc validate: {status} · checks={len(results)} · fail={failed}")
        return exit_code
    if args.json:
        payload = {
            "results": [
                {
                    "check_id": r.check_id,
                    "severity": r.severity.value,
                    "passed": r.passed,
                    "detail": r.detail,
                }
                for r in results
            ],
            "exit_code": check_doc_facts.exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(check_doc_facts.format_report(results))
    return check_doc_facts.exit_code_for(results)


def cmd_doc_roster_digest(args: argparse.Namespace) -> int:
    """Print agent id + one-line description (token-efficient roster)."""
    root = Path(args.directory).resolve()
    agents_dir = root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        print(f"doc roster-digest: FAIL — missing {agents_dir}", file=sys.stderr)
        return 1
    rows: list[dict[str, str]] = []
    for path in sorted(agents_dir.glob("*.md")):
        agent_id = path.stem
        desc = ""
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
                break
        rows.append({"id": agent_id, "description": desc})
    if args.json:
        print(json.dumps({"agents": rows, "count": len(rows)}, indent=2))
    else:
        print(f"agents={len(rows)}")
        for row in rows:
            short = row["description"]
            if len(short) > 72:
                short = short[:69] + "…"
            print(f"{row['id']}\t{short}")
    return 0


def cmd_doc_summarize(args: argparse.Namespace) -> int:
    """Print first N non-empty lines of a markdown/doc path (token-efficient)."""
    root = Path(args.directory).resolve()
    path = Path(args.path)
    if not path.is_absolute():
        path = (root / path).resolve()
    if not path.is_file():
        print(f"doc summarize: FAIL — missing {path}", file=sys.stderr)
        return 1
    max_lines = int(args.lines)
    lines_out: list[str] = []
    in_comment = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        if not stripped:
            continue
        lines_out.append(line.rstrip())
        if len(lines_out) >= max_lines:
            break
    payload = {
        "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
        "lines": lines_out,
        "truncated": len(lines_out) >= max_lines,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"path={payload['path']} · lines={len(lines_out)}"
              f"{' · truncated' if payload['truncated'] else ''}")
        for line in lines_out:
            print(line)
    return 0


def _find_skill_path(root: Path, skill_id: str) -> Path | None:
    for base in (root / ".cursor" / "skills", root / ".agents" / "skills"):
        candidate = base / skill_id / "SKILL.md"
        if candidate.is_file():
            return candidate
        flat = base / f"{skill_id}.md"
        if flat.is_file():
            return flat
    return None


def _parse_thin_index_rows(root: Path) -> list[dict[str, str]]:
    """Parse skill thin-index table from token-efficiency.md."""
    path = root / ".ai_infra" / "docs" / "operations" / "token-efficiency.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    block = extract_section(text, "Skill thin-index")
    if not block:
        return []
    rows: list[dict[str, str]] = []
    for line in block.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            continue
        skill_cell = parts[1]
        if not skill_cell.startswith("`"):
            continue
        skill_id = skill_cell.strip("`").strip()
        prefer = parts[3] if len(parts) > 3 else ""
        rows.append({"skill": skill_id, "prefer": prefer})
    return rows


def _prefer_sections(prefer: str) -> list[str]:
    """Extract section headings from Prefer column (§ markers or 'Full skill')."""
    if "full skill" in prefer.lower():
        return ["__full__"]
    sections: list[str] = []
    for part in prefer.split("·"):
        part = part.strip()
        if part.startswith("§"):
            part = part[1:].strip()
        if part:
            sections.append(part)
    if not sections and prefer.strip():
        sections.append(prefer.strip())
    return sections or ["When"]


def list_h3_sections(path: Path) -> list[str]:
    """List ``###`` heading titles from a markdown file."""
    if not path.is_file():
        return []
    headings: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            headings.append(line[4:].strip())
    return headings


def _match_section_heading(headings: list[str], hint: str, h3: list[str] | None = None) -> str | None:
    """Map a thin-index Prefer hint to an actual ## heading (fuzzy)."""
    if hint == "__full__":
        return "__full__"
    hint_slug = slugify_heading(hint)
    pool = list(headings)
    if h3:
        pool.extend(h3)
    for h in pool:
        if slugify_heading(h) == hint_slug:
            return h
    for h in pool:
        hs = slugify_heading(h)
        if hint_slug in hs or hs in hint_slug:
            return h
    # Keyword fallbacks from common Prefer phrases
    keywords = {
        "continuation": "Continuation",
        "tier-1": "Tier-1",
        "tier 1": "Tier-1",
        "consent": "CONSENT GATE",
        "turn protocol": "TURN PROTOCOL",
        "evidence contract": "Evidence contract",
        "current phase": "Phase",
        "steps": "Steps",
        "goal": "Goal",
        "when": "When",
        "procedure": "Procedure",
        "commands": "Commands",
        "intake": "Intake",
        "preflight": "Phase 0",
        "constraints": "Constraints",
        "universal contract": "Universal contract",
        "tiers": "Tiers",
        "cli": "CLI",
        "pattern a": "First-time setup",
        "intents": "Intents",
        "version gate": "What update does",
    }
    lower = hint.lower()
    for key, prefix in keywords.items():
        if key in lower:
            for h in pool:
                if prefix.lower() in h.lower():
                    return h
    return None


def _validate_skill_prefer(root: Path, skill_id: str, prefer: str) -> list[str]:
    """Return failure messages for a skill prefer column."""
    skill_path = _find_skill_path(root, skill_id)
    if skill_path is None:
        return [f"{skill_id}: missing on disk"]
    text = skill_path.read_text(encoding="utf-8")
    headings = list_h2_sections(skill_path)
    h3 = list_h3_sections(skill_path)
    failures: list[str] = []
    if "+" in prefer and "§" not in prefer and "full skill" not in prefer.lower():
        hints = [p.strip() for p in prefer.split("+")]
    else:
        hints = _prefer_sections(prefer)
    for hint in hints:
        if hint == "__full__":
            if len(text.strip()) < 80:
                failures.append(f"{skill_id}: full skill too short")
            continue
        matched = _match_section_heading(headings, hint, h3)
        if matched is None:
            failures.append(f"{skill_id}: no heading match for {hint!r}")
            continue
        if matched in h3:
            marker = f"### {matched}"
            if marker not in text:
                failures.append(f"{skill_id}: missing h3 {matched!r}")
            continue
        body = extract_section(text, matched)
        if not body.strip():
            failures.append(f"{skill_id}: empty section {matched!r}")
    return failures


def _load_profile_skill_allowlist(root: Path) -> set[str] | None:
    marker = root / ".local" / "generated-data" / "install-profile.json"
    if not marker.is_file():
        return None
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("profile") != "consumer_lite":
        return None
    manifest = root / ".ai_infra" / "manifest.yaml"
    if not manifest.is_file():
        return None
    import yaml

    spec = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    profile = spec.get("consumer_lite") or {}
    allow = profile.get("skill_allowlist")
    if isinstance(allow, list):
        return {str(x) for x in allow}
    return None


def cmd_doc_skill_section(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    skill_path = _find_skill_path(root, args.skill)
    if skill_path is None:
        print(f"doc skill-section: FAIL — skill not found: {args.skill}", file=sys.stderr)
        return 1
    text = skill_path.read_text(encoding="utf-8")
    body = extract_section(text, args.section)
    if not body and args.section.lower() != "full":
        print(
            f"doc skill-section: FAIL — section not found: {args.section!r} in {skill_path}",
            file=sys.stderr,
        )
        return 1
    if args.section.lower() == "full":
        body = text
    rel = skill_path.relative_to(root) if skill_path.is_relative_to(root) else skill_path
    payload = {
        "skill": args.skill,
        "section": args.section,
        "path": str(rel),
        "bytes": len(body.encode("utf-8")),
        "body": body,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"skill={args.skill} · section={args.section} · bytes={payload['bytes']}")
        print(body)
    return 0


def cmd_doc_validate_thin_index(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    allowlist = _load_profile_skill_allowlist(root)
    rows = _parse_thin_index_rows(root)
    if not rows:
        print("doc validate-thin-index: FAIL — no thin-index rows", file=sys.stderr)
        return 1
    failures: list[str] = []
    skipped = 0
    checked = 0
    for row in rows:
        skill_id = row["skill"]
        if allowlist is not None and skill_id not in allowlist:
            skipped += 1
            continue
        skill_path = _find_skill_path(root, skill_id)
        if skill_path is None:
            if allowlist is not None:
                skipped += 1
                continue
            failures.append(f"{skill_id}: missing on disk")
            continue
        row_failures = _validate_skill_prefer(root, skill_id, row["prefer"])
        failures.extend(row_failures)
        checked += max(1, len(_prefer_sections(row["prefer"])))
    if args.summary:
        status = "PASS" if not failures else "FAIL"
        print(
            f"validate-thin-index: {status} · checked={checked} · skipped={skipped} · fail={len(failures)}"
        )
    elif args.json:
        print(
            json.dumps(
                {
                    "passed": not failures,
                    "checked": checked,
                    "skipped": skipped,
                    "failures": failures,
                },
                indent=2,
            )
        )
    else:
        for msg in failures:
            print(f"FAIL: {msg}")
        print(f"summary: checked={checked} skipped={skipped} fail={len(failures)}")
    return 1 if failures else 0


def register_doc_subparser(sub: argparse._SubParsersAction) -> None:
    doc = sub.add_parser("doc", help="Canonical documentation fact checks")
    doc_sub = doc.add_subparsers(dest="doc_command", required=True)

    validate_cmd = doc_sub.add_parser(
        "validate",
        help="Validate README/AGENTS/status docs against repo facts",
    )
    validate_cmd.add_argument("--directory", type=Path, default=".")
    validate_cmd.add_argument("--json", action="store_true", help="Emit JSON report")
    validate_cmd.add_argument(
        "--write-preflight",
        action="store_true",
        help="Write .local/workflow-artifacts/audit/doc-facts-preflight.json",
    )
    validate_cmd.add_argument(
        "--preflight-out",
        type=Path,
        default=None,
        help="Custom preflight JSON path",
    )
    validate_cmd.add_argument(
        "--summary",
        action="store_true",
        help="One-line PASS/FAIL summary",
    )
    validate_cmd.set_defaults(func=cmd_doc_validate)

    roster_cmd = doc_sub.add_parser(
        "roster-digest",
        help="Token-efficient agent roster (id + description)",
    )
    roster_cmd.add_argument("--directory", type=Path, default=".")
    roster_cmd.add_argument("--json", action="store_true")
    roster_cmd.set_defaults(func=cmd_doc_roster_digest)

    summarize_cmd = doc_sub.add_parser(
        "summarize",
        help="First N non-empty lines of a doc (token-efficient)",
    )
    summarize_cmd.add_argument("--directory", type=Path, default=".")
    summarize_cmd.add_argument("--path", required=True, help="Repo-relative or absolute path")
    summarize_cmd.add_argument("--lines", type=int, default=40, help="Max non-empty lines")
    summarize_cmd.add_argument("--json", action="store_true")
    summarize_cmd.set_defaults(func=cmd_doc_summarize)

    skill_section_cmd = doc_sub.add_parser(
        "skill-section",
        help="Extract one ## section from a skill SKILL.md",
    )
    skill_section_cmd.add_argument("--directory", type=Path, default=".")
    skill_section_cmd.add_argument("--skill", required=True, help="Skill folder id")
    skill_section_cmd.add_argument("--section", required=True, help="## heading title")
    skill_section_cmd.add_argument("--json", action="store_true")
    skill_section_cmd.set_defaults(func=cmd_doc_skill_section)

    thin_cmd = doc_sub.add_parser(
        "validate-thin-index",
        help="Validate token-efficiency thin-index rows against on-disk skills",
    )
    thin_cmd.add_argument("--directory", type=Path, default=".")
    thin_cmd.add_argument("--json", action="store_true")
    thin_cmd.add_argument("--summary", action="store_true")
    thin_cmd.set_defaults(func=cmd_doc_validate_thin_index)
