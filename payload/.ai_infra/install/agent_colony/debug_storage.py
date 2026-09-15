"""
File: debug_storage.py
Path: .ai_infra/install/agent_colony/debug_storage.py
Role: Safe storage primitives for debugger campaign evidence.
Used By:
 - .ai_infra/install/agent_colony/debug_capture.py
 - .ai_infra/install/agent_colony/debug_campaign.py
Depends On:
 - hashlib
 - json
 - os
 - pathlib
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"
DEFAULT_STREAM_LIMIT_BYTES = 16 * 1024 * 1024
DEFAULT_COMBINED_LIMIT_BYTES = 32 * 1024 * 1024
DEFAULT_CAMPAIGN_LIMIT_BYTES = 512 * 1024 * 1024
DEFAULT_ROOT_LIMIT_BYTES = 4 * 1024 * 1024 * 1024
DEFAULT_MIN_FREE_BYTES = 1024 * 1024 * 1024
DEFAULT_RUN_LIMIT = 20
HARD_RUN_LIMIT = 200


class DebugStorageError(RuntimeError):
    """Raised when debugger storage cannot be safely used."""


@dataclass(frozen=True)
class Budget:
    stream_limit_bytes: int = DEFAULT_STREAM_LIMIT_BYTES
    combined_limit_bytes: int = DEFAULT_COMBINED_LIMIT_BYTES
    campaign_limit_bytes: int = DEFAULT_CAMPAIGN_LIMIT_BYTES
    root_limit_bytes: int = DEFAULT_ROOT_LIMIT_BYTES
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES
    run_limit: int = DEFAULT_RUN_LIMIT


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def chmod_owner_only(path: Path, *, directory: bool | None = None) -> None:
    """Apply owner-only permissions where POSIX chmod is supported."""
    mode = 0o700 if (directory if directory is not None else path.is_dir()) else 0o600
    try:
        os.chmod(path, mode)
    except (AttributeError, NotImplementedError, OSError):
        return


def ensure_owner_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    chmod_owner_only(path, directory=True)


def resolve_under(root: Path, raw: str | Path, *, must_exist: bool = False) -> Path:
    """Resolve a relative path below root without allowing symlink escape."""
    root_resolved = root.resolve()
    candidate_raw = Path(raw)
    if candidate_raw.is_absolute():
        raise DebugStorageError(f"path must be relative to workspace: {raw}")
    if any(part in ("", ".", "..") for part in candidate_raw.parts):
        raise DebugStorageError(f"path must not contain dot segments: {raw}")
    candidate = root_resolved / candidate_raw
    if must_exist:
        resolved = candidate.resolve(strict=True)
    else:
        existing_parent = candidate.parent.resolve(strict=True)
        if not _is_relative_to(existing_parent, root_resolved):
            raise DebugStorageError(f"path escapes root through symlink: {raw}")
        resolved = existing_parent / candidate.name
    if not _is_relative_to(resolved, root_resolved):
        raise DebugStorageError(f"path escapes root: {raw}")
    return resolved


def relative_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise DebugStorageError(f"path escapes root: {path}") from exc


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_symlink() or not item.is_file():
            continue
        try:
            total += item.stat().st_size
        except OSError:
            continue
    return total


def enforce_budget(campaign_dir: Path, debug_root: Path, budget: Budget) -> None:
    run_dirs = list((campaign_dir / "vault" / "logs" / "by-run").glob("run-[0-9][0-9][0-9][0-9][0-9][0-9]"))
    if len(run_dirs) >= min(budget.run_limit, HARD_RUN_LIMIT):
        raise DebugStorageError("campaign run budget exceeded")
    if directory_size(campaign_dir) > budget.campaign_limit_bytes:
        raise DebugStorageError("campaign byte budget exceeded")
    if directory_size(debug_root) > budget.root_limit_bytes:
        raise DebugStorageError("debug root byte budget exceeded")
    stat = os.statvfs(debug_root if debug_root.exists() else debug_root.parent)
    if stat.f_bavail * stat.f_frsize < budget.min_free_bytes:
        raise DebugStorageError("free disk budget below floor")


def atomic_write_text(path: Path, body: str, *, mode: int = 0o600) -> None:
    ensure_owner_dir(path.parent)
    data = body.encode("utf-8")
    _atomic_write_bytes(path, data, mode=mode)


def atomic_write_json(path: Path, payload: Any, *, mode: int = 0o600) -> None:
    body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    atomic_write_text(path, body, mode=mode)


def _atomic_write_bytes(path: Path, data: bytes, *, mode: int) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
        _fsync_dir(path.parent)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    ensure_owner_dir(path.parent)
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.is_file():
        return rows, [f"missing {path}"]
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        errors.append(f"partial trailing JSONL row: {path}")
    for lineno, raw in enumerate(data.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}:{lineno}: invalid JSONL row: {exc}")
            continue
        if not isinstance(row, dict):
            errors.append(f"{path}:{lineno}: row must be object")
            continue
        rows.append(row)
    return rows, errors


class CampaignLock:
    """Atomic mkdir based campaign lock."""

    def __init__(self, campaign_dir: Path, *, name: str = ".lock") -> None:
        self.campaign_dir = campaign_dir
        self.path = campaign_dir / name
        self.acquired = False

    def __enter__(self) -> "CampaignLock":
        try:
            self.path.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise DebugStorageError(f"campaign locked: {self.path}") from exc
        self.acquired = True
        atomic_write_json(
            self.path / "owner.json",
            {
                "schema_version": SCHEMA_VERSION,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "created_at": utc_now(),
            },
        )
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        if not self.acquired:
            return
        try:
            for child in self.path.iterdir():
                child.unlink()
            self.path.rmdir()
        finally:
            self.acquired = False


def allocate_run_id(campaign_dir: Path) -> str:
    runs = campaign_dir / "vault" / "logs" / "by-run"
    ensure_owner_dir(runs)
    for number in range(1, HARD_RUN_LIMIT + 1):
        run_id = f"run-{number:06d}"
        path = runs / run_id
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            continue
        chmod_owner_only(path, directory=True)
        ensure_owner_dir(path / "extracted")
        return run_id
    raise DebugStorageError("no run ids remain")


def reconstruct_event_counters(events_path: Path) -> tuple[dict[str, int], list[str]]:
    rows, errors = read_jsonl(events_path)
    counters = {
        "runs": 0,
        "captures": 0,
        "ingests": 0,
        "findings": 0,
        "artifacts": 0,
        "probes_active": 0,
        "runs_used": 0,
    }
    active_probes: set[str] = set()
    completed_runs: set[str] = set()
    for row in rows:
        event = row.get("event")
        if event == "capture_finished":
            run_id = str(row.get("run_id") or "")
            if run_id and run_id not in completed_runs:
                completed_runs.add(run_id)
                counters["runs"] += 1
                counters["captures"] += 1
                counters["runs_used"] = max(counters["runs_used"], _run_number(run_id))
        elif event == "ingest_finished":
            run_id = str(row.get("run_id") or "")
            if run_id and run_id not in completed_runs:
                completed_runs.add(run_id)
                counters["runs"] += 1
                counters["ingests"] += 1
                counters["runs_used"] = max(counters["runs_used"], _run_number(run_id))
        elif event == "finding_changed":
            counters["findings"] += 1
        elif event == "artifact_registered":
            counters["artifacts"] += 1
        elif event == "probe_changed":
            probe_id = str(row.get("probe_id") or "")
            if row.get("status") == "active" and probe_id:
                active_probes.add(probe_id)
            elif probe_id:
                active_probes.discard(probe_id)
    counters["probes_active"] = len(active_probes)
    return counters, errors


def index_event_divergence(index: dict[str, Any], events_path: Path) -> list[str]:
    expected, errors = reconstruct_event_counters(events_path)
    actual = index.get("counters") if isinstance(index.get("counters"), dict) else {}
    if "runs_used" in actual:
        if actual.get("runs_used", 0) != expected.get("runs_used", 0):
            errors.append(
                f"INDEX counters.runs_used={actual.get('runs_used', 0)} diverges from events={expected.get('runs_used', 0)}"
            )
        return errors
    for key, value in expected.items():
        if key == "runs_used":
            continue
        if actual.get(key, 0) != value:
            errors.append(f"INDEX counters.{key}={actual.get(key, 0)} diverges from events={value}")
    return errors


def _run_number(run_id: str) -> int:
    try:
        return int(run_id.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
