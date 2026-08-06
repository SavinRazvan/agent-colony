"""
File: doc_facts_checks.py
Path: .ai_infra/scripts/architecture/doc_facts_checks.py
Role: Individual DOC-001…008 checks for canonical doc vs repo fact parity.
Used By:
 - .ai_infra/scripts/architecture/check_doc_facts.py
Depends On:
 - ast, re, pathlib (stdlib)
Notes:
 - Does not duplicate DRIFT-005 test counts in prose; DOC-006 mirrors that parity in the doc-validate path.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass
class CheckResult:
    check_id: str
    severity: Severity
    passed: bool
    detail: str


@dataclass
class DocFactsPaths:
    root: Path
    agents_dir: Path
    rules_dir: Path
    exemplars_dir: Path
    prepare_py: Path
    readme: Path
    agents_md: Path
    workflow_architecture: Path
    implementation_status: Path
    gate_matrix: Path


def doc_facts_paths(root: Path) -> DocFactsPaths:
    docs = root / ".ai_infra" / "docs"
    return DocFactsPaths(
        root=root,
        agents_dir=root / ".cursor" / "agents",
        rules_dir=root / ".cursor" / "rules",
        exemplars_dir=root / ".ai_infra" / "templates" / "local-workspace" / "exemplars",
        prepare_py=root / ".ai_infra" / "scripts" / "pr" / "prepare.py",
        readme=root / "README.md",
        agents_md=root / "AGENTS.md",
        workflow_architecture=docs / "architecture" / "workflow-architecture.md",
        implementation_status=docs / "handoff" / "IMPLEMENTATION-STATUS.md",
        gate_matrix=docs / "operations" / "gate-matrix.md",
    )


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def is_kit_dev(root: Path) -> bool:
    """Doc-facts apply only on the kit dev repo (consumer stub lacks handoff docs)."""
    return (root / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md").is_file()


def list_agent_ids(paths: DocFactsPaths) -> list[str]:
    if not paths.agents_dir.is_dir():
        return []
    return sorted(p.stem for p in paths.agents_dir.glob("*.md"))


def list_rule_count(paths: DocFactsPaths) -> int:
    if not paths.rules_dir.is_dir():
        return 0
    return len(list(paths.rules_dir.glob("*.mdc")))


def _ast_gate_list_length(text: str, assign_name: str) -> int | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == assign_name:
                try:
                    gates = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    return None
                return len(gates) if isinstance(gates, list) else None
    return None


def _load_prepare_gate_count(paths: DocFactsPaths) -> int | None:
    if not paths.prepare_py.is_file():
        return None
    text = _read(paths.prepare_py)
    universal = _ast_gate_list_length(text, "GATES_UNIVERSAL")
    if universal is None:
        universal = _ast_gate_list_length(text, "GATES")
    if universal is None:
        return None
    total = universal
    if is_kit_dev(paths.root):
        kit_append = _ast_gate_list_length(text, "GATES_KIT_DEV_APPEND") or 0
        total += kit_append
    return total


def _parse_status_agent_count(text: str) -> int | None:
    match = re.search(r"\|\s*Agents\s*\|\s*(\d+)\s*core", text)
    return int(match.group(1)) if match else None


def _parse_status_rules_count(text: str) -> int | None:
    match = re.search(r"\|\s*Universal rules\s*\|\s*(\d+)", text)
    return int(match.group(1)) if match else None


def _agent_in_text(agent_id: str, text: str) -> bool:
    return agent_id in text or f"`{agent_id}`" in text


def check_doc001_agent_roster(paths: DocFactsPaths) -> CheckResult:
    agents = list_agent_ids(paths)
    if not agents:
        return CheckResult(
            check_id="DOC-001",
            severity=Severity.P0,
            passed=False,
            detail="missing .cursor/agents/*.md",
        )
    doc_targets = [
        ("README.md", paths.readme),
        ("AGENTS.md", paths.agents_md),
        (
            ".ai_infra/docs/architecture/workflow-architecture.md",
            paths.workflow_architecture,
        ),
    ]
    missing: list[str] = []
    for label, path in doc_targets:
        text = _read(path)
        if not text:
            missing.append(f"{label}: file missing")
            continue
        for agent_id in agents:
            if not _agent_in_text(agent_id, text):
                missing.append(f"{label}: missing {agent_id}")
    passed = not missing
    detail = "agent roster present in canonical docs" if passed else "; ".join(missing[:8])
    if not passed and len(missing) > 8:
        detail += f"; +{len(missing) - 8} more"
    return CheckResult(
        check_id="DOC-001",
        severity=Severity.P1,
        passed=passed,
        detail=detail,
    )


def check_doc002_status_agent_count(paths: DocFactsPaths) -> CheckResult:
    agents = list_agent_ids(paths)
    text = _read(paths.implementation_status)
    doc_count = _parse_status_agent_count(text)
    if doc_count is None:
        return CheckResult(
            check_id="DOC-002",
            severity=Severity.P1,
            passed=False,
            detail="IMPLEMENTATION-STATUS missing Agents | N core row",
        )
    actual = len(agents)
    passed = doc_count == actual
    return CheckResult(
        check_id="DOC-002",
        severity=Severity.P1,
        passed=passed,
        detail=(
            f"agent count matches ({actual})"
            if passed
            else f"doc={doc_count} agents_dir={actual}"
        ),
    )


def check_doc003_kit_exemplar_tokens(paths: DocFactsPaths) -> CheckResult:
    if not paths.exemplars_dir.is_dir():
        return CheckResult(
            check_id="DOC-003",
            severity=Severity.P2,
            passed=True,
            detail="exemplars dir missing — skipped",
        )
    hits: list[str] = []
    for path in sorted(paths.exemplars_dir.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml"}:
            continue
        if "STARTER-001" in _read(path):
            hits.append(path.relative_to(paths.root).as_posix())
    passed = not hits
    return CheckResult(
        check_id="DOC-003",
        severity=Severity.P0,
        passed=passed,
        detail=(
            "kit exemplars free of STARTER-001"
            if passed
            else f"STARTER-001 in {', '.join(hits)}"
        ),
    )


def check_doc004_rules_count(paths: DocFactsPaths) -> CheckResult:
    actual = list_rule_count(paths)
    if actual == 0:
        return CheckResult(
            check_id="DOC-004",
            severity=Severity.P1,
            passed=False,
            detail="missing .cursor/rules/*.mdc",
        )
    status_count = _parse_status_rules_count(_read(paths.implementation_status))
    readme_text = _read(paths.readme)
    readme_ok = re.search(rf"\b{actual}\s+universal\b", readme_text, re.IGNORECASE) is not None
    status_ok = status_count == actual if status_count is not None else False
    passed = readme_ok and status_ok
    parts: list[str] = []
    if not readme_ok:
        parts.append(f"README missing '{actual} universal'")
    if status_count is None:
        parts.append("IMPLEMENTATION-STATUS missing Universal rules row")
    elif not status_ok:
        parts.append(f"IMPLEMENTATION-STATUS doc={status_count} actual={actual}")
    return CheckResult(
        check_id="DOC-004",
        severity=Severity.P1,
        passed=passed,
        detail="rules count aligned" if passed else "; ".join(parts),
    )


def check_doc005_prepare_gate_facts(paths: DocFactsPaths) -> CheckResult:
    gate_count = _load_prepare_gate_count(paths)
    if gate_count is None:
        return CheckResult(
            check_id="DOC-005",
            severity=Severity.P2,
            passed=False,
            detail="unable to parse GATES from prepare.py",
        )
    agents_text = _read(paths.agents_md)
    gate_matrix = _read(paths.gate_matrix)
    agents_ok = (
        "**two**" in agents_text.lower()
        or f"**{gate_count}**" in agents_text
        or "kit-dev" in agents_text.lower()
    )
    matrix_ok = (
        f"{gate_count}:" in gate_matrix
        or f"| **{gate_count}**" in gate_matrix
        or f"**{gate_count}**" in gate_matrix
    )
    passed = agents_ok and matrix_ok
    parts: list[str] = []
    if not agents_ok:
        parts.append(f"AGENTS.md missing gate count hint for {gate_count}")
    if not matrix_ok:
        parts.append(f"gate-matrix.md missing prepare gate count {gate_count}")
    return CheckResult(
        check_id="DOC-005",
        severity=Severity.P2,
        passed=passed,
        detail="prepare gate count documented" if passed else "; ".join(parts),
    )


def _parse_implementation_test_count(text: str) -> int | None:
    match = re.search(r"\*\*Tests:\*\*\s*(\d+)", text)
    return int(match.group(1)) if match else None


def _collect_pytest_count(root: Path) -> int:
    from paths import resolve_project_python

    proc = subprocess.run(
        [resolve_project_python(root), "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = proc.stdout + proc.stderr
    match = re.search(r"(\d+)\s+tests?\s+collected", combined)
    return int(match.group(1)) if match else -1


def check_doc006_implementation_test_count(paths: DocFactsPaths) -> CheckResult:
    """IMPLEMENTATION-STATUS **Tests:** must match pytest --collect-only (same as DRIFT-005)."""
    status_text = _read(paths.implementation_status)
    doc_count = _parse_implementation_test_count(status_text)
    if doc_count is None:
        return CheckResult(
            check_id="DOC-006",
            severity=Severity.P1,
            passed=False,
            detail="IMPLEMENTATION-STATUS missing **Tests:** count",
        )
    actual = _collect_pytest_count(paths.root)
    if actual < 0:
        return CheckResult(
            check_id="DOC-006",
            severity=Severity.P1,
            passed=False,
            detail="pytest --collect-only failed",
        )
    passed = doc_count == actual
    return CheckResult(
        check_id="DOC-006",
        severity=Severity.P1,
        passed=passed,
        detail=(
            f"test count matches ({actual})"
            if passed
            else f"doc={doc_count} pytest={actual}"
        ),
    )


def check_doc007_agent_board_rights(paths: DocFactsPaths) -> CheckResult:
    """Every agent Anchor Board rights must mention promote-to-issue and mention-pr."""
    agents_dir = paths.agents_dir
    if not agents_dir.is_dir():
        return CheckResult(
            check_id="DOC-007",
            severity=Severity.P1,
            passed=False,
            detail="missing .cursor/agents/",
        )
    missing: list[str] = []
    for path in sorted(agents_dir.glob("*.md")):
        text = _read(path)
        agent_id = path.stem
        if "**Board rights:**" not in text:
            missing.append(f"{agent_id}: missing Board rights")
            continue
        # Scope to Board rights paragraph (until next blank line after the marker)
        start = text.index("**Board rights:**")
        rest = text[start:]
        para = rest.split("\n\n", 1)[0]
        for needle in ("promote-to-issue", "mention-pr"):
            if needle not in para:
                missing.append(f"{agent_id}: Board rights missing {needle}")
    passed = not missing
    return CheckResult(
        check_id="DOC-007",
        severity=Severity.P1,
        passed=passed,
        detail=(
            "all agents Board rights include promote-to-issue + mention-pr"
            if passed
            else "; ".join(missing[:8])
        ),
    )


CANVAS_ROSTER_FILES = (
    "agent-relations.canvas.tsx",
    "agent-roster.canvas.tsx",
    "agent-board-collaboration.canvas.tsx",
)

CANVAS_ROSTER_HUBS = (
    "agent-relations.canvas.tsx",
    "agent-roster.canvas.tsx",
)

# Flow/UI tokens in canvases — not agent ids (DOC-008 allowlist).
_CANVAS_NON_AGENT_TOKENS = frozenset(
    {
        "all",
        "agent",
        "a",
        "b",
        "c",
        "back",
        "board",
        "bottom",
        "claim",
        "cli",
        "close",
        "code",
        "corpus",
        "create",
        "doc-drift",
        "done",
        "export",
        "fix-notes",
        "gates",
        "handoff",
        "index",
        "left",
        "list",
        "main",
        "merge",
        "next",
        "notes",
        "plan",
        "pr",
        "primary",
        "right",
        "session",
        "side",
        "skill",
        "snapshot",
        "status",
        "tests",
        "top",
        "tracker",
        "trackers",
        "close",
        "triage",
        "validate",
        "verdict",
        "yaml",
        "audit",
        "artifacts",
        "boundaries",
        "brief",
        "bootstrap",
        "checks",
        "coverage",
        "evidence",
        "intake",
        "promote",
        "restate",
        "rounds",
        "todo",
        "todos",
        "card",
        "wire",
        "verify",
        "pr-workflow",
        "entry",
        "offline",
        "compare",
    }
)


def _canvas_paths(root: Path) -> list[Path]:
    canvases = root / "canvases"
    if not canvases.is_dir():
        return []
    paths: list[Path] = []
    for name in CANVAS_ROSTER_FILES:
        path = canvases / name
        if path.is_file():
            paths.append(path)
    paths.extend(sorted(canvases.glob("agent-*.canvas.tsx")))
    # Dedupe while preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = path.as_posix()
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _parse_agents_array_ids(text: str) -> set[str]:
    """Extract `id: \"agent-id\"` entries from AGENTS / AgentId roster blocks."""
    ids: set[str] = set()
    for match in re.finditer(r'\bid:\s*"([a-z][a-z0-9-]*)"', text):
        ids.add(match.group(1))
    return ids


def _canvas_agent_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for match in re.finditer(
        r'(?:from|to|value|label):\s*"([a-z][a-z0-9-]*)"', text
    ):
        refs.add(match.group(1))
    for match in re.finditer(
        r'\|\s*"([a-z][a-z0-9-]+)"\s*\|', text
    ):
        refs.add(match.group(1))
    return refs


def check_doc008_canvas_roster(paths: DocFactsPaths) -> CheckResult:
    """Canvas agent ids must match .cursor/agents roster; hub canvases list all live agents."""
    live = set(list_agent_ids(paths))
    if not live:
        return CheckResult(
            check_id="DOC-008",
            severity=Severity.P2,
            passed=False,
            detail="missing .cursor/agents/*.md",
        )
    canvas_paths = _canvas_paths(paths.root)
    if not canvas_paths:
        return CheckResult(
            check_id="DOC-008",
            severity=Severity.P2,
            passed=False,
            detail="missing canvases/agent-*.canvas.tsx",
        )

    unknown: list[str] = []
    missing_roster: list[str] = []
    for path in canvas_paths:
        rel = path.relative_to(paths.root).as_posix()
        text = _read(path)
        for ref in sorted(_canvas_agent_refs(text)):
            if ref in _CANVAS_NON_AGENT_TOKENS or ref in live:
                continue
            unknown.append(f"{rel}: unknown agent {ref}")

    for hub_name in CANVAS_ROSTER_HUBS:
        hub = paths.root / "canvases" / hub_name
        if not hub.is_file():
            missing_roster.append(f"{hub_name}: file missing")
            continue
        listed = _parse_agents_array_ids(_read(hub))
        for agent_id in sorted(live):
            if agent_id not in listed:
                missing_roster.append(f"{hub_name}: missing {agent_id}")

    passed = not unknown and not missing_roster
    if passed:
        detail = f"canvas roster aligned ({len(live)} agents, {len(canvas_paths)} canvases)"
    else:
        parts = unknown[:4] + missing_roster[:4]
        detail = "; ".join(parts)
        if len(unknown) + len(missing_roster) > 4:
            detail += f"; +{len(unknown) + len(missing_roster) - 4} more"
    return CheckResult(
        check_id="DOC-008",
        severity=Severity.P2,
        passed=passed,
        detail=detail,
    )


KIT_DEV_CHECKS = (
    check_doc001_agent_roster,
    check_doc002_status_agent_count,
    check_doc003_kit_exemplar_tokens,
    check_doc004_rules_count,
    check_doc005_prepare_gate_facts,
    check_doc006_implementation_test_count,
    check_doc007_agent_board_rights,
    check_doc008_canvas_roster,
)
