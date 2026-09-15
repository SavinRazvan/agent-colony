"""
File: test_debug_redaction.py
Path: tests/modules/debug/test_debug_redaction.py
Role: Tests for streaming debugger redaction rules.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/debug_redaction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

import debug_redaction  # noqa: E402


def test_redacts_common_secret_canaries() -> None:
    canary = "canary-token-abcdefghijklmnopqrstuvwxyz"
    text = (
        f"Authorization: Bearer {canary}\n"
        f"Cookie: session={canary}\n"
        f"https://user:{canary}@example.test/path?api_key={canary}\n"
        f"password: {canary}\n"
        "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"
    )
    redacted, report = debug_redaction.redact_text(text, {"API_TOKEN": canary})
    assert canary not in redacted
    assert "[REDACTED]" in redacted
    assert report.rule_version == debug_redaction.RULE_VERSION
    assert report.replacement_counts


def test_streaming_redaction_carries_split_env_secret() -> None:
    secret = "split-secret-canary"
    redactor = debug_redaction.StreamingRedactor([secret])
    output = redactor.redact_chunk("prefix split-")
    output += redactor.redact_chunk("secret-canary suffix")
    output += redactor.flush()
    assert secret not in output
    assert "[REDACTED]" in output


def test_publish_secret_scan_reports_hits(tmp_path: Path) -> None:
    publish = tmp_path / "publish"
    publish.mkdir()
    (publish / "note.md").write_text("Authorization: Bearer abcdefghijklmnop\n", encoding="utf-8")
    hits = debug_redaction.scan_publish_secrets(publish)
    assert hits and "authorization_bearer" in hits[0]
