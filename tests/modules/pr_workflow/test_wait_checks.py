"""
File: test_wait_checks.py
Path: tests/modules/pr_workflow/test_wait_checks.py
Role: Unit tests for wait_checks.py (REST gh pr checks poller; throttle early-exit).
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/wait_checks.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


def _load():
    spec = importlib.util.spec_from_file_location("wait_checks_mod", SCRIPTS_DIR / "wait_checks.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def wait_mod():
    return _load()


def test_is_throttle_output(wait_mod) -> None:
    assert wait_mod.is_throttle_output("Post graphql: Forbidden") is True
    assert wait_mod.is_throttle_output("HTTP 429") is True
    assert wait_mod.is_throttle_output("API rate limit exceeded") is True
    assert wait_mod.is_throttle_output("quality\tpass") is False


def test_wait_pr_checks_pass(wait_mod) -> None:
    code = wait_mod.wait_pr_checks(
        "1",
        timeout_sec=10,
        interval_sec=1,
        sleeper=lambda _s: None,
        runner=lambda _pr: (0, "quality\tpass"),
    )
    assert code == 0


def test_wait_pr_checks_throttle_exits_immediately(wait_mod) -> None:
    calls = {"n": 0}

    def _runner(_pr: str):
        calls["n"] += 1
        return 1, 'Post "https://api.github.com/graphql": Forbidden'

    sleeps: list[int] = []
    code = wait_mod.wait_pr_checks(
        "265",
        timeout_sec=600,
        interval_sec=15,
        sleeper=lambda s: sleeps.append(s),
        runner=_runner,
    )
    assert code == 2
    assert calls["n"] == 1
    assert sleeps == []


def test_wait_pr_checks_timeout(wait_mod) -> None:
    code = wait_mod.wait_pr_checks(
        "9",
        timeout_sec=1,
        interval_sec=1,
        sleeper=lambda _s: None,
        runner=lambda _pr: (1, "quality\tpending"),
    )
    assert code == 1
