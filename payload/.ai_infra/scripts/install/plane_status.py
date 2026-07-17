"""
File: plane_status.py
Path: .ai_infra/scripts/install/plane_status.py
Role: Assess three-plane readiness (Cursor contract, infrastructure, runtime).
Used By:
 - .ai_infra/install/cursor_workflow/activate_cli.py
 - workflow_mcp workflow_activate
Depends On:
 - .ai_infra/install-contract.json
 - pathlib, json (stdlib)
Notes:
 - Uses install-contract required_paths grouped by plane prefix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlaneStatus:
    cursor_contract: bool
    infrastructure: bool
    runtime: bool
    missing: tuple[str, ...]

    @property
    def all_ready(self) -> bool:
        return self.cursor_contract and self.infrastructure and self.runtime


def _contract_path(root: Path) -> Path:
    return root / ".ai_infra" / "install-contract.json"


def _load_contract(root: Path) -> dict:
    path = _contract_path(root)
    if not path.is_file():
        # Consumer may not have contract until first install; use minimal checks.
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_profile(contract: dict, name: str) -> dict:
    if not contract:
        return {"required_paths": []}
    raw = contract.get("profiles", {}).get(name, {})
    if "extends" not in raw:
        return raw
    base = _resolve_profile(contract, raw["extends"])
    merged = {
        "required_paths": list(base.get("required_paths", [])),
        "forbidden_paths": list(base.get("forbidden_paths", [])),
    }
    merged["required_paths"].extend(raw.get("required_paths", []))
    merged["forbidden_paths"].extend(raw.get("forbidden_paths", []))
    return merged


def _plane_for_path(rel: str) -> str:
    if rel.startswith(".local/"):
        return "runtime"
    if rel.startswith(".ai_infra/") or rel.startswith("cursor_workflow/"):
        return "infrastructure"
    if rel.startswith(".cursor/") or rel.startswith(".agents/") or rel == "AGENTS.md":
        return "cursor"
    if rel.startswith("tests/"):
        return "infrastructure"
    return "infrastructure"


def is_kit_dev_repo(root: Path) -> bool:
    return (root / "tests" / "modules" / "install" / "test_scaffold.py").is_file()


CONSUMER_ONLY_PATHS = frozenset(
    {
        "tests/modules/smoke/test_kit_installed.py",
    }
)


def assess_planes(root: Path, *, profile: str = "with_mcp") -> PlaneStatus:
    project_root = root.resolve()
    contract = _load_contract(project_root)
    spec = _resolve_profile(contract, profile)
    required = list(spec.get("required_paths") or [
        ".cursor/agents/implementer.md",
        ".ai_infra/scripts/pr/prepare.py",
        ".local/index-and-planning/current/session-pointer.md",
        "AGENTS.md",
    ])
    if is_kit_dev_repo(project_root):
        required = [rel for rel in required if rel not in CONSUMER_ONLY_PATHS]

    missing: list[str] = []
    plane_hits = {"cursor": True, "infrastructure": True, "runtime": True}

    for rel in required:
        if not (project_root / rel).exists():
            missing.append(rel)
            plane = _plane_for_path(rel)
            plane_hits[plane] = False

    settings_dir = project_root / ".local" / "user_settings"
    _ = settings_dir  # settings exemplars scaffolded at activate; validated separately

    return PlaneStatus(
        cursor_contract=plane_hits["cursor"],
        infrastructure=plane_hits["infrastructure"],
        runtime=plane_hits["runtime"],
        missing=tuple(missing),
    )


def format_plane_report(status: PlaneStatus) -> str:
    def mark(ok: bool) -> str:
        return "ready" if ok else "missing"

    lines = [
        f"cursor_contract: {mark(status.cursor_contract)}",
        f"infrastructure: {mark(status.infrastructure)}",
        f"runtime: {mark(status.runtime)}",
    ]
    if status.missing:
        lines.append("missing_paths:")
        for path in status.missing[:12]:
            lines.append(f"  - {path}")
        if len(status.missing) > 12:
            lines.append(f"  - ... +{len(status.missing) - 12} more")
    return "\n".join(lines)
