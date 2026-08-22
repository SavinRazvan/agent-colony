"""
File: _manifest_version.py
Path: tests/modules/install/_manifest_version.py
Role: Single SSOT for expected kit version in install module tests.
Used By:
 - tests/modules/install/test_*.py
Depends On:
 - .ai_infra/manifest.yaml
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST = REPO_ROOT / ".ai_infra" / "manifest.yaml"


def expected_kit_version() -> str:
    text = _MANIFEST.read_text(encoding="utf-8")
    match = re.search(r'kit_version:\s*"(?P<v>[^"]+)"', text)
    if not match:
        match = re.search(r"kit_version:\s*(?P<v>\S+)", text)
    assert match, f"kit_version missing in {_MANIFEST}"
    return match.group("v")
