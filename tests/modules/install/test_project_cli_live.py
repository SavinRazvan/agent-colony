"""
File: test_project_cli_live.py
Path: tests/modules/install/test_project_cli_live.py
Role: Optional live smoke against real GitHub Project (skip unless PROJECT_SSOT_LIVE=1).
Used By:
 - pytest (manual / maintainer)
Depends On:
 - .ai_infra/install/agent_colony/project_cli.py
 - gh auth with project scopes
Notes:
 - Never run in default CI; creates and closes a temporary card.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import project_cli  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("PROJECT_SSOT_LIVE") != "1",
    reason="Set PROJECT_SSOT_LIVE=1 for live board smoke",
)


def test_live_create_claim_handoff_validate_done() -> None:
    args_doc = argparse.Namespace(directory=REPO_ROOT)
    assert project_cli.cmd_doctor(args_doc) == 0

    cft = argparse.Namespace(
        directory=REPO_ROOT,
        title="[LIVE-SMOKE] board Pattern A (auto-cleanup)",
        template="slice",
        acceptance="live smoke create→claim→handoff→done",
        rollback="set Status Done",
        notes="",
        status="ready",
    )
    # Capture item_id from stdout by monkeypatching print is awkward; use create_draft path
    ssot, errs = project_cli.load_project_ssot(REPO_ROOT)
    assert not errs and ssot
    body = project_cli.render_card_template(
        project_cli.load_card_template(REPO_ROOT, "slice"),
        acceptance="live smoke",
        rollback="done",
    )
    item_id, raw, err = project_cli.create_draft_item(
        ssot, "[LIVE-SMOKE] board Pattern A (auto-cleanup)", body
    )
    assert err is None, err
    assert item_id, raw
    try:
        ok, _ = project_cli.set_item_status(ssot, item_id, "ready")
        assert ok
        claim = argparse.Namespace(
            directory=REPO_ROOT,
            id=item_id,
            agent="implementer",
            text="live claim",
            limit=100,
        )
        # GraphQL eventual consistency: newly created items may 404 briefly.
        claim_rc = 1
        for _ in range(8):
            claim_rc = project_cli.cmd_claim(claim)
            if claim_rc == 0:
                break
            time.sleep(1.5)
        assert claim_rc == 0, f"claim failed after retries: exit={claim_rc} id={item_id}"
        handoff = argparse.Namespace(
            directory=REPO_ROOT,
            id=item_id,
            agent="implementer",
            next="verifier",
            to="in_review",
            text="live handoff",
            limit=100,
        )
        assert project_cli.cmd_handoff(handoff) == 0
        val = argparse.Namespace(directory=REPO_ROOT, id=item_id, limit=100)
        assert project_cli.cmd_validate_item(val) == 0
    finally:
        project_cli.set_item_status(ssot, item_id, "done")
