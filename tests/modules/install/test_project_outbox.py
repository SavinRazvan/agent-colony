"""
File: test_project_outbox.py
Path: tests/modules/install/test_project_outbox.py
Role: Unit tests for board rate-limit outbox (project_outbox.py).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/project_outbox.py
 - .ai_infra/install/cursor_workflow/project_cli.py
Notes:
 - All outbox paths use tmp_path; never touches real .local/generated-data.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_cli  # noqa: E402
import project_outbox  # noqa: E402
from test_project_cli import SAMPLE_SSOT  # noqa: E402

VALID_ITEM_ID = "PVTI_lAHOBl46-84A9KZxtest01"
SHORT_PVTI = "PVTI_stub"
DI_ITEM_ID = "DI_draftitem01"


def _outbox_ssot(tmp_path: Path, **outbox_overrides: object) -> dict:
    rel = "outbox/test-outbox.jsonl"
    outbox = {
        "enabled": True,
        "path": rel,
        "min_graphql_remaining": 200,
        "max_flush_per_run": 10,
        "retry_backoff_seconds": 0,
        **outbox_overrides,
    }
    return {**SAMPLE_SSOT, "outbox": outbox}


def _write_collab(tmp: Path, ssot: dict) -> None:
    path = tmp / ".local" / "user_settings" / "github.collaboration.yaml"
    path.parent.mkdir(parents=True)
    data = {
        "version": 1,
        "owner": {"display_name": "Test User", "github_user": "@test"},
        "project_ssot": ssot,
        "commit_provenance": {"ai_disclosure_mode": "assisted_by"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _outbox_file(tmp_path: Path, ssot: dict) -> Path:
    cfg = project_outbox.load_outbox_config(ssot)
    return project_outbox.outbox_path(tmp_path, cfg)


def _valid_entry(**overrides: object) -> dict:
    base: dict = {
        "id": "00000000-0000-4000-8000-000000000001",
        "ts": "2026-07-18T10:00:00Z",
        "agent": "implementer",
        "github_user": "@test",
        "op": "append-notes",
        "item_id": VALID_ITEM_ID,
        "payload": {"text": "queued note"},
        "status": "pending",
        "attempts": 0,
        "last_error": None,
    }
    base.update(overrides)
    return base


def _mock_graphql(monkeypatch: pytest.MonkeyPatch, *, remaining: int = 5000, error: str | None = None) -> None:
    if error:

        def _fail() -> dict:
            return {
                "remaining": None,
                "limit": None,
                "reset_epoch": None,
                "error": error,
            }

        monkeypatch.setattr(project_outbox, "graphql_rate_limit", _fail)
    else:

        def _ok() -> dict:
            return {
                "remaining": remaining,
                "limit": 5000,
                "reset_epoch": 1700000000,
                "error": None,
            }

        monkeypatch.setattr(project_outbox, "graphql_rate_limit", _ok)


# --- load_outbox_config ---


def test_load_outbox_config_defaults() -> None:
    cfg = project_outbox.load_outbox_config({})
    assert cfg["enabled"] is True
    assert cfg["path"] == ".local/generated-data/board-outbox.jsonl"
    assert cfg["min_graphql_remaining"] == 200
    assert cfg["max_flush_per_run"] == 10
    assert cfg["retry_backoff_seconds"] == 30


def test_load_outbox_config_custom_and_disabled() -> None:
    ssot = {
        "outbox": {
            "enabled": False,
            "path": "/tmp/custom.jsonl",
            "min_graphql_remaining": 50,
            "max_flush_per_run": 3,
            "retry_backoff_seconds": 5,
        }
    }
    cfg = project_outbox.load_outbox_config(ssot)
    assert cfg["enabled"] is False
    assert cfg["path"] == "/tmp/custom.jsonl"
    assert cfg["min_graphql_remaining"] == 50
    assert cfg["max_flush_per_run"] == 3
    assert cfg["retry_backoff_seconds"] == 5


def test_load_outbox_config_missing_outbox_key() -> None:
    cfg = project_outbox.load_outbox_config({"enabled": True})
    assert cfg["enabled"] is True
    assert cfg["path"].endswith("board-outbox.jsonl")


# --- is_rate_limit_error ---


@pytest.mark.parametrize(
    "text,expected",
    [
        ("API rate limit exceeded", True),
        ("secondary rate limit hit", True),
        ("Rate Limit: too many requests", True),
        ("network timeout", False),
        ("", False),
        ("item not found", False),
    ],
)
def test_is_rate_limit_error(text: str, expected: bool) -> None:
    assert project_outbox.is_rate_limit_error(text) is expected


# --- graphql_rate_limit ---


def test_graphql_rate_limit_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"remaining": 4999, "limit": 5000, "reset": 1700000000})

    def fake_run(cmd: list[str], **kwargs: object) -> SimpleNamespace:
        assert cmd[:3] == ["gh", "api", "rate_limit"]
        return SimpleNamespace(returncode=0, stdout=payload, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    rl = project_outbox.graphql_rate_limit()
    assert rl["remaining"] == 4999
    assert rl["limit"] == 5000
    assert rl["reset_epoch"] == 1700000000
    assert rl["error"] is None


def test_graphql_rate_limit_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="gh auth required"),
    )
    rl = project_outbox.graphql_rate_limit()
    assert rl["remaining"] is None
    assert "gh auth required" in (rl["error"] or "")


def test_graphql_rate_limit_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*a: object, **k: object) -> SimpleNamespace:
        raise subprocess.TimeoutExpired(cmd=["gh"], timeout=30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    rl = project_outbox.graphql_rate_limit()
    assert rl["error"] is not None


def test_graphql_rate_limit_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*a: object, **k: object) -> SimpleNamespace:
        raise OSError("no gh binary")

    monkeypatch.setattr(subprocess, "run", fake_run)
    rl = project_outbox.graphql_rate_limit()
    assert "no gh binary" in (rl["error"] or "")


def test_graphql_rate_limit_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="not-json", stderr=""),
    )
    rl = project_outbox.graphql_rate_limit()
    assert "invalid JSON" in (rl["error"] or "")


def test_graphql_rate_limit_non_object(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='"string"', stderr=""),
    )
    rl = project_outbox.graphql_rate_limit()
    assert "not an object" in (rl["error"] or "")


def test_format_reset_iso() -> None:
    assert project_outbox.format_reset_iso(1700000000).startswith("2023-")
    assert project_outbox.format_reset_iso("bad") == "(unknown)"


# --- validate_outbox_entry ---


def test_validate_outbox_entry_happy() -> None:
    assert project_outbox.validate_outbox_entry(_valid_entry()) == []


def test_validate_outbox_entry_missing_fields() -> None:
    entry = _valid_entry()
    del entry["agent"]
    errs = project_outbox.validate_outbox_entry(entry)
    assert any("missing agent" in e for e in errs)


def test_validate_outbox_entry_bad_item_id() -> None:
    errs = project_outbox.validate_outbox_entry(_valid_entry(item_id=SHORT_PVTI))
    assert any("bad item_id" in e for e in errs)
    errs_di = project_outbox.validate_outbox_entry(_valid_entry(item_id=DI_ITEM_ID))
    assert any("bad item_id" in e for e in errs_di)


def test_validate_outbox_entry_unknown_op_and_status() -> None:
    errs = project_outbox.validate_outbox_entry(_valid_entry(op="nope"))
    assert any("unknown op" in e for e in errs)
    errs2 = project_outbox.validate_outbox_entry(_valid_entry(status="queued"))
    assert any("bad status" in e for e in errs2)


def test_validate_outbox_entry_payload_rules() -> None:
    assert any(
        "append-notes payload.text required" in e
        for e in project_outbox.validate_outbox_entry(
            _valid_entry(payload={"text": "  "})
        )
    )
    assert any(
        "set-status payload.to required" in e
        for e in project_outbox.validate_outbox_entry(
            _valid_entry(op="set-status", payload={"to": ""})
        )
    )
    assert any(
        "handoff payload.next required" in e
        for e in project_outbox.validate_outbox_entry(
            _valid_entry(op="handoff", payload={"next": ""})
        )
    )
    assert any(
        "set-assignee payload.login required" in e
        for e in project_outbox.validate_outbox_entry(
            _valid_entry(op="set-assignee", payload={"login": ""})
        )
    )
    assert any(
        "payload must be object" in e
        for e in project_outbox.validate_outbox_entry(_valid_entry(payload="x"))
    )
    assert any(
        "attempts must be non-negative int" in e
        for e in project_outbox.validate_outbox_entry(_valid_entry(attempts=-1))
    )


# --- enqueue_op ---


def test_enqueue_op_writes_jsonl(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id=VALID_ITEM_ID,
        agent="implementer",
        payload={"text": "hello"},
    )
    assert err == ""
    assert entry is not None
    path = _outbox_file(tmp_path, ssot)
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["op"] == "append-notes"
    assert parsed["status"] == "pending"
    assert parsed["item_id"] == VALID_ITEM_ID


def test_enqueue_op_rejects_placeholder_and_short_pvti(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id="PVTI_…",
        agent="implementer",
        payload={"text": "x"},
    )
    assert entry is None
    assert "placeholder" in err
    entry2, err2 = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id=SHORT_PVTI,
        agent="implementer",
        payload={"text": "x"},
    )
    assert entry2 is None
    assert "bad item_id" in err2 or "placeholder" in err2


def test_enqueue_op_rejects_di_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id=DI_ITEM_ID,
        agent="implementer",
        payload={"text": "x"},
    )
    assert entry is None
    assert "bad item_id" in err


def test_enqueue_op_unknown_op_and_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="delete-all",
        item_id=VALID_ITEM_ID,
        agent="implementer",
        payload={"text": "x"},
    )
    assert entry is None
    assert "unknown op" in err
    disabled = _outbox_ssot(tmp_path, enabled=False)
    entry2, err2 = project_outbox.enqueue_op(
        tmp_path,
        disabled,
        op="append-notes",
        item_id=VALID_ITEM_ID,
        agent="implementer",
        payload={"text": "x"},
    )
    assert entry2 is None
    assert "enabled is false" in err2


def test_enqueue_op_resolve_user_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)

    def _boom(root: Path) -> str:
        raise RuntimeError("no user settings")

    monkeypatch.setattr(project_cli, "resolve_human_github_user", _boom)
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id=VALID_ITEM_ID,
        agent="implementer",
        payload={"text": "x"},
        github_user="",
    )
    assert entry is None
    assert "no user settings" in err


def test_enqueue_op_empty_github_user_after_normalize(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "   ")
    monkeypatch.setattr(project_cli, "normalize_github_handle", lambda raw: "")
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id=VALID_ITEM_ID,
        agent="implementer",
        payload={"text": "x"},
    )
    assert entry is None
    assert "github_user missing" in err


def test_enqueue_op_requires_agent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    entry, err = project_outbox.enqueue_op(
        tmp_path,
        ssot,
        op="append-notes",
        item_id=VALID_ITEM_ID,
        agent="",
        payload={"text": "x"},
    )
    assert entry is None
    assert "agent required" in err


# --- count_outbox ---


def test_count_outbox_tallies_and_corrupt(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(_valid_entry(status="pending")),
        json.dumps(_valid_entry(status="done", id="2")),
        json.dumps(_valid_entry(status="failed", id="3")),
        "not valid json",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    counts = project_outbox.count_outbox(path)
    assert counts == {"pending": 1, "done": 1, "failed": 1, "total": 3}


def test_count_outbox_empty_missing(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    counts = project_outbox.count_outbox(path)
    assert counts == {"pending": 0, "done": 0, "failed": 0, "total": 0}


# --- maybe_enqueue_on_gh_fail ---


def test_maybe_enqueue_rate_limit_returns_queued(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    code = project_outbox.maybe_enqueue_on_gh_fail(
        tmp_path,
        ssot,
        cmd="append-notes",
        err_detail="API rate limit exceeded",
        op="append-notes",
        item_id=VALID_ITEM_ID,
        agent="implementer",
        payload={"text": "queued"},
    )
    assert code == project_outbox.EXIT_QUEUED
    err = capsys.readouterr().err
    assert "QUEUED" in err


def test_maybe_enqueue_non_rate_limit_returns_none() -> None:
    ssot = _outbox_ssot(Path("/tmp/unused"))
    assert (
        project_outbox.maybe_enqueue_on_gh_fail(
            Path("/tmp/unused"),
            ssot,
            cmd="append-notes",
            err_detail="network down",
            op="append-notes",
            item_id=VALID_ITEM_ID,
            agent="implementer",
            payload={"text": "x"},
        )
        is None
    )


def test_maybe_enqueue_failure_returns_gh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(tmp_path)
    code = project_outbox.maybe_enqueue_on_gh_fail(
        tmp_path,
        ssot,
        cmd="append-notes",
        err_detail="rate limit",
        op="append-notes",
        item_id=SHORT_PVTI,
        agent="implementer",
        payload={"text": "x"},
    )
    assert code == project_outbox.EXIT_GH
    assert "enqueue failed" in capsys.readouterr().err


def test_maybe_enqueue_disabled_returns_none() -> None:
    ssot = _outbox_ssot(Path("/tmp/unused"), enabled=False)
    assert (
        project_outbox.maybe_enqueue_on_gh_fail(
            Path("/tmp/unused"),
            ssot,
            cmd="append-notes",
            err_detail="rate limit",
            op="append-notes",
            item_id=VALID_ITEM_ID,
            agent="implementer",
            payload={"text": "x"},
        )
        is None
    )


# --- apply_outbox_entry ---


def test_apply_outbox_entry_append_notes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path, ssot, _valid_entry(op="append-notes")
    )
    assert ok
    assert detail == "updated"


def test_apply_outbox_entry_append_notes_idempotent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "idempotent", project_cli.EXIT_OK),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path, ssot, _valid_entry(op="append-notes")
    )
    assert ok
    assert detail == "idempotent"


def test_apply_outbox_entry_set_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (True, "47fc9ee4"),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-status", payload={"to": "in_progress"}),
    )
    assert ok
    assert detail == "47fc9ee4"


def test_apply_outbox_entry_set_assignee(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_assignee",
        lambda ssot, iid, login: (True, "alice"),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-assignee", payload={"login": "alice"}),
    )
    assert ok
    assert detail == "alice"


def test_apply_outbox_entry_claim(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (True, "47fc9ee4"),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(
            op="claim",
            payload={"to": "in_progress", "text": "claimed (outbox flush)"},
        ),
    )
    assert ok
    assert detail == "claimed"


def test_apply_outbox_entry_handoff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (True, "4cc61d42"),
    )
    monkeypatch.setattr(
        project_cli,
        "format_agent_attribution",
        lambda root, agent: "@test/verifier",
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (True, "updated", project_cli.EXIT_OK),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(
            op="handoff",
            payload={"next": "verifier", "to": "in_review", "note": "done slice"},
        ),
    )
    assert ok
    assert detail == "updated"


def test_apply_outbox_entry_handoff_bad_next(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)

    def _raise_bad_agent(root: Path, agent: str) -> str:
        raise ValueError("bad agent")

    monkeypatch.setattr(project_cli, "format_agent_attribution", _raise_bad_agent)
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="handoff", payload={"next": "bad", "note": "x"}),
    )
    assert not ok
    assert "bad agent" in detail


def test_apply_outbox_entry_invalid_op(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path, ssot, _valid_entry(op="bogus")
    )
    assert not ok
    assert "unsupported op" in detail


def test_apply_outbox_entry_claim_status_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (False, "status failed"),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="claim", payload={"to": "in_progress", "text": "claimed"}),
    )
    assert not ok
    assert detail == "status failed"


def test_apply_outbox_entry_claim_notes_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (True, "47fc9ee4"),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes boom", project_cli.EXIT_GH),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="claim", payload={"to": "in_progress", "text": "claimed"}),
    )
    assert not ok
    assert "Notes failed" in detail


def test_apply_outbox_entry_handoff_status_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (False, "handoff status fail"),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(
            op="handoff",
            payload={"next": "verifier", "to": "in_review", "note": "x"},
        ),
    )
    assert not ok
    assert detail == "handoff status fail"


# --- flush_outbox ---


def test_flush_outbox_refuses_low_remaining(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _mock_graphql(monkeypatch, remaining=50)
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_GH
    assert "remaining=50" in summary
    assert "refuse flush" in summary


def test_flush_outbox_invalid_remaining_type(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)

    def _bad_rl() -> dict:
        return {
            "remaining": "not-a-number",
            "limit": 5000,
            "reset_epoch": 1700000000,
            "error": None,
        }

    monkeypatch.setattr(project_outbox, "graphql_rate_limit", _bad_rl)
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_GH
    assert "refuse flush" in summary


def test_flush_outbox_cap_minimum_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path, max_flush_per_run=0)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    _mock_graphql(monkeypatch, remaining=5000)
    applied: list[str] = []

    def track_apply(root: Path, ssot: dict, entry: dict, **k: object) -> tuple[bool, str]:
        applied.append(str(entry.get("id")))
        return True, "ok"

    monkeypatch.setattr(project_outbox, "apply_outbox_entry", track_apply)
    code, summary = project_outbox.flush_outbox(tmp_path, ssot, max_ops=0)
    assert code == project_outbox.EXIT_OK
    assert len(applied) == 1
    assert "done=1" in summary


def test_flush_outbox_graphql_remaining_typeerror_mid_batch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    calls = {"n": 0}

    def _rl_bad_mid() -> dict:
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "remaining": 5000,
                "limit": 5000,
                "reset_epoch": 1700000000,
                "error": None,
            }
        return {
            "remaining": {"bad": "type"},
            "limit": 5000,
            "reset_epoch": 1700000000,
            "error": None,
        }

    monkeypatch.setattr(project_outbox, "graphql_rate_limit", _rl_bad_mid)
    monkeypatch.setattr(
        project_outbox,
        "apply_outbox_entry",
        lambda *a, **k: (True, "ok"),
    )
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_OK
    assert project_outbox.read_outbox_entries(path)[0]["status"] == "done"


def test_flush_outbox_stops_mid_batch_low_quota(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(
        path,
        [
            _valid_entry(id="batch-a"),
            _valid_entry(id="batch-b", payload={"text": "two"}),
        ],
    )
    calls = {"n": 0}

    def _rl_sequence() -> dict:
        calls["n"] += 1
        # call 1: pre-loop quota check; call 2: first batch iteration; call 3+: low quota
        if calls["n"] <= 2:
            return {
                "remaining": 5000,
                "limit": 5000,
                "reset_epoch": 1700000000,
                "error": None,
            }
        return {
            "remaining": 10,
            "limit": 5000,
            "reset_epoch": 1700000000,
            "error": None,
        }

    monkeypatch.setattr(project_outbox, "graphql_rate_limit", _rl_sequence)
    monkeypatch.setattr(
        project_outbox,
        "apply_outbox_entry",
        lambda *a, **k: (True, "ok"),
    )
    code, summary = project_outbox.flush_outbox(tmp_path, ssot, max_ops=5)
    assert code == project_outbox.EXIT_OK
    assert "stopped early" in summary
    entries = project_outbox.read_outbox_entries(path)
    done = [e for e in entries if e["status"] == "done"]
    pending = [e for e in entries if e["status"] == "pending"]
    assert len(done) == 1
    assert len(pending) == 1


def test_flush_outbox_refuses_rate_limit_read_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _mock_graphql(monkeypatch, error="timeout")
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_GH
    assert "cannot read rate_limit" in summary


def test_flush_outbox_disabled(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path, enabled=False)
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_USAGE
    assert "enabled is false" in summary


def test_flush_outbox_applies_and_marks_done(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    _mock_graphql(monkeypatch, remaining=5000)
    monkeypatch.setattr(
        project_outbox,
        "apply_outbox_entry",
        lambda *a, **k: (True, "updated"),
    )
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_OK
    assert "done=1" in summary
    entries = project_outbox.read_outbox_entries(path)
    assert entries[0]["status"] == "done"
    assert entries[0]["attempts"] == 1


def test_flush_outbox_marks_failed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    _mock_graphql(monkeypatch, remaining=5000)
    monkeypatch.setattr(
        project_outbox,
        "apply_outbox_entry",
        lambda *a, **k: (False, "item not found"),
    )
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_OK
    assert "failed=1" in summary
    entries = project_outbox.read_outbox_entries(path)
    assert entries[0]["status"] == "failed"
    assert entries[0]["last_error"] == "item not found"


def test_flush_outbox_stops_on_rate_limit_during_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(
        path,
        [_valid_entry(id="a"), _valid_entry(id="b", payload={"text": "two"})],
    )
    _mock_graphql(monkeypatch, remaining=5000)

    def flaky_apply(*a: object, **k: object) -> tuple[bool, str]:
        return False, "secondary rate limit exceeded"

    monkeypatch.setattr(project_outbox, "apply_outbox_entry", flaky_apply)
    code, summary = project_outbox.flush_outbox(tmp_path, ssot, max_ops=5)
    assert code == project_outbox.EXIT_GH
    assert "rate-limit" in summary
    entries = project_outbox.read_outbox_entries(path)
    assert entries[0]["status"] == "pending"
    assert entries[0]["attempts"] == 1


def test_flush_outbox_respects_max_flush_per_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path, max_flush_per_run=2)
    path = _outbox_file(tmp_path, ssot)
    entries = [
        _valid_entry(id=f"id-{i}", payload={"text": f"n{i}"}) for i in range(3)
    ]
    project_outbox.write_outbox_entries(path, entries)
    _mock_graphql(monkeypatch, remaining=5000)
    applied: list[str] = []

    def track_apply(root: Path, ssot: dict, entry: dict, **k: object) -> tuple[bool, str]:
        applied.append(str(entry.get("id")))
        return True, "ok"

    monkeypatch.setattr(project_outbox, "apply_outbox_entry", track_apply)
    code, summary = project_outbox.flush_outbox(tmp_path, ssot)
    assert code == project_outbox.EXIT_OK
    assert len(applied) == 2
    assert "pending_left=1" in summary
    stored = project_outbox.read_outbox_entries(path)
    done = [e for e in stored if e["status"] == "done"]
    pending = [e for e in stored if e["status"] == "pending"]
    assert len(done) == 2
    assert len(pending) == 1


def test_queued_message() -> None:
    msg = project_outbox.queued_message("queue", _valid_entry())
    assert "QUEUED" in msg
    assert "outbox flush" in msg


# --- CLI integration (monkeypatch, no network) ---


def test_cmd_queue_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM_ID,
        last=False,
        agent="implementer",
        op="append-notes",
        text="manual queue",
        to=None,
        next=None,
        login=None,
    )
    assert project_cli.cmd_queue(args) == project_cli.EXIT_QUEUED
    out = capsys.readouterr().out
    assert "QUEUED" in out
    assert _outbox_file(tmp_path, ssot).is_file()


def test_cmd_queue_missing_agent_and_bad_op(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    base = dict(
        directory=tmp_path,
        id=VALID_ITEM_ID,
        last=False,
        text="x",
        to=None,
        next=None,
        login=None,
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**base, agent="", op="append-notes")
        )
        == project_cli.EXIT_USAGE
    )
    assert (
        project_cli.cmd_queue(
            argparse.Namespace(**base, agent="implementer", op="bad-op")
        )
        == project_cli.EXIT_USAGE
    )


def test_cmd_outbox_status_prints_counts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    _mock_graphql(monkeypatch, remaining=4500)
    args = argparse.Namespace(directory=tmp_path)
    assert project_cli.cmd_outbox_status(args) == project_cli.EXIT_OK
    out = capsys.readouterr().out
    assert "pending=1" in out
    assert "graphql: remaining=4500" in out


def test_cmd_outbox_flush_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(tmp_path)
    path = _outbox_file(tmp_path, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    _mock_graphql(monkeypatch, remaining=5000)
    monkeypatch.setattr(
        project_outbox,
        "flush_outbox",
        lambda *a, **k: (project_outbox.EXIT_OK, "flushed done=1 failed=0 pending_left=0"),
    )
    args = argparse.Namespace(directory=tmp_path, max=None, limit=100)
    assert project_cli.cmd_outbox_flush(args) == project_cli.EXIT_OK
    assert "flushed done=1" in capsys.readouterr().out


def test_cmd_outbox_flush_refuses_low_remaining(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(
        project_outbox,
        "flush_outbox",
        lambda *a, **k: (
            project_outbox.EXIT_GH,
            "GraphQL remaining=50 < min=200; refuse flush until 2026-01-01T00:00:00Z",
        ),
    )
    args = argparse.Namespace(directory=tmp_path, max=None, limit=100)
    assert project_cli.cmd_outbox_flush(args) == project_cli.EXIT_GH


def _board_item(item_id: str = VALID_ITEM_ID) -> dict:
    return {
        "id": item_id,
        "title": "Slice",
        "status": "Ready",
        "content": {"body": "## Acceptance\n\nx\n\n## Rollback\n\ny\n\n## Notes\n\n"},
    }


def test_cmd_append_notes_auto_queues_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "API rate limit exceeded", project_cli.EXIT_GH),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM_ID,
        last=False,
        text="note",
        agent="implementer",
        limit=50,
    )
    assert project_cli.cmd_append_notes(args) == project_cli.EXIT_QUEUED
    assert _outbox_file(tmp_path, ssot).is_file()


def test_cmd_set_status_auto_queues_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda args, *, timeout_s=60.0: SimpleNamespace(
            returncode=1, stdout="", stderr="rate limit exceeded for graphql"
        ),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM_ID,
        last=False,
        to="in_progress",
        agent="implementer",
    )
    assert project_cli.cmd_set_status(args) == project_cli.EXIT_QUEUED


def test_cmd_claim_auto_queues_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([_board_item()], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (False, "secondary rate limit"),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM_ID,
        last=False,
        agent="implementer",
        text="claimed",
        limit=50,
    )
    assert project_cli.cmd_claim(args) == project_cli.EXIT_QUEUED


def test_cmd_handoff_auto_queues_on_rate_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    _write_collab(tmp_path, ssot)
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "fetch_project_items",
        lambda ssot, limit=100: ([_board_item()], None),
    )
    monkeypatch.setattr(
        project_cli,
        "set_item_status",
        lambda ssot, iid, to: (False, "API rate limit exceeded"),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        id=VALID_ITEM_ID,
        last=False,
        agent="implementer",
        next="verifier",
        to="in_review",
        text="handoff note",
        limit=50,
    )
    assert project_cli.cmd_handoff(args) == project_cli.EXIT_QUEUED


def test_cmd_doctor_warns_low_remaining_and_pending(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    ssot = _outbox_ssot(REPO_ROOT)
    path = _outbox_file(REPO_ROOT, ssot)
    project_outbox.write_outbox_entries(path, [_valid_entry()])
    monkeypatch.setattr(project_cli, "load_project_ssot", lambda root: (ssot, []))
    monkeypatch.setattr(project_cli, "resolve_human_github_user", lambda root: "@test")
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda args, *, timeout_s=60.0: SimpleNamespace(
            returncode=0, stdout='{"items":[]}', stderr=""
        ),
    )
    _mock_graphql(monkeypatch, remaining=50)
    args = argparse.Namespace(directory=REPO_ROOT)
    try:
        assert project_cli.cmd_doctor(args) == project_cli.EXIT_OK
        err = capsys.readouterr().err
        assert "WARN" in err
        assert "min_graphql_remaining" in err or "low GraphQL quota" in err
        assert "pending outbox ops" in err
    finally:
        if path.is_file():
            path.unlink()


def test_apply_outbox_claim_start_date_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["fields"] = {**ssot["fields"], "start_date": {"field_id": "PVTF_start"}}
    monkeypatch.setattr(project_cli, "set_item_status", lambda *a, **k: (True, "ok"))
    monkeypatch.setattr(
        project_cli, "set_item_date", lambda *a, **k: (False, "date failed")
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(
            op="claim",
            payload={"to": "in_progress", "start_date": "2026-07-18", "text": "x"},
        ),
    )
    assert not ok
    assert "start_date failed" in detail


def test_apply_outbox_set_field_estimate_bad_type(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-field", payload={"field": "estimate", "to": "nope"}),
    )
    assert not ok
    assert "must be a number" in detail


def test_apply_outbox_set_field_priority(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-field", payload={"field": "priority", "to": "p1"}),
    )
    assert ok
    assert "priority=p1" in detail


def test_apply_outbox_set_field_unsupported(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-field", payload={"field": "labels", "to": "x"}),
    )
    assert not ok
    assert "unsupported set-field" in detail


def test_apply_outbox_promote_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["default_repo"] = "o/r"
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (False, "promote failed", {}),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="promote-to-issue", payload={"repo": "o/r"}),
    )
    assert not ok
    assert detail == "promote failed"


def test_apply_outbox_promote_notes_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    ssot["default_repo"] = "o/r"
    monkeypatch.setattr(
        project_cli,
        "promote_draft_item_to_issue",
        lambda *a, **k: (
            True,
            "Issue #8",
            {"item_id": VALID_ITEM_ID, "issue_number": "8", "url": "u", "noop": False},
        ),
    )
    monkeypatch.setattr(
        project_cli,
        "append_notes_helper",
        lambda *a, **k: (False, "notes failed", project_cli.EXIT_GH),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(
            op="promote-to-issue",
            payload={"repo": "o/r", "text": "promoted"},
        ),
    )
    assert not ok
    assert "Notes failed" in detail


def test_apply_outbox_set_field_priority_keyerror(tmp_path: Path) -> None:
    ssot = _outbox_ssot(tmp_path)
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-field", payload={"field": "priority", "to": "p99"}),
    )
    assert not ok
    assert "unknown priority" in detail


def test_apply_outbox_set_field_priority_gh_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ssot = _outbox_ssot(tmp_path)
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="edit failed"),
    )
    ok, detail = project_outbox.apply_outbox_entry(
        tmp_path,
        ssot,
        _valid_entry(op="set-field", payload={"field": "priority", "to": "p1"}),
    )
    assert not ok
    assert "edit failed" in detail
