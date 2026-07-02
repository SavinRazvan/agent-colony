"""
File: migrate_local_workspace_layout.py
Path: .ai_infra/scripts/dev/migrate_local_workspace_layout.py
Role: Move `.local/` files from legacy flat layout to nested enterprise layout (gitignored tree).
Used By:
 - Maintainers after pulling docs/IA updates
Depends On:
 - pathlib
 - shutil
Notes:
 - Run from repo root. Use `--dry-run` first. Idempotent for already-migrated trees.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ensure_paths_import(__file__)
        break
else:
    raise RuntimeError(f"kit root not found above {__file__}")

from paths import kit_root_from_script, ui_local_workspace

REPO = kit_root_from_script(__file__)
LOCAL = REPO / ".local"
TEMPLATE = ui_local_workspace(REPO)

# (source relative to .local, destination relative to .local)
FILE_MOVES: list[tuple[str, str]] = [
    ("index-and-planning/plan.md", "index-and-planning/current/plan.md"),
    ("index-and-planning/work-tracker.md", "index-and-planning/current/work-tracker.md"),
    ("index-and-planning/test-plan.md", "index-and-planning/current/test-plan.md"),
    ("index-and-planning/test-index.md", "index-and-planning/current/test-index.md"),
    ("index-and-planning/coverage-index.md", "index-and-planning/current/coverage-index.md"),
    ("index-and-planning/updates-log.md", "index-and-planning/history/updates-log.md"),
    (
        "index-and-planning/agent-governance-audit.md",
        "index-and-planning/audits/agent-governance-audit.md",
    ),
    (
        "index-and-planning/agent-governance-todos.md",
        "index-and-planning/audits/agent-governance-todos.md",
    ),
    (
        "agents-control-center/implementation-control-center.html",
        "agents-control-center/dashboards/implementation-control-center.html",
    ),
    ("agents-control-center/module-audit.html", "agents-control-center/audits/module-audit.html"),
    ("workflow-artifacts/review.md", "workflow-artifacts/pr/review.md"),
    ("workflow-artifacts/prep.md", "workflow-artifacts/pr/prep.md"),
    ("workflow-artifacts/merge.md", "workflow-artifacts/pr/merge.md"),
    ("workflow-artifacts/alignment-audit.md", "workflow-artifacts/alignment/alignment-audit.md"),
    ("workflow-artifacts/alignment-todos.md", "workflow-artifacts/alignment/alignment-todos.md"),
    ("generated-data/coverage.json", "generated-data/coverage/coverage.json"),
]

ROOT_MOVES: list[tuple[str, str]] = [
    ("rc-signoff.md", "workflow-artifacts/release/rc-signoff.md"),
    ("rc-signoff.json", "workflow-artifacts/release/rc-signoff.json"),
    ("db-validate-meta.json", "generated-data/validation/db-validate-meta.json"),
    ("ui-e2e-smoke.json", "generated-data/ui/ui-e2e-smoke.json"),
    ("ui-smoke-runtime-snapshots.json", "generated-data/ui/ui-smoke-runtime-snapshots.json"),
    ("byoc-governance-metrics.json", "generated-data/governance/byoc-governance-metrics.json"),
]

ARCHITECTURE_STUB = """<!--
File: architecture.md
Path: .local/index-and-planning/current/architecture.md
Role: Local pointer to durable workspace architecture doc.
Used By:
 - .local/agents-control-center/dashboards/implementation-control-center.html
Depends On:
 - docs/architecture/workspace-architecture.md
Notes:
 - Edit docs/architecture/workspace-architecture.md for doctrine changes.
-->

# Architecture (canonical in docs)

