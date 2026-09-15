"""
File: debug_campaign.py
Path: .ai_infra/install/agent_colony/debug_campaign.py
Role: Debugger campaign lifecycle — init, inventory, analyze, findings, handoff, validate, close.
Used By:
 - .ai_infra/install/agent_colony/debug_cli.py
 - .ai_infra/install/agent_colony/project_atomics.py (validate_for_board)
Depends On:
 - .ai_infra/install/agent_colony/debug_storage.py
 - .ai_infra/install/agent_colony/debug_capture.py
 - .ai_infra/install/agent_colony/debug_redaction.py
 - .ai_infra/templates/debug-campaign/
Notes:
 - Strict jsonschema validation; never silently skip.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore[assignment]

import debug_capture
import debug_redaction
import debug_storage

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_FAIL = 1

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_STATUSES = ("init", "in_progress", "blocked", "ready_for_consumer", "closed")
_MODES = ("incident", "standardize", "structural", "deep")
_DEFAULT_LENSES = [
    "repro",
    "control-error",
    "data-state",
    "concurrency",
    "resource",
    "memory",
    "performance",
    "integration",
]
_TOOL_VERSION = "1.0.0"


class DebugCampaignError(RuntimeError):
    """Campaign lifecycle error."""


def templates_dir(root: Path) -> Path:
    return root / ".ai_infra" / "templates" / "debug-campaign"


def debug_root(root: Path) -> Path:
    return root / ".local" / "workflow-artifacts" / "debug"


def campaign_dir(root: Path, slug: str) -> Path:
    return debug_root(root) / slug


def validate_slug(slug: str) -> str | None:
    s = (slug or "").strip()
    if not s or not _SLUG_RE.match(s):
        return "slug must match ^[a-z0-9][a-z0-9._-]{0,63}$"
    return None


def _read_template(tpl_dir: Path, name: str) -> str:
    path = tpl_dir / name
    if not path.is_file():
        raise DebugCampaignError(f"missing template {path}")
    return path.read_text(encoding="utf-8")


def _render(template: str, values: dict[str, str]) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    return out.rstrip() + "\n"


def _load_schema(root: Path, name: str) -> dict[str, Any]:
    path = templates_dir(root) / "schemas" / name
    if not path.is_file():
        raise DebugCampaignError(f"missing schema {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_against(root: Path, schema_name: str, payload: Any) -> list[str]:
    if jsonschema is None:
        return [
            "jsonschema is required — pip install 'jsonschema>=4' "
            "(or activate with a venv that installs requirements-dev.txt)"
        ]
    try:
        schema = _load_schema(root, schema_name)
        jsonschema.validate(instance=payload, schema=schema)
    except FileNotFoundError as exc:
        return [str(exc)]
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path) if exc.absolute_path else ""
        detail = f"{path}: {exc.message}" if path else exc.message
        return [f"{schema_name}: {detail}"]
    except Exception as exc:  # noqa: BLE001
        return [f"{schema_name}: {exc}"]
    return []


def _require_jsonschema() -> None:
    # Import already required at module top; this exists for clear messaging.
    if jsonschema is None:
        raise DebugCampaignError(
            "jsonschema is required — pip install 'jsonschema>=4' "
            "(or activate with a venv that installs requirements-dev.txt)"
        )


def _git_sha(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def _assert_local_ignored(root: Path) -> None:
    local = root / ".local"
    if not local.exists():
        return
    try:
        tracked = subprocess.run(
            ["git", "-C", str(root), "ls-files", ".local"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    if tracked.returncode == 0 and tracked.stdout.strip():
        raise DebugCampaignError(".local is tracked by git — refuse debug campaigns")
    try:
        check = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", ".local"],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    if check.returncode != 0:
        raise DebugCampaignError(".local is not gitignored — refuse debug campaigns")


def _default_index(
    *,
    slug: str,
    mode: str,
    item_id: str | None,
    lenses: list[str],
    source_revision: str | None,
    supersedes: str | None,
) -> dict[str, Any]:
    budget = debug_storage.Budget()
    now = debug_storage.utc_now()
    return {
        "schema_version": "1",
        "campaign_id": str(uuid.uuid4()),
        "slug": slug,
        "status": "init",
        "mode": mode,
        "item_id": item_id,
        "created_at": now,
        "updated_at": now,
        "tool_version": _TOOL_VERSION,
        "source_revision": source_revision,
        "supersedes": supersedes,
        "lenses": lenses,
        "budgets": {
            "stream_limit_bytes": budget.stream_limit_bytes,
            "combined_limit_bytes": budget.combined_limit_bytes,
            "campaign_limit_bytes": budget.campaign_limit_bytes,
            "root_limit_bytes": budget.root_limit_bytes,
            "min_free_bytes": budget.min_free_bytes,
            "run_limit": budget.run_limit,
        },
        "counters": {"runs_used": 0, "bytes_used": 0},
        "modules": {"done": [], "todo": [], "blocked": []},
        "wave": {"id": 1, "modules": []},
        "human_status": "not_required",
        "human_approver": None,
        "blocked_reason": None,
        "next_agent": None,
        "vault_root": "vault",
        "publish_root": "publish",
        "inventory_digest": None,
        "include": [],
        "exclude": [
            ".git/",
            ".local/",
            ".venv/",
            "venv/",
            "node_modules/",
            "__pycache__/",
            "payload/",
            "htmlcov/",
            ".pytest_cache/",
        ],
    }


def _write_index(camp: Path, index: dict[str, Any]) -> None:
    index["updated_at"] = debug_storage.utc_now()
    debug_storage.atomic_write_json(camp / "INDEX.json", index)


def _read_index(camp: Path) -> dict[str, Any]:
    path = camp / "INDEX.json"
    if not path.is_file():
        raise DebugCampaignError(f"missing INDEX.json: {path}")
    data = debug_storage.read_json(path)
    if not isinstance(data, dict):
        raise DebugCampaignError("INDEX.json must be an object")
    return data


def _ensure_mutable(index: dict[str, Any]) -> None:
    if index.get("status") == "closed":
        raise DebugCampaignError("campaign is closed and immutable")


def init_campaign(
    root: Path,
    *,
    slug: str,
    mode: str = "incident",
    item_id: str | None = None,
    lenses: list[str] | None = None,
    consumers: list[str] | None = None,
    scope: str = "(TBD)",
    notes: str = "(none)",
    supersedes: str | None = None,
) -> Path:
    _require_jsonschema()
    err = validate_slug(slug)
    if err:
        raise DebugCampaignError(err)
    if mode not in _MODES:
        raise DebugCampaignError(f"mode must be one of {_MODES}")
    _assert_local_ignored(root)
    tpl = templates_dir(root)
    if not tpl.is_dir():
        raise DebugCampaignError(f"missing templates at {tpl}")
    droot = debug_root(root)
    debug_storage.ensure_owner_dir(droot)
    boundaries = droot / "DEBUG_BOUNDARIES.md"
    stub = (
        root
        / ".ai_infra"
        / "templates"
        / "local-workspace"
        / "artifact-stubs"
        / "debug"
        / "DEBUG_BOUNDARIES.md"
    )
    if not boundaries.is_file() and stub.is_file():
        shutil.copy2(stub, boundaries)
    camp = campaign_dir(root, slug)
    if camp.exists():
        raise DebugCampaignError(f"campaign exists: {camp} (no --force)")
    debug_storage.enforce_budget(camp, droot, debug_storage.Budget())
    lens_list = lenses or list(_DEFAULT_LENSES)
    consumer_list = consumers or ["implementer", "test-runner"]
    source_revision = _git_sha(root)
    index = _default_index(
        slug=slug,
        mode=mode,
        item_id=item_id,
        lenses=lens_list,
        source_revision=source_revision,
        supersedes=supersedes,
    )
    errors = _validate_against(root, "INDEX.schema.json", index)
    if errors:
        raise DebugCampaignError("; ".join(errors))

    for rel in (
        "vault/logs/by-run",
        "vault/logs",
        "vault/probes",
        "vault/artifacts",
        "vault/scratch",
        "vault/scripts",
        "vault/evidence",
        "publish/project-map/files",
        "publish/runs",
        "publish/findings",
        "publish/attachments",
    ):
        debug_storage.ensure_owner_dir(camp / rel)

    now = debug_storage.utc_now()
    values = {
        "slug": slug,
        "mode": mode,
        "lenses": ", ".join(lens_list),
        "item_id": item_id or "(none)",
        "consumers": ", ".join(consumer_list),
        "human_status": "not_required",
        "scope": scope,
        "notes": notes,
        "symptom": "(TBD)",
        "falsification": "(TBD)",
        "acceptance": "(TBD)",
        "rollback": "(TBD)",
        "created_at": now,
        "campaign_id": index["campaign_id"],
        "status": "init",
        "source_revision": source_revision or "(none)",
        "outcome": "(pending)",
        "next_agent": "(none)",
        "validation": "(pending)",
        "dbg_ids": "(none)",
        "tr_ids": "(none)",
        "sg_ids": "(none)",
        "active_probes": "(none)",
        "publish_refs": "publish/",
        "next_action": "run inventory then experiment loop",
        "probe_rows": "(none)",
        "hypothesis_rows": "(none)",
        "module_rows": "(none)",
        "file_rows": "(none)",
        "dbg_rows": "(none)",
        "tr_rows": "(none)",
        "sg_rows": "(none)",
        "run_id": "run-000001",
        "capture_kind": "(pending)",
        "command": "(pending)",
        "started_at": "(pending)",
        "ended_at": "(pending)",
        "module": "(pending)",
        "lens": "(pending)",
        "hypothesis": "(pending)",
        "exit_code": "(pending)",
        "errors": "(pending)",
        "logs": "(pending)",
        "probe_hits": "(pending)",
        "verdict": "unknown",
        "vault_ref": "vault/logs/by-run/run-000001/",
        "evidence_sha256": "(pending)",
        "root_cause": "(pending)",
        "confidence": "(pending)",
        "evidence": "(pending)",
        "causal_test": "(pending)",
        "fix_boundary": "(pending)",
    }

    (camp / "DEBUG-BRIEF.md").write_text(
        _render(_read_template(tpl, "DEBUG-BRIEF.template.md"), values), encoding="utf-8"
    )
    debug_storage.chmod_owner_only(camp / "DEBUG-BRIEF.md")
    for name, dest in (
        ("session-log.template.md", "vault/session-log.md"),
        ("hypotheses.template.md", "vault/hypotheses.md"),
        ("hypotheses.template.md", "publish/hypotheses.md"),
        ("HANDOFF.template.md", "publish/HANDOFF.md"),
        ("instrumentation-map.template.md", "publish/instrumentation-map.md"),
        ("MODULE-INDEX.template.md", "publish/project-map/MODULE-INDEX.md"),
        (
            "findings/bugs-for-implementer.template.md",
            "publish/findings/bugs-for-implementer.md",
        ),
        (
            "findings/cases-for-test-runner.template.md",
            "publish/findings/cases-for-test-runner.md",
        ),
        (
            "findings/standards-gaps.template.md",
            "publish/findings/standards-gaps.md",
        ),
    ):
        body = _render(_read_template(tpl, name), values)
        path = camp / dest
        debug_storage.atomic_write_text(path, body)

    (camp / "publish" / "signals-index.md").write_text(
        f"# Signals index — {slug}\n\n(empty while active)\n", encoding="utf-8"
    )
    debug_storage.atomic_write_json(
        camp / "vault" / "meta.json",
        {
            "schema_version": "1",
            "campaign_id": index["campaign_id"],
            "slug": slug,
            "created_at": now,
            "agent": "debugger",
        },
    )
    debug_storage.atomic_write_json(
        camp / "vault" / "inventory.json",
        {"schema_version": "1", "files": [], "categories": {}},
    )
    debug_storage.atomic_write_json(
        camp / "vault" / "modules.json",
        {"schema_version": "1", "modules": []},
    )
    debug_storage.atomic_write_text(camp / "vault" / "files.jsonl", "")
    debug_storage.atomic_write_text(camp / "vault" / "logs" / "events.jsonl", "")
    debug_storage.atomic_write_json(
        camp / "vault" / "probes" / "index.json",
        {"schema_version": "1", "probes": []},
    )
    debug_storage.atomic_write_text(camp / "vault" / "artifacts" / "index.jsonl", "")
    debug_storage.atomic_write_json(
        camp / "publish" / "findings" / "index.json",
        {"schema_version": "1", "findings": []},
    )
    debug_storage.atomic_write_json(
        camp / "publish" / "HANDOFF.json",
        {
            "schema_version": "1",
            "campaign_id": index["campaign_id"],
            "slug": slug,
            "status": "init",
            "outcome": "pending",
            "findings": [],
            "next_agent": None,
        },
    )
    debug_storage.atomic_write_json(
        camp / "publish" / "manifest.json",
        {"schema_version": "1", "artifacts": []},
    )
    _write_index(camp, index)
    return camp


def inventory_campaign(root: Path, slug: str) -> dict[str, Any]:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        files: list[dict[str, Any]] = []
        categories = {
            "tracked": 0,
            "untracked": 0,
            "ignored": 0,
            "generated": 0,
            "excluded": 0,
            "inaccessible": 0,
        }
        exclude = set(index.get("exclude") or [])
        paths: list[str] = []
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if proc.returncode == 0:
                paths = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
        except (OSError, subprocess.TimeoutExpired):
            paths = []
        if not paths:
            for path in root.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    try:
                        paths.append(path.relative_to(root).as_posix())
                    except ValueError:
                        categories["inaccessible"] += 1
        for rel in paths:
            if any(rel.startswith(prefix.rstrip("/")) or f"/{prefix.rstrip('/')}/" in f"/{rel}/" for prefix in exclude):
                categories["excluded"] += 1
                continue
            category = "tracked"
            if rel.startswith(("payload/", "agents/", "skills/", "rules/")):
                category = "generated"
            categories[category] = categories.get(category, 0) + 1
            files.append(
                {
                    "schema_version": "1",
                    "path": rel,
                    "category": category,
                    "module": rel.split("/", 1)[0] if "/" in rel else rel,
                    "disposition": "unreviewed",
                }
            )
        digest = hashlib.sha256(
            "\n".join(sorted(f["path"] for f in files)).encode("utf-8")
        ).hexdigest()
        inventory = {
            "schema_version": "1",
            "files": files,
            "categories": categories,
            "digest": digest,
            "source_revision": index.get("source_revision"),
        }
        debug_storage.atomic_write_json(camp / "vault" / "inventory.json", inventory)
        modules: dict[str, dict[str, Any]] = {}
        for row in files:
            mod = row["module"]
            modules.setdefault(
                mod,
                {
                    "id": mod,
                    "importance": "MEDIUM",
                    "status": "pending",
                    "file_count": 0,
                },
            )
            modules[mod]["file_count"] += 1
        debug_storage.atomic_write_json(
            camp / "vault" / "modules.json",
            {"schema_version": "1", "modules": list(modules.values())},
        )
        lines = [json.dumps(row, sort_keys=True) + "\n" for row in files]
        debug_storage.atomic_write_text(camp / "vault" / "files.jsonl", "".join(lines))
        index["inventory_digest"] = digest
        index["modules"]["todo"] = sorted(modules.keys())
        if index["status"] == "init":
            index["status"] = "in_progress"
        _write_index(camp, index)
        debug_storage.append_jsonl(
            camp / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": "1",
                "event": "note_appended",
                "timestamp": debug_storage.utc_now(),
                "summary": f"inventory digest={digest} files={len(files)}",
            },
        )
        return inventory


def analyze_run(
    root: Path,
    slug: str,
    run_id: str,
    *,
    verdict: str = "unknown",
    module: str = "",
    lens: str = "",
    hypothesis: str = "",
) -> Path:
    if verdict not in {"confirmed", "ruled_out", "probable", "unknown"}:
        raise DebugCampaignError("invalid verdict")
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        run_dir = camp / "vault" / "logs" / "by-run" / run_id
        if not run_dir.is_dir():
            raise DebugCampaignError(f"missing run {run_id}")
        meta = debug_storage.read_json(run_dir / "meta.json")
        stderr = ""
        stdout = ""
        if (run_dir / "stderr.log").is_file():
            stderr = (run_dir / "stderr.log").read_text(encoding="utf-8", errors="replace")
        if (run_dir / "stdout.log").is_file():
            stdout = (run_dir / "stdout.log").read_text(encoding="utf-8", errors="replace")
        error_lines = [
            line.strip()
            for line in stderr.splitlines()
            if re.search(r"error|exception|traceback|fail", line, re.I)
        ][:20]
        extracted = run_dir / "extracted" / "errors.txt"
        debug_storage.atomic_write_text(extracted, "\n".join(error_lines) + ("\n" if error_lines else ""))
        tpl = templates_dir(root)
        values = {
            "slug": slug,
            "run_id": run_id,
            "capture_kind": str(meta.get("capture_kind") or "command"),
            "command": str(meta.get("argv_redacted") or meta.get("source") or ""),
            "started_at": str(meta.get("started_at") or ""),
            "ended_at": str(meta.get("ended_at") or ""),
            "module": module or "(none)",
            "lens": lens or "(none)",
            "hypothesis": hypothesis or "(none)",
            "exit_code": str(meta.get("child_exit_code")),
            "errors": "; ".join(error_lines) if error_lines else "(none)",
            "logs": f"stdout={len(stdout)}B stderr={len(stderr)}B",
            "probe_hits": str(meta.get("probe_hits") or "(none)"),
            "verdict": verdict,
            "vault_ref": f"vault/logs/by-run/{run_id}/",
            "evidence_sha256": str(meta.get("evidence_sha256") or ""),
            "notes": "drafted by debug analyze",
        }
        summary = _render(_read_template(tpl, "run-summary.template.md"), values)
        out = camp / "publish" / "runs" / f"{run_id}.md"
        debug_storage.atomic_write_text(out, summary)
        debug_storage.append_jsonl(
            camp / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": "1",
                "event": "analysis_recorded",
                "timestamp": debug_storage.utc_now(),
                "run_id": run_id,
                "verdict": verdict,
            },
        )
        if index["status"] == "init":
            index["status"] = "in_progress"
        index["counters"]["runs_used"] = max(
            int(index["counters"].get("runs_used") or 0),
            int(run_id.split("-")[-1]),
        )
        _write_index(camp, index)
        return out


def append_note(root: Path, slug: str, text: str, *, agent: str = "debugger") -> None:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        redacted, _ = debug_redaction.redact_text(text)
        line = f"- {debug_storage.utc_now()} · {agent} · {redacted.strip()}\n"
        path = camp / "vault" / "session-log.md"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        debug_storage.append_jsonl(
            camp / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": "1",
                "event": "note_appended",
                "timestamp": debug_storage.utc_now(),
                "summary": redacted.strip()[:200],
            },
        )
        _write_index(camp, index)


# CLI-compatible overload used by debug_cli.cmd_note(agent, text positional order)
def append_note_cli(root: Path, slug: str, agent: str, text: str) -> None:
    append_note(root, slug, text, agent=agent)


def finding_add(
    root: Path,
    slug: str,
    *,
    kind: str,
    summary: str,
    severity: str = "p2",
    module: str = "",
    paths: list[str] | None = None,
    owner: str = "",
) -> str:
    if kind not in {"DBG", "TR", "SG"}:
        raise DebugCampaignError("kind must be DBG|TR|SG")
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        findings_path = camp / "publish" / "findings" / "index.json"
        data = debug_storage.read_json(findings_path)
        findings = list(data.get("findings") or [])
        next_n = len(findings) + 1
        fid = f"{kind}-{next_n:03d}"
        default_owner = {
            "DBG": "implementer",
            "TR": "test-runner",
            "SG": "implementer",
        }[kind]
        redacted_summary, _ = debug_redaction.redact_text(summary)
        row = {
            "schema_version": "1",
            "id": fid,
            "kind": kind,
            "severity": severity,
            "status": "open",
            "module": module,
            "paths": paths or [],
            "summary": redacted_summary,
            "owner": owner or default_owner,
            "child_card": None,
        }
        findings.append(row)
        data["findings"] = findings
        debug_storage.atomic_write_json(findings_path, data)
        _render_finding_views(camp, findings)
        debug_storage.append_jsonl(
            camp / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": "1",
                "event": "finding_changed",
                "timestamp": debug_storage.utc_now(),
                "finding_id": fid,
                "status": "open",
            },
        )
        _write_index(camp, index)
        return fid


def _render_finding_views(camp: Path, findings: list[dict[str, Any]]) -> None:
    def rows(kind: str) -> str:
        selected = [f for f in findings if f.get("kind") == kind]
        if not selected:
            return "(none)"
        return " | ".join(
            f"{f['id']} | {f.get('severity')} | {f.get('module')} | {f.get('summary')} | {f.get('owner')} | {f.get('status')}"
            for f in selected
        )

    mapping = {
        "DBG": camp / "publish" / "findings" / "bugs-for-implementer.md",
        "TR": camp / "publish" / "findings" / "cases-for-test-runner.md",
        "SG": camp / "publish" / "findings" / "standards-gaps.md",
    }
    for kind, path in mapping.items():
        body = path.read_text(encoding="utf-8") if path.is_file() else f"# {kind}\n"
        # Keep simple: rewrite a table marker line if present.
        path.write_text(body.replace("{{dbg_rows}}", rows("DBG"))
                        .replace("{{tr_rows}}", rows("TR"))
                        .replace("{{sg_rows}}", rows("SG"))
                        .replace("(none)", rows(kind) if "(none)" in body else "(none)"),
                        encoding="utf-8")


def handoff_campaign(
    root: Path,
    slug: str,
    *,
    next_agent: str = "implementer",
    outcome: str = "ready_for_consumer",
) -> dict[str, Any]:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        findings = debug_storage.read_json(camp / "publish" / "findings" / "index.json").get(
            "findings"
        ) or []
        probes = debug_storage.read_json(camp / "vault" / "probes" / "index.json").get(
            "probes"
        ) or []
        active = [p for p in probes if p.get("status") == "active"]
        payload = {
            "schema_version": "1",
            "campaign_id": index["campaign_id"],
            "slug": slug,
            "status": "ready_for_consumer",
            "mode": index.get("mode"),
            "source_revision": index.get("source_revision"),
            "outcome": outcome,
            "next_agent": next_agent,
            "validation": "pending_close",
            "human_status": index.get("human_status"),
            "findings": [f.get("id") for f in findings],
            "active_probes": [p.get("id") for p in active],
            "publish_root": "publish",
            "vault_root": "vault",
            "child_card_payloads": [
                {
                    "template": "bug" if f.get("kind") == "DBG" else "slice",
                    "finding_id": f.get("id"),
                    "summary": f.get("summary"),
                    "owner": f.get("owner"),
                }
                for f in findings
                if f.get("status") in {"open", "queued", "handed_off"}
            ],
        }
        debug_storage.atomic_write_json(camp / "publish" / "HANDOFF.json", payload)
        md = _render(
            _read_template(templates_dir(root), "HANDOFF.template.md"),
            {
                "slug": slug,
                "campaign_id": str(index["campaign_id"]),
                "status": "ready_for_consumer",
                "mode": str(index.get("mode")),
                "source_revision": str(index.get("source_revision") or "(none)"),
                "outcome": outcome,
                "next_agent": next_agent,
                "validation": "pending_close",
                "human_status": str(index.get("human_status")),
                "dbg_ids": ", ".join(f["id"] for f in findings if f.get("kind") == "DBG")
                or "(none)",
                "tr_ids": ", ".join(f["id"] for f in findings if f.get("kind") == "TR")
                or "(none)",
                "sg_ids": ", ".join(f["id"] for f in findings if f.get("kind") == "SG")
                or "(none)",
                "active_probes": ", ".join(p.get("id", "") for p in active) or "(none)",
                "publish_refs": "publish/HANDOFF.json",
                "next_action": f"create child cards; next={next_agent}",
            },
        )
        debug_storage.atomic_write_text(camp / "publish" / "HANDOFF.md", md)
        index["status"] = "ready_for_consumer"
        index["next_agent"] = next_agent
        _write_index(camp, index)
        return payload


def handoff(
    root: Path,
    slug: str,
    *,
    next_agent: str = "implementer",
    outcome: str = "ready_for_consumer",
) -> dict[str, Any]:
    return handoff_campaign(root, slug, next_agent=next_agent, outcome=outcome)


def mark_run_committed(root: Path, slug: str, kind: str) -> None:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        if index["status"] == "init":
            index["status"] = "in_progress"
        expected, _ = debug_storage.reconstruct_event_counters(camp / "vault" / "logs" / "events.jsonl")
        counters = dict(index.get("counters") or {})
        counters["runs_used"] = expected.get("runs_used", counters.get("runs_used", 0))
        counters["bytes_used"] = debug_storage.directory_size(camp)
        index["counters"] = counters
        _write_index(camp, index)
        _ = kind


def register_artifact(root: Path, slug: str, skill_id: str, raw_path: str) -> dict[str, Any]:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        target = debug_storage.resolve_under(camp, raw_path, must_exist=True)
        rel = target.relative_to(camp).as_posix()
        if not (
            rel.startswith(f"vault/artifacts/{skill_id}/")
            or rel.startswith(f"publish/attachments/{skill_id}/")
        ):
            raise DebugCampaignError(
                "artifact must be under vault/artifacts/<skill-id>/ or publish/attachments/<skill-id>/"
            )
        record = {
            "schema_version": "1",
            "timestamp": debug_storage.utc_now(),
            "skill_id": skill_id,
            "path": rel,
            "bytes": target.stat().st_size,
            "sha256": debug_storage.sha256_file(target),
        }
        debug_storage.append_jsonl(camp / "vault" / "artifacts" / "index.jsonl", record)
        debug_storage.append_jsonl(
            camp / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": "1",
                "event": "artifact_registered",
                "timestamp": debug_storage.utc_now(),
                "skill_id": skill_id,
                "path": rel,
                "bytes": record["bytes"],
                "sha256": record["sha256"],
            },
        )
        _write_index(camp, index)
        return record


def register_probe(root: Path, slug: str, probe_id: str, path: str, note: str = "") -> None:
    _set_probe(root, slug, probe_id, "active", path, note)


def resolve_probe(root: Path, slug: str, probe_id: str, note: str = "") -> None:
    _set_probe(root, slug, probe_id, "resolved", "", note)


def scan_probes(root: Path, slug: str) -> list[str]:
    _ = slug
    hits: list[str] = []
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith((".git/", ".local/", ".venv/", "venv/", "node_modules/")):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in re.finditer(r"DEBUG-PROBE[:\s]+([A-Za-z0-9_.-]+)", text):
            hits.append(f"{rel}:{match.group(1)}")
    return hits


def update_finding(
    root: Path,
    slug: str,
    finding_id: str,
    status: str | None = None,
    child_card: str | None = None,
) -> dict[str, Any]:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        findings_path = camp / "publish" / "findings" / "index.json"
        data = debug_storage.read_json(findings_path)
        findings = list(data.get("findings") or [])
        for row in findings:
            if row.get("id") == finding_id:
                if status:
                    row["status"] = status
                if child_card:
                    row["child_card"] = child_card
                data["findings"] = findings
                debug_storage.atomic_write_json(findings_path, data)
                _render_finding_views(camp, findings)
                debug_storage.append_jsonl(
                    camp / "vault" / "logs" / "events.jsonl",
                    {
                        "schema_version": "1",
                        "event": "finding_changed",
                        "timestamp": debug_storage.utc_now(),
                        "finding_id": finding_id,
                        "status": row.get("status"),
                    },
                )
                _write_index(camp, index)
                return row
    raise DebugCampaignError(f"finding not found: {finding_id}")


def render_findings(root: Path, slug: str) -> None:
    camp = campaign_dir(root, slug)
    findings = debug_storage.read_json(camp / "publish" / "findings" / "index.json").get("findings") or []
    _render_finding_views(camp, findings)


def validate_campaign(root: Path, slug: str, *, final: bool = False) -> list[str]:
    errors = structural_validate(root, slug)
    if final:
        camp = campaign_dir(root, slug)
        if not (camp / "publish" / "manifest.json").is_file():
            errors.append("missing publish/manifest.json")
    return errors


def repair_check(root: Path, slug: str) -> list[str]:
    camp = campaign_dir(root, slug)
    issues: list[str] = []
    if (camp / ".lock").exists():
        issues.append("stale-lock-candidate")
    for part in camp.rglob("*.part"):
        issues.append(f"partial-file:{part.relative_to(camp).as_posix()}")
    try:
        index = _read_index(camp)
    except DebugCampaignError as exc:
        return [str(exc)]
    issues.extend(debug_storage.index_event_divergence(index, camp / "vault" / "logs" / "events.jsonl"))
    return issues


def repair_apply(root: Path, slug: str, acknowledge: str) -> list[str]:
    camp = campaign_dir(root, slug)
    index = _read_index(camp)
    if acknowledge != index.get("campaign_id"):
        raise DebugCampaignError("repair --apply requires --acknowledge <campaign-id>")
    issues = repair_check(root, slug)
    if not issues:
        return []
    archive = camp / "vault" / "recovery" / debug_storage.utc_now().replace(":", "").replace("-", "")
    debug_storage.ensure_owner_dir(archive)
    for path in (camp / "INDEX.json", camp / "vault" / "logs" / "events.jsonl"):
        if path.exists():
            shutil.copy2(path, archive / path.name)
    counters, errors = debug_storage.reconstruct_event_counters(camp / "vault" / "logs" / "events.jsonl")
    if not errors and "runs_used" in index.get("counters", {}):
        index["counters"]["runs_used"] = counters["runs_used"]
        _write_index(camp, index)
    debug_storage.append_jsonl(
        camp / "vault" / "logs" / "events.jsonl",
        {"schema_version": "1", "event": "recovery_applied", "timestamp": debug_storage.utc_now(), "issues": issues},
    )
    return issues


def _set_probe(root: Path, slug: str, probe_id: str, status: str, path: str, note: str) -> None:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        probe_path = camp / "vault" / "probes" / "index.json"
        data = debug_storage.read_json(probe_path)
        probes = list(data.get("probes") or [])
        for row in probes:
            if row.get("id") == probe_id:
                row.update({"status": status, "note": note, "updated_at": debug_storage.utc_now()})
                break
        else:
            probes.append(
                {
                    "schema_version": "1",
                    "id": probe_id,
                    "status": status,
                    "path": path,
                    "note": note,
                    "created_at": debug_storage.utc_now(),
                    "updated_at": debug_storage.utc_now(),
                }
            )
        data["probes"] = probes
        debug_storage.atomic_write_json(probe_path, data)
        debug_storage.append_jsonl(
            camp / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": "1",
                "event": "probe_changed",
                "timestamp": debug_storage.utc_now(),
                "probe_id": probe_id,
                "status": status,
            },
        )
        _write_index(camp, index)


def structural_validate(root: Path, slug: str) -> list[str]:
    camp = campaign_dir(root, slug)
    errors: list[str] = []
    if not camp.is_dir():
        return [f"pack missing: {camp}"]
    try:
        index = _read_index(camp)
    except DebugCampaignError as exc:
        return [str(exc)]
    errors.extend(_validate_against(root, "INDEX.schema.json", index))
    for rel in (
        "DEBUG-BRIEF.md",
        "vault/meta.json",
        "vault/session-log.md",
        "vault/logs/events.jsonl",
        "publish/HANDOFF.json",
        "publish/manifest.json",
        "publish/findings/index.json",
    ):
        if not (camp / rel).exists():
            errors.append(f"missing {rel}")
    events, event_errors = debug_storage.read_jsonl(camp / "vault" / "logs" / "events.jsonl")
    errors.extend(event_errors)
    errors.extend(debug_storage.index_event_divergence(index, camp / "vault" / "logs" / "events.jsonl"))
    runs_dir = camp / "vault" / "logs" / "by-run"
    if runs_dir.is_dir():
        for run_path in sorted(runs_dir.glob("run-*")):
            if (run_path / "stdout.log.part").exists() or (run_path / "stderr.log.part").exists():
                errors.append(f"incomplete capture parts in {run_path.name}")
            summary = camp / "publish" / "runs" / f"{run_path.name}.md"
            if run_path.is_dir() and (run_path / "meta.json").is_file():
                meta = debug_storage.read_json(run_path / "meta.json")
                if meta.get("status") in {"complete", "completed"} and not summary.is_file():
                    if index.get("status") in {"ready_for_consumer", "closed"}:
                        errors.append(f"missing publish summary for {run_path.name}")
                if summary.is_file():
                    text = summary.read_text(encoding="utf-8")
                    for field in (
                        "exit_code:",
                        "errors:",
                        "logs:",
                        "probe_hits:",
                        "verdict:",
                        "vault_ref:",
                        "evidence_sha256:",
                    ):
                        if field not in text:
                            errors.append(f"{summary.name} missing Signals field {field}")
    lock = camp / ".lock"
    if lock.exists():
        owner = lock / "owner.json"
        live = False
        if owner.is_file():
            try:
                meta = debug_storage.read_json(owner)
                live = int(meta.get("pid") or 0) == os.getpid()
            except (TypeError, ValueError, OSError):
                live = False
        if not live:
            errors.append(f"stale or live lock present: {lock}")
    if index.get("status") in {"ready_for_consumer", "closed"}:
        errors.extend(debug_redaction.scan_publish_secrets(camp / "publish"))
    if index.get("status") == "closed":
        probes = debug_storage.read_json(camp / "vault" / "probes" / "index.json").get(
            "probes"
        ) or []
        active = [p for p in probes if p.get("status") == "active"]
        if active:
            errors.append(f"closed campaign has active probes: {[p.get('id') for p in active]}")
        findings = debug_storage.read_json(camp / "publish" / "findings" / "index.json").get(
            "findings"
        ) or []
        for finding in findings:
            if finding.get("status") == "open" and not finding.get("owner"):
                errors.append(f"unowned open finding {finding.get('id')}")
            if finding.get("status") == "open":
                errors.append(
                    f"finding {finding.get('id')} still open — need queued|handed_off with owner"
                )
    _ = events
    return errors


def validate_for_board(root: Path, slug: str, *, board_status: str = "") -> list[str]:
    """Board-facing validation used by project_atomics (not Audit-Schema 1)."""
    errors = structural_validate(root, slug)
    camp = campaign_dir(root, slug)
    if not camp.is_dir():
        return errors
    try:
        index = _read_index(camp)
    except DebugCampaignError as exc:
        return errors + [str(exc)]
    status = str(index.get("status") or "")
    if board_status == "in_review" and status not in {"ready_for_consumer", "closed"}:
        errors.append(
            f"campaign status={status!r} (need ready_for_consumer|closed for In review)"
        )
    if board_status == "done" and status != "closed":
        errors.append(f"campaign status={status!r} (need closed for Done)")
    return errors


def block_campaign(root: Path, slug: str, *, reason: str, human_status: str = "blocked") -> None:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        index["status"] = "blocked"
        index["blocked_reason"] = reason
        index["human_status"] = human_status
        _write_index(camp, index)
        append_note.__wrapped__ if False else None  # placate linters
        # Append note without re-entering lock: write directly.
        redacted, _ = debug_redaction.redact_text(reason)
        with (camp / "vault" / "session-log.md").open("a", encoding="utf-8") as fh:
            fh.write(f"- {debug_storage.utc_now()} · debugger · blocked: {redacted}\n")


def close_campaign(root: Path, slug: str, outcome: str = "closed") -> None:
    camp = campaign_dir(root, slug)
    with debug_storage.CampaignLock(camp):
        index = _read_index(camp)
        _ensure_mutable(index)
        probes = debug_storage.read_json(camp / "vault" / "probes" / "index.json").get("probes") or []
        active = [p for p in probes if p.get("status") == "active"]
        if active:
            raise DebugCampaignError(f"cannot close with active probes: {[p.get('id') for p in active]}")
        # Stage candidate closed INDEX and validate.
        candidate = dict(index)
        candidate["status"] = "closed"
        candidate["outcome"] = outcome
        candidate["updated_at"] = debug_storage.utc_now()
        # Temporarily write candidate for structural checks via in-memory swap
        original = index
        _write_index(camp, candidate)
        errors = structural_validate(root, slug)
        # structural_validate reads closed status rules
        if errors:
            _write_index(camp, original)
            raise DebugCampaignError("; ".join(errors))
        # Final manifest excluding itself
        artifacts = []
        publish = camp / "publish"
        for path in sorted(publish.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name == "manifest.json":
                continue
            artifacts.append(
                {
                    "path": path.relative_to(camp).as_posix(),
                    "sha256": debug_storage.sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
        debug_storage.atomic_write_json(
            publish / "manifest.json",
            {
                "schema_version": "1",
                "campaign_id": candidate["campaign_id"],
                "source_revision": candidate.get("source_revision"),
                "generated_at": debug_storage.utc_now(),
                "artifacts": artifacts,
            },
        )
        _write_index(camp, candidate)


def status_digest(root: Path, slug: str) -> str:
    camp = campaign_dir(root, slug)
    index = _read_index(camp)
    findings = debug_storage.read_json(camp / "publish" / "findings" / "index.json").get(
        "findings"
    ) or []
    probes = debug_storage.read_json(camp / "vault" / "probes" / "index.json").get("probes") or []
    active = [p for p in probes if p.get("status") == "active"]
    return (
        f"slug={slug} status={index.get('status')} mode={index.get('mode')} "
        f"runs={index.get('counters', {}).get('runs_used')} "
        f"findings={len(findings)} active_probes={len(active)} "
        f"next={index.get('next_agent')}"
    )


def capture(
    root: Path,
    slug: str,
    argv: list[str],
    *,
    cwd: str | None = None,
    timeout_s: int = 300,
    propagate_exit: bool = False,
) -> debug_capture.CaptureResult:
    camp = campaign_dir(root, slug)
    index = _read_index(camp)
    _ensure_mutable(index)
    budget = debug_storage.Budget(
        stream_limit_bytes=int(index["budgets"]["stream_limit_bytes"]),
        combined_limit_bytes=int(index["budgets"]["combined_limit_bytes"]),
        campaign_limit_bytes=int(index["budgets"]["campaign_limit_bytes"]),
        root_limit_bytes=int(index["budgets"]["root_limit_bytes"]),
        min_free_bytes=int(index["budgets"]["min_free_bytes"]),
        run_limit=int(index["budgets"]["run_limit"]),
    )
    _code, result = debug_capture.capture_command(
        workspace=root,
        campaign_dir=camp,
        argv=argv,
        cwd=cwd,
        timeout_s=timeout_s,
        budget=budget,
        propagate_exit=propagate_exit,
    )
    mark_run_committed(root, slug, "capture")
    return result


def ingest(
    root: Path,
    slug: str,
    *,
    file_path: str | None = None,
    text: str | None = None,
) -> debug_capture.CaptureResult:
    camp = campaign_dir(root, slug)
    index = _read_index(camp)
    _ensure_mutable(index)
    budget = debug_storage.Budget(
        stream_limit_bytes=int(index["budgets"]["stream_limit_bytes"]),
        combined_limit_bytes=int(index["budgets"]["combined_limit_bytes"]),
        campaign_limit_bytes=int(index["budgets"]["campaign_limit_bytes"]),
        root_limit_bytes=int(index["budgets"]["root_limit_bytes"]),
        min_free_bytes=int(index["budgets"]["min_free_bytes"]),
        run_limit=int(index["budgets"]["run_limit"]),
    )
    source = Path(file_path) if file_path else None
    stdin_bytes = text.encode("utf-8") if text is not None else None
    result = debug_capture.ingest_file(
        workspace=root,
        campaign_dir=camp,
        source=source,
        stdin_bytes=stdin_bytes,
        budget=budget,
    )
    mark_run_committed(root, slug, "ingest")
    return result
