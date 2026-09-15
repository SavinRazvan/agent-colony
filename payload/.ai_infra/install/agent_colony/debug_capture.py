"""
File: debug_capture.py
Path: .ai_infra/install/agent_colony/debug_capture.py
Role: Secure command capture and log ingest for debugger campaigns.
Used By:
 - .ai_infra/install/agent_colony/debug_campaign.py
 - .ai_infra/install/agent_colony/debug_cli.py
Depends On:
 - .ai_infra/install/agent_colony/debug_redaction.py
 - .ai_infra/install/agent_colony/debug_storage.py
 - subprocess
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import debug_redaction
import debug_storage

DEFAULT_TIMEOUT_SECONDS = 300
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 7200


class DebugCaptureError(RuntimeError):
    """Raised when a capture cannot commit usable evidence."""


@dataclass(frozen=True)
class CaptureResult:
    run_id: str
    run_dir: Path
    child_exit_code: int | None
    termination_reason: str
    stdout_bytes: int
    stderr_bytes: int
    combined_bytes: int
    evidence_sha256: str


@dataclass
class _DrainState:
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    invalid_utf8_stdout: int = 0
    invalid_utf8_stderr: int = 0
    limit_exceeded: bool = False
    errors: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


def capture_command(
    *,
    workspace: Path,
    campaign_dir: Path,
    argv: list[str],
    cwd: str | Path | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_SECONDS,
    budget: debug_storage.Budget | None = None,
    propagate_exit: bool = False,
    env: dict[str, str] | None = None,
) -> tuple[int, CaptureResult]:
    if os.name == "nt":
        raise DebugCaptureError("debug capture is POSIX-only; native Windows is refused before spawn")
    if not argv:
        raise DebugCaptureError("capture requires argv after --")
    if timeout_s < MIN_TIMEOUT_SECONDS or timeout_s > MAX_TIMEOUT_SECONDS:
        raise DebugCaptureError("timeout must be between 1 and 7200 seconds")

    workspace_root = workspace.resolve()
    run_cwd = workspace_root if cwd is None else debug_storage.resolve_under(workspace_root, cwd, must_exist=True)
    if not run_cwd.is_dir():
        raise DebugCaptureError(f"cwd is not a directory: {run_cwd}")

    effective_budget = budget or debug_storage.Budget()
    debug_root = workspace_root / ".local" / "workflow-artifacts" / "debug"
    env_for_child = dict(os.environ if env is None else env)
    env_values = debug_redaction.secret_env_values(env_for_child)

    with debug_storage.CampaignLock(campaign_dir):
        debug_storage.enforce_budget(campaign_dir, debug_root, effective_budget)
        run_id = debug_storage.allocate_run_id(campaign_dir)
        run_dir = campaign_dir / "vault" / "logs" / "by-run" / run_id
        started_at = debug_storage.utc_now()
        redacted_argv, argv_report = debug_redaction.redact_text(" ".join(argv), env_for_child)
        meta_path = run_dir / "meta.json"
        debug_storage.atomic_write_json(
            meta_path,
            {
                "schema_version": debug_storage.SCHEMA_VERSION,
                "run_id": run_id,
                "capture_kind": "command",
                "status": "running",
                "started_at": started_at,
                "finished_at": None,
                "argv": redacted_argv,
                "cwd": debug_storage.relative_to(run_cwd, workspace_root),
                "timeout_s": timeout_s,
                "limits": {
                    "stream_limit_bytes": effective_budget.stream_limit_bytes,
                    "combined_limit_bytes": effective_budget.combined_limit_bytes,
                },
                "redaction": {
                    "rule_version": argv_report.rule_version,
                    "replacement_counts": argv_report.replacement_counts,
                },
            },
        )
        debug_storage.append_jsonl(
            campaign_dir / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": debug_storage.SCHEMA_VERSION,
                "event": "capture_started",
                "run_id": run_id,
                "timestamp": started_at,
            },
        )

        stdout_part = run_dir / "stdout.log.part"
        stderr_part = run_dir / "stderr.log.part"
        try:
            proc = subprocess.Popen(
                argv,
                cwd=run_cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                env=env_for_child,
                start_new_session=True,
            )
        except OSError as exc:
            raise DebugCaptureError(f"spawn failed: {exc}") from exc

        state = _DrainState()
        state_lock = threading.Lock()
        stop_event = threading.Event()
        stdout_redactor = debug_redaction.StreamingRedactor(env_values)
        stderr_redactor = debug_redaction.StreamingRedactor(env_values)

        with stdout_part.open("wb") as stdout_fh, stderr_part.open("wb") as stderr_fh:
            debug_storage.chmod_owner_only(stdout_part, directory=False)
            debug_storage.chmod_owner_only(stderr_part, directory=False)
            threads = [
                threading.Thread(
                    target=_drain_stream,
                    args=(
                        proc.stdout,
                        stdout_fh,
                        stdout_redactor,
                        "stdout",
                        state,
                        state_lock,
                        stop_event,
                        effective_budget,
                    ),
                    daemon=True,
                ),
                threading.Thread(
                    target=_drain_stream,
                    args=(
                        proc.stderr,
                        stderr_fh,
                        stderr_redactor,
                        "stderr",
                        state,
                        state_lock,
                        stop_event,
                        effective_budget,
                    ),
                    daemon=True,
                ),
            ]
            for thread in threads:
                thread.start()
            termination_reason = _wait_for_process(proc, timeout_s, stop_event, state, state_lock)
            for thread in threads:
                thread.join(timeout=5)
            _write_text(stdout_fh, stdout_redactor.flush())
            _write_text(stderr_fh, stderr_redactor.flush())
            stdout_fh.flush()
            stderr_fh.flush()
            os.fsync(stdout_fh.fileno())
            os.fsync(stderr_fh.fileno())

        stdout_log = run_dir / "stdout.log"
        stderr_log = run_dir / "stderr.log"
        os.replace(stdout_part, stdout_log)
        os.replace(stderr_part, stderr_log)
        debug_storage.chmod_owner_only(stdout_log, directory=False)
        debug_storage.chmod_owner_only(stderr_log, directory=False)

        finished_at = debug_storage.utc_now()
        stdout_hash = debug_storage.sha256_file(stdout_log)
        stderr_hash = debug_storage.sha256_file(stderr_log)
        evidence_hash = debug_storage.sha256_bytes((stdout_hash + stderr_hash).encode("ascii"))
        stdout_counts = stdout_redactor.report.replacement_counts
        stderr_counts = stderr_redactor.report.replacement_counts
        replacement_counts = _merge_counts(argv_report.replacement_counts, stdout_counts, stderr_counts)
        child_exit_code = proc.returncode
        with state_lock:
            stdout_bytes = state.stdout_bytes
            stderr_bytes = state.stderr_bytes
            invalid_stdout = state.invalid_utf8_stdout
            invalid_stderr = state.invalid_utf8_stderr
            errors = list(state.errors or [])
        meta = {
            "schema_version": debug_storage.SCHEMA_VERSION,
            "run_id": run_id,
            "capture_kind": "command",
            "status": "complete",
            "started_at": started_at,
            "finished_at": finished_at,
            "argv": redacted_argv,
            "cwd": debug_storage.relative_to(run_cwd, workspace_root),
            "timeout_s": timeout_s,
            "child_exit_code": child_exit_code,
            "termination_reason": termination_reason,
            "stdout": {
                "path": "stdout.log",
                "bytes": stdout_bytes,
                "sha256": stdout_hash,
                "invalid_utf8_bytes": invalid_stdout,
            },
            "stderr": {
                "path": "stderr.log",
                "bytes": stderr_bytes,
                "sha256": stderr_hash,
                "invalid_utf8_bytes": invalid_stderr,
            },
            "combined_bytes": stdout_bytes + stderr_bytes,
            "evidence_sha256": evidence_hash,
            "limits": {
                "stream_limit_bytes": effective_budget.stream_limit_bytes,
                "combined_limit_bytes": effective_budget.combined_limit_bytes,
            },
            "redaction": {
                "rule_version": debug_redaction.RULE_VERSION,
                "replacement_counts": replacement_counts,
            },
            "errors": errors,
        }
        debug_storage.atomic_write_json(meta_path, meta)
        debug_storage.append_jsonl(
            campaign_dir / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": debug_storage.SCHEMA_VERSION,
                "event": "capture_finished",
                "run_id": run_id,
                "timestamp": finished_at,
                "child_exit_code": child_exit_code,
                "termination_reason": termination_reason,
                "evidence_sha256": evidence_hash,
            },
        )
        result = CaptureResult(
            run_id=run_id,
            run_dir=run_dir,
            child_exit_code=child_exit_code,
            termination_reason=termination_reason,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            combined_bytes=stdout_bytes + stderr_bytes,
            evidence_sha256=evidence_hash,
        )
        return _mapped_exit(result, propagate_exit), result


def ingest_file(
    *,
    workspace: Path,
    campaign_dir: Path,
    source: Path | None,
    stdin_bytes: bytes | None = None,
    budget: debug_storage.Budget | None = None,
    env: dict[str, str] | None = None,
) -> CaptureResult:
    workspace_root = workspace.resolve()
    effective_budget = budget or debug_storage.Budget()
    debug_root = workspace_root / ".local" / "workflow-artifacts" / "debug"
    source_label = "stdin"
    if source is not None:
        source_path = debug_storage.resolve_under(workspace_root, source, must_exist=True)
        if not source_path.is_file():
            raise DebugCaptureError(f"ingest source is not a file: {source}")
        raw = source_path.read_bytes()
        source_label = debug_storage.relative_to(source_path, workspace_root)
    elif stdin_bytes is not None:
        raw = stdin_bytes
    else:
        raise DebugCaptureError("ingest requires --file or piped stdin")
    if len(raw) > effective_budget.stream_limit_bytes:
        raise DebugCaptureError("ingest stream byte limit exceeded")

    with debug_storage.CampaignLock(campaign_dir):
        debug_storage.enforce_budget(campaign_dir, debug_root, effective_budget)
        run_id = debug_storage.allocate_run_id(campaign_dir)
        run_dir = campaign_dir / "vault" / "logs" / "by-run" / run_id
        redactor = debug_redaction.StreamingRedactor(debug_redaction.secret_env_values(env or dict(os.environ)))
        text = raw.decode("utf-8", errors="replace")
        redacted = redactor.redact_chunk(text) + redactor.flush()
        log_path = run_dir / "stdout.log"
        debug_storage.atomic_write_text(log_path, redacted)
        debug_storage.atomic_write_text(run_dir / "stderr.log", "")
        source_hash = debug_storage.sha256_bytes(raw)
        evidence_hash = debug_storage.sha256_file(log_path)
        now = debug_storage.utc_now()
        debug_storage.atomic_write_json(
            run_dir / "meta.json",
            {
                "schema_version": debug_storage.SCHEMA_VERSION,
                "run_id": run_id,
                "capture_kind": "ingest",
                "status": "complete",
                "started_at": now,
                "finished_at": now,
                "source": source_label,
                "source_sha256": source_hash,
                "child_exit_code": None,
                "termination_reason": "ingested",
                "stdout": {
                    "path": "stdout.log",
                    "bytes": len(redacted.encode("utf-8")),
                    "sha256": evidence_hash,
                    "invalid_utf8_bytes": 0,
                },
                "stderr": {
                    "path": "stderr.log",
                    "bytes": 0,
                    "sha256": debug_storage.sha256_file(run_dir / "stderr.log"),
                    "invalid_utf8_bytes": 0,
                },
                "combined_bytes": len(redacted.encode("utf-8")),
                "evidence_sha256": evidence_hash,
                "redaction": {
                    "rule_version": debug_redaction.RULE_VERSION,
                    "replacement_counts": redactor.report.replacement_counts,
                },
            },
        )
        debug_storage.append_jsonl(
            campaign_dir / "vault" / "logs" / "events.jsonl",
            {
                "schema_version": debug_storage.SCHEMA_VERSION,
                "event": "ingest_finished",
                "run_id": run_id,
                "timestamp": now,
                "source_sha256": source_hash,
                "evidence_sha256": evidence_hash,
            },
        )
        return CaptureResult(
            run_id=run_id,
            run_dir=run_dir,
            child_exit_code=None,
            termination_reason="ingested",
            stdout_bytes=len(redacted.encode("utf-8")),
            stderr_bytes=0,
            combined_bytes=len(redacted.encode("utf-8")),
            evidence_sha256=evidence_hash,
        )


def _drain_stream(
    pipe: BinaryIO | None,
    dest: BinaryIO,
    redactor: debug_redaction.StreamingRedactor,
    stream_name: str,
    state: _DrainState,
    state_lock: threading.Lock,
    stop_event: threading.Event,
    budget: debug_storage.Budget,
) -> None:
    if pipe is None:
        return
    while not stop_event.is_set():
        chunk = pipe.read(8192)
        if not chunk:
            break
        decoded = chunk.decode("utf-8", errors="replace")
        invalid = decoded.count("\ufffd")
        encoded_len = len(decoded.encode("utf-8"))
        with state_lock:
            current = state.stdout_bytes if stream_name == "stdout" else state.stderr_bytes
            combined = state.stdout_bytes + state.stderr_bytes
            if current + encoded_len > budget.stream_limit_bytes:
                state.limit_exceeded = True
                stop_event.set()
                state.errors.append(f"{stream_name} stream byte limit exceeded")
                break
            if combined + encoded_len > budget.combined_limit_bytes:
                state.limit_exceeded = True
                stop_event.set()
                state.errors.append("combined byte limit exceeded")
                break
            if stream_name == "stdout":
                state.stdout_bytes += encoded_len
                state.invalid_utf8_stdout += invalid
            else:
                state.stderr_bytes += encoded_len
                state.invalid_utf8_stderr += invalid
        _write_text(dest, redactor.redact_chunk(decoded))


def _wait_for_process(
    proc: subprocess.Popen[bytes],
    timeout_s: int,
    stop_event: threading.Event,
    state: _DrainState,
    state_lock: threading.Lock,
) -> str:
    deadline = time.monotonic() + timeout_s
    reason = "completed"
    while True:
        if proc.poll() is not None:
            return reason
        with state_lock:
            limit_exceeded = state.limit_exceeded
        if limit_exceeded:
            reason = "output_limit"
            _terminate_process_group(proc)
            return reason
        if time.monotonic() >= deadline:
            reason = "timeout"
            stop_event.set()
            _terminate_process_group(proc)
            return reason
        time.sleep(0.02)


def _terminate_process_group(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        proc.terminate()
    try:
        proc.wait(timeout=3)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        proc.kill()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        return


def _write_text(dest: BinaryIO, text: str) -> None:
    if text:
        dest.write(text.encode("utf-8"))


def _merge_counts(*counts: dict[str, int]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for count_map in counts:
        for key, value in count_map.items():
            merged[key] = merged.get(key, 0) + value
    return merged


def _mapped_exit(result: CaptureResult, propagate_exit: bool) -> int:
    if not propagate_exit:
        return 0
    if result.termination_reason == "timeout":
        return 124
    if result.termination_reason == "output_limit":
        return 125
    code = result.child_exit_code
    if code is None:
        return 0
    if code < 0:
        return min(255, 128 + abs(code))
    return min(255, code)