Enduring workspace architecture: **[docs/architecture/workspace-architecture.md](../../../docs/architecture/workspace-architecture.md)**.
"""


def _import_local_workflow_paths() -> object:
    pr_scripts = REPO / ".ai_infra" / "scripts" / "pr"
    pr_str = str(pr_scripts)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import local_workflow_paths

    return local_workflow_paths


def _copy_artifact_readme_stubs(dry_run: bool, log: list[str]) -> None:
    lwp = _import_local_workflow_paths()
    stubs_root = TEMPLATE / "artifact-stubs"
    for bucket in lwp.ARTIFACT_STUB_BUCKET_NAMES:
        src = stubs_root / bucket / "README.md"
        dst = LOCAL / "workflow-artifacts" / bucket / "README.md"
        if not src.is_file():
            continue
        if dst.exists():
            continue
        log.append(f"[COPY] {src.relative_to(REPO)} -> {dst.relative_to(REPO)}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _pages_json_needs_artifact_tabs(pages_path: Path) -> bool:
    if not pages_path.is_file():
        return True
    data = json.loads(pages_path.read_text(encoding="utf-8"))
    ids = {page["id"] for page in data.get("pages", [])}
    return not {"pr-review", "drift-audit", "ea-audit"}.issubset(ids)


def _pages_json_paths_stale(pages_path: Path) -> bool:
    """True when legacy ../../../docs/ paths omit .ai_infra (break ICC fetch over http.server)."""
    if not pages_path.is_file():
        return False
    data = json.loads(pages_path.read_text(encoding="utf-8"))
    for page in data.get("pages", []):
        rel = page.get("file", "")
        if isinstance(rel, str) and rel.startswith("../../../docs/"):
            return True
    return False


def _ensure_workflow_artifact_buckets(dry_run: bool, log: list[str]) -> None:
    lwp = _import_local_workflow_paths()
    if dry_run:
        for bucket in lwp.WORKFLOW_ARTIFACT_BUCKETS:
            log.append(f"[MKDIR] {LOCAL / bucket}")
        return
    lwp.ensure_workflow_artifacts_tree(root=REPO)


def _move(src: Path, dst: Path, dry_run: bool, log: list[str]) -> None:
    if not src.exists():
        return
    if dst.exists():
        log.append(f"[SKIP] destination exists: {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    log.append(f"[MOVE] {src.relative_to(REPO)} -> {dst.relative_to(REPO)}")
    if not dry_run:
        shutil.move(str(src), str(dst))


def _copy_template(name: str, dest: Path, dry_run: bool, log: list[str]) -> None:
    src = TEMPLATE / name
    if not src.exists():
        return
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.append(f"[COPY] {src.relative_to(REPO)} -> {dest.relative_to(REPO)}")
    if not dry_run:
        shutil.copy2(src, dest)


def _copy_template_overwrite(name: str, dest: Path, dry_run: bool, log: list[str]) -> None:
    """Always refresh small shared assets (e.g. site navigator) so `.local` picks up fixes."""
    src = TEMPLATE / name
    if not src.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.append(f"[COPY+] {src.relative_to(REPO)} -> {dest.relative_to(REPO)}")
    if not dry_run:
        shutil.copy2(src, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate .local/ to nested layout.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions only.")
    args = parser.parse_args()
    dry_run = args.dry_run
    log: list[str] = []

    if not LOCAL.exists():
        print("[INFO] .local/ missing; nothing to migrate.")
        return 0

    for rel_src, rel_dst in FILE_MOVES:
        _move(LOCAL / rel_src, LOCAL / rel_dst, dry_run, log)

    for rel_src, rel_dst in ROOT_MOVES:
        _move(LOCAL / rel_src, LOCAL / rel_dst, dry_run, log)

    _ensure_workflow_artifact_buckets(dry_run, log)
    _copy_artifact_readme_stubs(dry_run, log)

    arch_dst = LOCAL / "index-and-planning" / "current" / "architecture.md"
    arch_legacy = LOCAL / "index-and-planning" / "architecture.md"
    arch_snap = LOCAL / "index-and-planning" / "history" / "architecture-legacy-snapshot.md"
    if not arch_dst.exists():
        if arch_legacy.exists():
            _move(arch_legacy, arch_snap, dry_run, log)
        log.append(f"[STUB] write {arch_dst.relative_to(REPO)}")
        if not dry_run:
            arch_dst.parent.mkdir(parents=True, exist_ok=True)
            arch_dst.write_text(ARCHITECTURE_STUB, encoding="utf-8")

    cfg = LOCAL / "agents-control-center" / "config" / "pages.json"
    if _pages_json_needs_artifact_tabs(cfg) or _pages_json_paths_stale(cfg):
        _copy_template_overwrite("pages.json", cfg, dry_run, log)
    else:
        _copy_template("pages.json", cfg, dry_run, log)
    landing = LOCAL / "agents-control-center" / "dashboards" / "index.html"
    _copy_template("index.html", landing, dry_run, log)
    nav_js = LOCAL / "agents-control-center" / "dashboards" / "site-nav.js"
    _copy_template_overwrite("site-nav.js", nav_js, dry_run, log)
    shell_css = LOCAL / "agents-control-center" / "dashboards" / "local-shell.css"
    _copy_template_overwrite("local-shell.css", shell_css, dry_run, log)
    markdown_js = LOCAL / "agents-control-center" / "dashboards" / "local-markdown.js"
    _copy_template_overwrite("local-markdown.js", markdown_js, dry_run, log)
    dash = LOCAL / "agents-control-center" / "dashboards" / "implementation-control-center.html"
    legacy_backup = (
        LOCAL / "agents-control-center" / "dashboards" / "implementation-control-center.legacy.html"
    )
    if dash.exists() and "MANIFEST" not in dash.read_text(encoding="utf-8", errors="replace"):
        log.append(
            f"[BACKUP] legacy dashboard -> {legacy_backup.relative_to(REPO)} "
            "(no manifest loader; replacing with template)"
        )
        if not dry_run:
            legacy_backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dash, legacy_backup)
            shutil.copy2(TEMPLATE / "implementation-control-center.html", dash)
    else:
        _copy_template("implementation-control-center.html", dash, dry_run, log)

    audit_html = LOCAL / "agents-control-center" / "audits" / "module-audit.html"
    _copy_template("audits/module-audit.html", audit_html, dry_run, log)

    summary = LOCAL / "agents-control-center" / "data" / "summary.json"
    if not summary.exists():
        log.append(f"[STUB] write {summary.relative_to(REPO)}")
        if not dry_run:
            summary.parent.mkdir(parents=True, exist_ok=True)
            summary.write_text(
                '{\n  "version": 1,\n  "generated_at": null,\n  "counts": {}\n}\n',
                encoding="utf-8",
            )

    for line in log:
        print(line)
    print(f"[DONE] actions={len(log)} dry_run={dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
