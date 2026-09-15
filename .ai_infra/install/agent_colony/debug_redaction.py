"""
File: debug_redaction.py
Path: .ai_infra/install/agent_colony/debug_redaction.py
Role: Streaming redaction and publish secret scan for debugger evidence.
Used By:
 - .ai_infra/install/agent_colony/debug_capture.py
 - .ai_infra/install/agent_colony/debug_campaign.py
Depends On:
 - re
 - pathlib
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

RULE_VERSION = "debug-redaction-v1"
REPLACEMENT = "[REDACTED]"
_CARRY_CHARS = 8192
_SECRET_ENV_NAME_RE = re.compile(
    r"(SECRET|TOKEN|KEY|PASSWORD|PASSWD|AUTH|CREDENTIAL|PRIVATE|SESSION|COOKIE)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RedactionRule:
    name: str
    pattern: re.Pattern[str]
    replacement: str


@dataclass
class RedactionReport:
    rule_version: str = RULE_VERSION
    replacement_counts: dict[str, int] = field(default_factory=dict)

    def add(self, rule: str, count: int) -> None:
        if count:
            self.replacement_counts[rule] = self.replacement_counts.get(rule, 0) + count


def secret_env_values(env: dict[str, str] | None) -> list[str]:
    if not env:
        return []
    values: list[str] = []
    for key, value in env.items():
        if len(value) >= 8 and _SECRET_ENV_NAME_RE.search(key):
            values.append(value)
    return values


def default_rules(env_values: list[str] | None = None) -> list[RedactionRule]:
    rules = [
        RedactionRule(
            "authorization_bearer",
            re.compile(r"(?i)\b(authorization\s*:\s*bearer\s+)[^\s'\";,]+"),
            rf"\1{REPLACEMENT}",
        ),
        RedactionRule(
            "authorization_basic",
            re.compile(r"(?i)\b(authorization\s*:\s*basic\s+)[A-Za-z0-9+/=_-]+"),
            rf"\1{REPLACEMENT}",
        ),
        RedactionRule(
            "cookies",
            re.compile(r"(?i)\b(cookie|set-cookie)(\s*:\s*)[^\r\n]+"),
            rf"\1\2{REPLACEMENT}",
        ),
        RedactionRule(
            "url_credentials",
            re.compile(r"([a-z][a-z0-9+.-]*://)([^/@\s:]+):([^/@\s]+)@", re.IGNORECASE),
            rf"\1{REPLACEMENT}:{REPLACEMENT}@",
        ),
        RedactionRule(
            "url_secret_query",
            re.compile(
                r"(?i)([?&](?:access_token|api_key|apikey|token|secret|password|passwd|key|client_secret)=)[^&#\s]+"
            ),
            rf"\1{REPLACEMENT}",
        ),
        RedactionRule(
            "token_key_family",
            re.compile(
                r"(?i)\b((?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret[_-]?key|client[_-]?secret|password|passwd)\s*[=:]\s*)[^\s,'\"]+"
            ),
            rf"\1{REPLACEMENT}",
        ),
        RedactionRule(
            "structured_secret_field",
            re.compile(
                r"(?im)^(\s*['\"]?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|secret[_-]?key|client[_-]?secret|password|passwd|private[_-]?key)['\"]?\s*[:=]\s*)['\"]?([^'\"\r\n#]+)['\"]?"
            ),
            rf"\1{REPLACEMENT}",
        ),
        RedactionRule(
            "pem_private_key",
            re.compile(
                r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
                re.DOTALL,
            ),
            REPLACEMENT,
        ),
    ]
    for idx, value in enumerate(env_values or []):
        if value:
            rules.append(
                RedactionRule(
                    f"secret_env_value_{idx}",
                    re.compile(re.escape(value)),
                    REPLACEMENT,
                )
            )
    return rules


class StreamingRedactor:
    """Redact chunked text while preserving enough carry for split secrets."""

    def __init__(self, env_values: list[str] | None = None) -> None:
        self.rules = default_rules(env_values)
        self.report = RedactionReport()
        self._carry = ""

    def redact_chunk(self, chunk: str) -> str:
        combined = self._carry + chunk
        redacted = self._redact_all(combined)
        if len(redacted) <= _CARRY_CHARS:
            self._carry = redacted
            return ""
        out = redacted[:-_CARRY_CHARS]
        self._carry = redacted[-_CARRY_CHARS:]
        return out

    def flush(self) -> str:
        out = self._redact_all(self._carry)
        self._carry = ""
        return out

    def redact_text(self, text: str) -> str:
        return self._redact_all(text)

    def _redact_all(self, text: str) -> str:
        out = text
        for rule in self.rules:
            out, count = rule.pattern.subn(rule.replacement, out)
            self.report.add(rule.name, count)
        return out


def redact_text(text: str, env: dict[str, str] | None = None) -> tuple[str, RedactionReport]:
    redactor = StreamingRedactor(secret_env_values(env))
    out = redactor.redact_chunk(text) + redactor.flush()
    return out, redactor.report


def scan_publish_secrets(publish_root: Path) -> list[str]:
    """Return publish files that still match built-in secret patterns."""
    hits: list[str] = []
    scanner_rules = default_rules([])
    for path in publish_root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            hits.append(f"unreadable publish file: {path}")
            continue
        for rule in scanner_rules:
            if rule.pattern.search(text):
                hits.append(f"{path}: matched {rule.name}")
                break
    return hits
