"""
File: check_governance_consistency.py
Path: .ai_infra/scripts/architecture/check_governance_consistency.py
Role: Detect governance drift across active rules, skills, merge checks, and CI wiring.
Used By:
 - .github/workflows/kit-quality.yml
Depends On:
 - pathlib
Notes:
 - Fails fast on stale references to removed governance research documents.
 - Enforces parity checks for merge prechecks and canonical skill ownership shims.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ROOT = ensure_paths_import(__file__)
        break
else:
    raise RuntimeError("kit root not found above check_governance_consistency.py")

from paths import kit_root_from_script

ROOT = kit_root_from_script(__file__)
BANNED_REFERENCE = ".cursor/research-for-refactor/"

GOVERNANCE_SCAN_TARGETS = (
    ".ai_infra/scripts/pr/merge.py",
    ".github/workflows/kit-quality.yml",
)

PATH_DRIFT_SURFACES = (
    ROOT / ".cursor" / "agents",
    ROOT / ".cursor" / "rules",
    ROOT / ".cursor" / "skills",
    ROOT / ".agents" / "skills",
)

PATH_DRIFT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("bare scripts/pr/", re.compile(r"(?<!.ai_infra/)scripts/pr/")),
    ("bare scripts/architecture/", re.compile(r"(?<!.ai_infra/)scripts/architecture/")),
)

BANNED_BRAND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("eXo-brain", re.compile(r"eXo-brain", re.IGNORECASE)),
    ("exo-brain", re.compile(r"exo-brain", re.IGNORECASE)),
    ("eXo_brain", re.compile(r"eXo_brain", re.IGNORECASE)),
    ("mcp-starter-kit", re.compile(r"mcp-starter-kit", re.IGNORECASE)),
    ("Cursor Workflow Starter Kit", re.compile(r"Cursor Workflow Starter Kit", re.IGNORECASE)),
    ("with_exo_pack", re.compile(r"with_exo_pack")),
    ("overlay-exo", re.compile(r"overlay-exo")),
    ("pack_exo_brain", re.compile(r"pack_exo_brain")),
    ("examples/eXo-brain-pack", re.compile(r"examples/eXo-brain-pack", re.IGNORECASE)),
    ("mas-workflow-kit-project-ssot", re.compile(r"mas-workflow-kit-project-ssot", re.IGNORECASE)),
    (
        "MAS Workflow Kit — Project SSOT",
        re.compile(r"MAS Workflow Kit — Project SSOT", re.IGNORECASE),
    ),
    ("MAS Workflow Kit", re.compile(r"MAS Workflow Kit", re.IGNORECASE)),
    ("mas-workflow-kit", re.compile(r"mas-workflow-kit", re.IGNORECASE)),
    ("workflow-kit", re.compile(r"workflow-kit", re.IGNORECASE)),
    ("MAS-SSOT-KIT", re.compile(r"MAS-SSOT-KIT", re.IGNORECASE)),
    ("Formerly", re.compile(r"Formerly", re.IGNORECASE)),
    ("upstream", re.compile(r"upstream", re.IGNORECASE)),
)

BRAND_DRIFT_SURFACES = (
    ROOT / ".cursor",
    ROOT / ".agents",
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / ".ai_infra" / "docs",
    ROOT / "tests",
    ROOT / "agent_colony",
)

BRAND_DRIFT_SKIP = frozenset(
    {
        ".ai_infra/scripts/architecture/check_debrand.py",
        ".ai_infra/scripts/architecture/check_governance_consistency.py",
        "tests/modules/architecture_scripts/test_check_debrand.py",
    }
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"unable to read {path}: {exc}") from exc


def _collect_banned_reference_violations() -> list[str]:
    violations: list[str] = []
    for target in GOVERNANCE_SCAN_TARGETS:
        if _is_gitignored(target):
            continue
        absolute = ROOT / target
        if absolute.is_file():
            text = _read_text(absolute)
            if BANNED_REFERENCE in text:
                rel = absolute.relative_to(ROOT).as_posix()
                violations.append(f"{rel}: contains stale reference '{BANNED_REFERENCE}'")
            continue

        if absolute.is_dir():
            for path in absolute.rglob("*"):
                if not path.is_file():
                    continue
                text = _read_text(path)
                if BANNED_REFERENCE in text:
                    rel = path.relative_to(ROOT).as_posix()
                    violations.append(f"{rel}: contains stale reference '{BANNED_REFERENCE}'")
            continue

        # Optional governance targets may be absent by repo policy.
        continue
    return violations


def _contains_required(path: str, required_fragments: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    if _is_gitignored(path):
        return violations
    absolute = ROOT / path
    if not absolute.exists():
        return [f"{path}: required file is missing"]
    text = _read_text(absolute)
    for fragment in required_fragments:
        if fragment not in text:
            violations.append(f"{path}: missing required fragment '{fragment}'")
    return violations


def _collect_contract_parity_violations() -> list[str]:
    violations: list[str] = []
    violations.extend(
        _contains_required(
            ".ai_infra/scripts/pr/merge.py",
            (
                ".local/workflow-artifacts/alignment/alignment-audit.md",
                ".local/workflow-artifacts/alignment/alignment-todos.md",
            ),
        )
    )
    ci_workflow = ROOT / ".github/workflows/kit-quality.yml"
    if ci_workflow.is_file():
        violations.extend(
            _contains_required(
                ".github/workflows/kit-quality.yml",
                (".ai_infra/scripts/architecture/check_governance_consistency.py",),
            )
        )
    return violations


def _is_gitignored(path: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def _collect_path_drift_violations() -> list[str]:
    violations: list[str] = []
    for surface in PATH_DRIFT_SURFACES:
        if not surface.is_dir():
            continue
        for path in surface.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".md", ".mdc"}:
                continue
            text = _read_text(path)
            rel = path.relative_to(ROOT).as_posix()
            for label, pattern in PATH_DRIFT_PATTERNS:
                if pattern.search(text):
                    violations.append(f"{rel}: contains stale reference ({label})")
    return violations


def _collect_brand_drift_violations() -> list[str]:
    arch = ROOT / ".ai_infra" / "scripts" / "architecture"
    arch_str = str(arch)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    from check_debrand import text_has_banned_pattern

    violations: list[str] = []
    for surface in BRAND_DRIFT_SURFACES:
        if surface.is_file():
            paths = [surface]
        elif surface.is_dir():
            paths = [p for p in surface.rglob("*") if p.is_file()]
        else:
            continue
        for path in paths:
            if path.suffix not in {".md", ".mdc", ".py", ".yaml", ".yml"} and path not in {
                ROOT / "AGENTS.md",
                ROOT / "README.md",
            }:
                continue
            text = _read_text(path)
            rel = path.relative_to(ROOT).as_posix()
            if rel in BRAND_DRIFT_SKIP:
                continue
            for label, pattern in BANNED_BRAND_PATTERNS:
                if label == "upstream" and path.suffix == ".py":
                    continue
                if text_has_banned_pattern(text, pattern):
                    violations.append(f"{rel}: banned brand term ({label})")
    return violations


def _collect_agent_description_violations() -> list[str]:
    violations: list[str] = []
    agents_dir = ROOT / ".cursor" / "agents"
    if not agents_dir.is_dir():
        return violations
    for path in sorted(agents_dir.glob("*.md")):
        text = _read_text(path)
        rel = path.relative_to(ROOT).as_posix()
        if not re.search(r"^description:\s*.+", text, re.MULTILINE):
            violations.append(f"{rel}: missing YAML frontmatter description")
    return violations


def _collect_duplicate_skill_folder_violations() -> list[str]:
    cursor_skills = ROOT / ".cursor" / "skills"
    agents_skills = ROOT / ".agents" / "skills"
    if not cursor_skills.is_dir() or not agents_skills.is_dir():
        return []
    cursor_names = {p.name for p in cursor_skills.iterdir() if p.is_dir()}
    agents_names = {p.name for p in agents_skills.iterdir() if p.is_dir()}
    overlap = sorted(cursor_names & agents_names)
    if overlap:
        return [
            "duplicate skill folder names between .cursor/skills and .agents/skills: "
            + ", ".join(overlap)
        ]
    return []


def _collect_agent_mcp_block_violations() -> list[str]:
    violations: list[str] = []
    agents_dir = ROOT / ".cursor" / "agents"
    if not agents_dir.is_dir():
        return violations
    for path in sorted(agents_dir.glob("*.md")):
        text = _read_text(path)
        rel = path.relative_to(ROOT).as_posix()
        if "## MCP integration" not in text:
            violations.append(f"{rel}: missing '## MCP integration' section")
        if "CallMcpTool" in text and "mcp.registry.yaml" not in text:
            violations.append(f"{rel}: references CallMcpTool without registry path")
    return violations


KIT_DEV_ONLY_PREFIXES = (
    ".ai_infra/scripts/ci/",
    ".ai_infra/scripts/release/",
)


def _is_kit_dev_only_path(candidate: str) -> bool:
    return any(candidate.startswith(prefix) for prefix in KIT_DEV_ONLY_PREFIXES)


def _is_consumer_excluded_path(candidate: str) -> bool:
    arch = ROOT / ".ai_infra" / "scripts" / "architecture"
    arch_str = str(arch)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    from consumer_bundle_paths import CONSUMER_EXCLUDED_REL_PATHS

    return candidate in CONSUMER_EXCLUDED_REL_PATHS


def _collect_owner_path_violations() -> list[str]:
    owners = ROOT / ".ai_infra/docs/governance/workflow-source-owners.md"
    if not owners.is_file():
        return [".ai_infra/docs/governance/workflow-source-owners.md: missing"]
    text = _read_text(owners)
    violations: list[str] = []
    for match in re.finditer(r"`(\.ai_infra/[^`]+)`", text):
        candidate = match.group(1)
        if candidate.endswith("/"):
            path = ROOT / candidate.rstrip("/")
            if not path.is_dir():
                violations.append(f"workflow-source-owners.md: missing directory {candidate}")
        elif "*" in candidate or "(" in candidate:
            continue
        else:
            path = ROOT / candidate
            if not path.exists():
                if _is_kit_dev_only_path(candidate):
                    continue
                if _is_consumer_excluded_path(candidate):
                    continue
                violations.append(f"workflow-source-owners.md: missing path {candidate}")
    return violations


def _collect_file_header_violations() -> list[str]:
    arch_dir = ROOT / ".ai_infra" / "scripts" / "architecture"
    if not arch_dir.is_dir():
        return [".ai_infra/scripts/architecture: missing"]
    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    from check_file_headers import collect_file_header_violations

    return [f"file header: {v}" for v in collect_file_header_violations(ROOT)]


def _collect_integration_validate_violations() -> list[str]:
    integration_dir = ROOT / ".ai_infra" / "scripts" / "integration"
    if not integration_dir.is_dir():
        return [".ai_infra/scripts/integration: missing integration validate module"]
    integration_str = str(integration_dir)
    if integration_str not in sys.path:
        sys.path.insert(0, integration_str)
    import validate

    violations: list[str] = []
    for result in validate.run_checks(ROOT):
        if not result.passed and result.severity.value == "P0":
            violations.append(f"integrate {result.check_id}: {result.detail}")
    return violations


def main() -> int:
    violations = _collect_banned_reference_violations()
    violations.extend(_collect_contract_parity_violations())
    violations.extend(_collect_path_drift_violations())
    violations.extend(_collect_brand_drift_violations())
    violations.extend(_collect_agent_description_violations())
    violations.extend(_collect_duplicate_skill_folder_violations())
    violations.extend(_collect_agent_mcp_block_violations())
    violations.extend(_collect_owner_path_violations())
    violations.extend(_collect_file_header_violations())
    violations.extend(_collect_integration_validate_violations())
    if violations:
        print("Governance consistency check failed:")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("Governance consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
