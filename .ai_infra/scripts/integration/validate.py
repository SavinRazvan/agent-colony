"""
File: validate.py
Path: .ai_infra/scripts/integration/validate.py
Role: Machine-enforced MAS infrastructure integration checks (integrate validate).
Used By:
 - cursor_workflow integrate validate
 - scripts/architecture/check_governance_consistency.py
 - workflow_mcp workflow_integrate_validate
Depends On:
 - .ai_infra/scripts/integration/checks.py
 - .ai_infra/scripts/pr/user_settings.py
Notes:
 - Exit code 1 when any P0 check fails; P1/P2 are advisory in output only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ensure_paths_import(__file__)
        break

from paths import ai_infra_dir

from checks import (
    check_all_agent_files,
    check_pipeline_agent_ids,
    check_registry_parity,
    pipeline_names_from_exemplar,
)


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


def _import_user_settings(root: Path):
    pr_dir = ai_infra_dir(root) / "scripts" / "pr"
    pr_str = str(pr_dir)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import user_settings

    return user_settings


def _paths(root: Path) -> dict[str, Path]:
    infra = ai_infra_dir(root)
    return {
        "github_exemplar": infra / "templates" / "user-settings" / "exemplars" / "github.collaboration.yaml",
        "registry_example": root / ".cursor" / "mcp.registry.yaml.example",
        "agents_dir": root / ".cursor" / "agents",
        "manifest": infra / "manifest.yaml",
        "ops_doc": infra / "docs" / "operations" / "mas-infrastructure-integration.md",
        "checklist": infra / "templates" / "agent-integration" / "INTEGRATION-CHECKLIST.md",
        "plugin_integrator": root / "plugin" / "agents" / "integrator-mas-agent.md",
        "plugin_drift_guard": root / "plugin" / "agents" / "workflow-drift-guard.md",
    }


def _check_int001(paths: dict[str, Path]) -> CheckResult:
    violations = check_all_agent_files(paths["agents_dir"])
    return CheckResult(
        check_id="INT-001",
        severity=Severity.P0,
        passed=not violations,
        detail="; ".join(violations) if violations else "all agents have Anchor + MCP integration markers",
    )


def _check_registry_file(paths: dict[str, Path]) -> CheckResult:
    violations = check_registry_parity(
        agents_dir=paths["agents_dir"],
        registry_path=paths["registry_example"],
    )
    return CheckResult(
        check_id="INT-002",
        severity=Severity.P0,
        passed=not violations,
        detail="; ".join(violations) if violations else "registry agent ids resolve to agent files",
    )


def _check_int004(us_module: Any, paths: dict[str, Path]) -> CheckResult:
    exemplar_names = pipeline_names_from_exemplar(paths["github_exemplar"])
    code_names = set(us_module.PIPELINE_NAMES)
    missing_in_exemplar = sorted(code_names - exemplar_names)
    missing_in_code = sorted(exemplar_names - code_names)
    violations: list[str] = []
    if missing_in_exemplar:
        violations.append(f"PIPELINE_NAMES not in exemplar: {missing_in_exemplar}")
    if missing_in_code:
        violations.append(f"exemplar pipelines not in PIPELINE_NAMES: {missing_in_code}")
    return CheckResult(
        check_id="INT-004",
        severity=Severity.P0,
        passed=not violations,
        detail="; ".join(violations) if violations else "PIPELINE_NAMES matches exemplar pipelines",
    )


def _check_int005(us_module: Any, root: Path, paths: dict[str, Path]) -> CheckResult:
    cfg = us_module.load_github_collaboration(root)
    if not cfg:
        return CheckResult(
            check_id="INT-005",
            severity=Severity.P1,
            passed=True,
            detail="skipped — no local github.collaboration.yaml",
        )
    violations = check_pipeline_agent_ids(cfg=cfg, agents_dir=paths["agents_dir"])
    return CheckResult(
        check_id="INT-005",
        severity=Severity.P1,
        passed=not violations,
        detail="; ".join(violations) if violations else "pipeline agent ids resolve",
    )


def _check_int006(us_module: Any, root: Path) -> CheckResult:
    path = us_module.github_collaboration_path(root)
    if not path.is_file():
        return CheckResult(
            check_id="INT-006",
            severity=Severity.P0,
            passed=True,
            detail="skipped — no local github.collaboration.yaml",
        )
    errors = us_module.validate_github_collaboration_schema(root)
    return CheckResult(
        check_id="INT-006",
        severity=Severity.P0,
        passed=not errors,
        detail="; ".join(errors) if errors else "local github.collaboration.yaml passes schema",
    )


def _check_int007(us_module: Any, root: Path) -> CheckResult:
    path = us_module.mcp_agents_path(root)
    if not path.is_file():
        return CheckResult(
            check_id="INT-007",
            severity=Severity.P1,
            passed=True,
            detail="skipped — no local mcp.agents.yaml",
        )
    errors = us_module.validate_mcp_agents_schema(root)
    return CheckResult(
        check_id="INT-007",
        severity=Severity.P1,
        passed=not errors,
        detail="; ".join(errors) if errors else "local mcp.agents.yaml passes schema",
    )


def _check_int008(paths: dict[str, Path]) -> CheckResult:
    violations: list[str] = []
    manifest_path = paths["manifest"]
    if not manifest_path.is_file():
        violations.append("missing manifest.yaml")
    else:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        profile = (data or {}).get("profiles", {}).get("default", {})
        copy_ai = profile.get("copy_ai_infra") or []
        copy_dirs = profile.get("copy_dirs") or []
        if "templates/agent-integration" not in copy_ai:
            violations.append("manifest missing templates/agent-integration in copy_ai_infra")
        has_cursor = any(
            isinstance(entry, dict) and entry.get("src") == ".cursor"
            for entry in copy_dirs
        )
        if not has_cursor:
            violations.append("manifest missing .cursor in copy_dirs")
    return CheckResult(
        check_id="INT-008",
        severity=Severity.P1,
        passed=not violations,
        detail="; ".join(violations) if violations else "manifest includes agent-integration + .cursor",
    )


def _check_int009(paths: dict[str, Path]) -> CheckResult:
    exists = paths["plugin_integrator"].is_file()
    return CheckResult(
        check_id="INT-009",
        severity=Severity.P2,
        passed=exists,
        detail=(
            "plugin/agents/integrator-mas-agent.md present"
            if exists
            else "missing plugin/agents/integrator-mas-agent.md — run make sync-plugin"
        ),
    )


def _check_int010(paths: dict[str, Path]) -> CheckResult:
    ops_doc = paths["ops_doc"]
    checklist = paths["checklist"]
    if not ops_doc.is_file():
        return CheckResult(
            check_id="INT-010",
            severity=Severity.P2,
            passed=False,
            detail="missing mas-infrastructure-integration.md",
        )
    text = ops_doc.read_text(encoding="utf-8")
    referenced = "INTEGRATION-CHECKLIST.md" in text or "agent-integration/INTEGRATION-CHECKLIST" in text
    return CheckResult(
        check_id="INT-010",
        severity=Severity.P2,
        passed=referenced and checklist.is_file(),
        detail=(
            "ops doc references INTEGRATION-CHECKLIST.md"
            if referenced
            else "ops doc missing INTEGRATION-CHECKLIST reference"
        ),
    )


def _import_check_drift(root: Path):
    workflow_dir = ai_infra_dir(root) / "scripts" / "workflow"
    workflow_str = str(workflow_dir)
    if workflow_str not in sys.path:
        sys.path.insert(0, workflow_str)
    import check_drift

    return check_drift


def _check_int011(paths: dict[str, Path]) -> CheckResult:
    agent_source = paths["agents_dir"] / "workflow-drift-guard.md"
    plugin_copy = paths["plugin_drift_guard"]
    if not agent_source.is_file():
        return CheckResult(
            check_id="INT-011",
            severity=Severity.P0,
            passed=False,
            detail="missing .cursor/agents/workflow-drift-guard.md",
        )
    exists = plugin_copy.is_file()
    return CheckResult(
        check_id="INT-011",
        severity=Severity.P2,
        passed=exists,
        detail=(
            "plugin/agents/workflow-drift-guard.md present"
            if exists
            else "missing plugin/agents/workflow-drift-guard.md — run make sync-plugin"
        ),
    )


def _check_int012(root: Path) -> CheckResult:
    workflow_dir = ai_infra_dir(root) / "scripts" / "workflow"
    if not workflow_dir.is_dir():
        return CheckResult(
            check_id="INT-012",
            severity=Severity.P0,
            passed=False,
            detail="missing .ai_infra/scripts/workflow",
        )
    try:
        check_drift = _import_check_drift(root)
    except ImportError as exc:
        return CheckResult(
            check_id="INT-012",
            severity=Severity.P0,
            passed=False,
            detail=f"check_drift import failed: {exc}",
        )
    results = check_drift.run_checks(root)
    p0_failures = [r for r in results if not r.passed and r.severity == Severity.P0]
    return CheckResult(
        check_id="INT-012",
        severity=Severity.P0,
        passed=not p0_failures,
        detail=(
            "drift P0 checks pass"
            if not p0_failures
            else "; ".join(f"{r.check_id}: {r.detail}" for r in p0_failures)
        ),
    )


def _import_check_doc_facts(root: Path):
    arch_dir = ai_infra_dir(root) / "scripts" / "architecture"
    if not arch_dir.is_dir():
        raise FileNotFoundError(f"missing {arch_dir}")
    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import check_doc_facts

    return check_doc_facts


def _check_int013(root: Path) -> CheckResult:
    try:
        check_doc_facts = _import_check_doc_facts(root)
    except FileNotFoundError as exc:
        return CheckResult(
            check_id="INT-013",
            severity=Severity.P0,
            passed=False,
            detail=f"check_doc_facts import failed: {exc}",
        )
    from doc_facts_checks import is_kit_dev

    if not is_kit_dev(root):
        return CheckResult(
            check_id="INT-013",
            severity=Severity.P1,
            passed=True,
            detail="consumer profile — doc facts skipped",
        )
    results = check_doc_facts.run_checks(root)
    failures = [
        r for r in results if not r.passed and r.severity.value in ("P0", "P1")
    ]
    return CheckResult(
        check_id="INT-013",
        severity=Severity.P1,
        passed=not failures,
        detail=(
            "doc facts checks pass"
            if not failures
            else "; ".join(f"{r.check_id}: {r.detail}" for r in failures)
        ),
    )


def run_checks(root: Path | None = None) -> list[CheckResult]:
    project_root = (root or Path.cwd()).resolve()
    paths = _paths(project_root)
    us = _import_user_settings(project_root)

    registry_result = _check_registry_file(paths)
    return [
        _check_int001(paths),
        registry_result,
        CheckResult(
            check_id="INT-003",
            severity=Severity.P0,
            passed=registry_result.passed,
            detail=registry_result.detail,
        ),
        _check_int004(us, paths),
        _check_int005(us, project_root, paths),
        _check_int006(us, project_root),
        _check_int007(us, project_root),
        _check_int008(paths),
        _check_int009(paths),
        _check_int010(paths),
        _check_int011(paths),
        _check_int012(project_root),
        _check_int013(project_root),
    ]


def format_report(results: list[CheckResult]) -> str:
    lines: list[str] = []
    p0_fail = p1_fail = p2_fail = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        if not result.passed:
            if result.severity == Severity.P0:
                p0_fail += 1
            elif result.severity == Severity.P1:
                p1_fail += 1
            else:
                p2_fail += 1
        lines.append(f"[{result.severity.value}] {result.check_id} {status}: {result.detail}")
    lines.append(
        f"summary: p0_fail={p0_fail} p1_fail={p1_fail} p2_fail={p2_fail} total={len(results)}"
    )
    return "\n".join(lines)


def exit_code_for(results: list[CheckResult]) -> int:
    return 1 if any(not r.passed and r.severity == Severity.P0 for r in results) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MAS infrastructure integration validate")
    parser.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Project root (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    results = run_checks(args.directory.resolve())
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
            "exit_code": exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(results))
    return exit_code_for(results)


if __name__ == "__main__":
    raise SystemExit(main())
