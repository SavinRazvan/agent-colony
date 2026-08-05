"""
File: test_gh_project_adapter_coverage.py
Path: tests/modules/install/test_gh_project_adapter_coverage.py
Role: Error-path and branch coverage for gh_project_adapter.py (GraphQL/gh adapters).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/gh_project_adapter.py
 - .ai_infra/install/cursor_workflow/project_cli.py
Notes:
 - Monkeypatches project_cli facade; no live network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import gh_project_adapter as gha  # noqa: E402
import project_cli  # noqa: E402
from test_project_cli import SAMPLE_SSOT, VALID_PVTI  # noqa: E402
from test_project_tier1 import _tier1_ssot  # noqa: E402


def _gh_ok(stdout: str = "{}") -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def _gh_fail(msg: str = "gh failed") -> SimpleNamespace:
    return SimpleNamespace(returncode=1, stdout="", stderr=msg)


def test_set_item_date_missing_field() -> None:
    ok, detail = gha.set_item_date(SAMPLE_SSOT, VALID_PVTI, "start_date", "2026-07-18")
    assert not ok
    assert "missing" in detail.lower()


def test_set_item_date_gh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("date edit failed"))
    ok, detail = gha.set_item_date(_tier1_ssot(), VALID_PVTI, "start_date", "2026-07-18")
    assert not ok
    assert "date edit failed" in detail


def test_set_item_number_missing_field() -> None:
    ok, detail = gha.set_item_number(SAMPLE_SSOT, VALID_PVTI, "estimate", 3.0)
    assert not ok
    assert "missing" in detail.lower()


def test_set_item_number_gh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("number edit failed"))
    ok, detail = gha.set_item_number(_tier1_ssot(), VALID_PVTI, "estimate", 2.0)
    assert not ok
    assert "number edit failed" in detail


def test_create_draft_item_gh_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("item-create failed"))
    item_id, raw, err = gha.create_draft_item(SAMPLE_SSOT, "Title", "body")
    assert item_id is None
    assert raw is None
    assert err and "item-create" in err


def test_create_issue_item_no_default_repo() -> None:
    ssot = {**SAMPLE_SSOT, "default_repo": ""}
    item_id, raw, err = gha.create_issue_item(ssot, "T", "B")
    assert item_id is None
    assert "default_repo" in (err or "")


def test_create_issue_item_create_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = {**SAMPLE_SSOT, "default_repo": "o/r"}
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("issue create failed"))
    item_id, raw, err = gha.create_issue_item(ssot, "T", "B")
    assert item_id is None
    assert "issue create" in (err or "")


def test_create_issue_item_no_url_in_output(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = {**SAMPLE_SSOT, "default_repo": "o/r"}

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["issue", "create"]:
            return _gh_ok("Created issue without url\n")
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    item_id, raw, err = gha.create_issue_item(ssot, "T", "B")
    assert item_id is None
    assert "no issue URL" in (err or "")


def test_create_issue_item_add_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = {**SAMPLE_SSOT, "default_repo": "o/r"}

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["issue", "create"]:
            return _gh_ok("https://github.com/o/r/issues/1\n")
        if args[:2] == ["project", "item-add"]:
            return _gh_fail("item-add failed")
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    item_id, raw, err = gha.create_issue_item(ssot, "T", "B")
    assert item_id is None
    assert "item-add failed" in (err or "")


def test_create_issue_item_no_pvti_in_add_output(monkeypatch: pytest.MonkeyPatch) -> None:
    ssot = {**SAMPLE_SSOT, "default_repo": "o/r"}

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        if args[:2] == ["issue", "create"]:
            return _gh_ok("https://github.com/o/r/issues/1\n")
        if args[:2] == ["project", "item-add"]:
            return _gh_ok('{"title":"x"}')
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    item_id, raw, err = gha.create_issue_item(ssot, "T", "B")
    assert item_id is None
    assert "no PVTI_" in (err or "")


def test_resolve_repository_id_invalid_repo() -> None:
    project_cli._REPO_ID_CACHE.clear()
    rid, err = gha.resolve_repository_id({**SAMPLE_SSOT, "default_repo": "o/r"}, "o/")
    assert rid is None
    assert err and "invalid repository" in err


def test_resolve_repository_id_graphql_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("graphql down"))
    rid, err = gha.resolve_repository_id({**SAMPLE_SSOT, "default_repo": "o/r"}, "o/r")
    assert rid is None
    assert "graphql" in (err or "").lower()


def test_resolve_repository_id_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("not-json"))
    rid, err = gha.resolve_repository_id({**SAMPLE_SSOT, "default_repo": "o/r"}, "o/r")
    assert rid is None
    assert "invalid graphql JSON" in (err or "")


def test_resolve_repository_id_graphql_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()
    payload = json.dumps({"errors": [{"message": "Not Found"}]})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    rid, err = gha.resolve_repository_id({**SAMPLE_SSOT, "default_repo": "o/r"}, "o/r")
    assert rid is None
    assert err == "Not Found"


def test_resolve_repository_id_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()
    payload = json.dumps({"data": {"repository": {}}})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    rid, err = gha.resolve_repository_id({**SAMPLE_SSOT, "default_repo": "o/r"}, "o/r")
    assert rid is None
    assert "not found" in (err or "")


def test_promote_resolve_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: (None, None, None, "resolve failed"),
    )
    ok, detail, meta = gha.promote_draft_item_to_issue(SAMPLE_SSOT, VALID_PVTI)
    assert not ok
    assert detail == "resolve failed"
    assert meta == {}


def test_promote_unsupported_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("pull_request", "1", {}, None),
    )
    ok, detail, meta = gha.promote_draft_item_to_issue(SAMPLE_SSOT, VALID_PVTI)
    assert not ok
    assert "cannot promote" in detail


def test_promote_repo_resolution_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    monkeypatch.setattr(gha, "resolve_repository_id", lambda *a, **k: (None, "no repo"))
    ssot = {**SAMPLE_SSOT, "default_repo": "o/r"}
    ok, detail, meta = gha.promote_draft_item_to_issue(ssot, VALID_PVTI)
    assert not ok
    assert "no repo" in detail


def test_promote_mutation_fine_grained_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_fail("Resource not accessible by fine-grained personal access token")
        if "ProjectV2Item" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "content": {
                                    "__typename": "DraftIssue",
                                    "id": "DI_d1",
                                    "title": "T",
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert not ok
    assert "fine-grained" in detail.lower() or "classic PAT" in detail


def test_promote_mutation_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_ok("bad-json")
        if "ProjectV2Item" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "content": {
                                    "__typename": "DraftIssue",
                                    "id": "DI_d1",
                                    "title": "T",
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert not ok
    assert "invalid promote JSON" in detail


def test_promote_mutation_graphql_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_ok(json.dumps({"errors": [{"message": "mutation denied"}]}))
        if "ProjectV2Item" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "content": {
                                    "__typename": "DraftIssue",
                                    "id": "DI_d1",
                                    "title": "T",
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert not ok
    assert detail == "mutation denied"


def test_promote_mutation_no_item(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_ok(json.dumps({"data": {"convertProjectV2DraftIssueItemToIssue": {}}}))
        if "ProjectV2Item" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "node": {
                                "content": {
                                    "__typename": "DraftIssue",
                                    "id": "DI_d1",
                                    "title": "T",
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert not ok
    assert "no item" in detail


def test_promote_fallback_resolve_issue_number(monkeypatch: pytest.MonkeyPatch) -> None:
    project_cli._REPO_ID_CACHE.clear()
    resolve_calls: list[str] = []

    def fake_resolve(ssot, iid):
        resolve_calls.append(iid)
        if len(resolve_calls) == 1:
            return "draft", "DI_d1", {"title": "T"}, None
        return "issue", "99", {"repo": "o/r"}, None

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "convertProjectV2DraftIssueItemToIssue": {
                                "item": {"id": VALID_PVTI, "content": {"__typename": "Issue"}}
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "resolve_item_content", fake_resolve)
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert ok
    assert meta["issue_number"] == "99"


def test_fetch_project_items_gh_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("item-list failed"))
    items, err = gha.fetch_project_items(SAMPLE_SSOT)
    assert items == []
    assert "item-list" in (err or "")


def test_fetch_project_items_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("not-json"))
    items, err = gha.fetch_project_items(SAMPLE_SSOT)
    assert items == []
    assert "invalid JSON" in (err or "")


def test_fetch_project_item_by_id_ok_maps_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        {
            "data": {
                "node": {
                    "id": VALID_PVTI,
                    "content": {
                        "__typename": "Issue",
                        "body": "## Acceptance\n\nok\n",
                    },
                    "fieldValues": {
                        "nodes": [
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "in_review",
                                "field": {"name": "Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "p1",
                                "field": {"name": "Priority"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "s",
                                "field": {"name": "Size"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldTextValue",
                                "text": "1",
                                "field": {"name": "Estimate"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldDateValue",
                                "date": "2026-07-20",
                                "field": {"name": "Start date"},
                            },
                        ]
                    },
                }
            }
        }
    )
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert err is None
    assert item is not None
    assert item["id"] == VALID_PVTI
    assert item["status"] == "in_review"
    assert item["priority"] == "p1"
    assert item["size"] == "s"
    assert item["estimate"] == "1"
    assert item["start date"] == "2026-07-20"
    assert item["content"]["body"].startswith("## Acceptance")


def test_fetch_project_item_by_id_gh_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("node query failed"))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is None
    assert "node query failed" in (err or "")


def test_fetch_project_item_by_id_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("not-json"))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is None
    assert "invalid graphql JSON" in (err or "")


def test_fetch_project_item_by_id_node_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"data": {"node": None}})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is None
    assert "not found" in (err or "")


def test_resolve_item_content_di_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "run_gh",
        lambda *a, **k: _gh_ok(json.dumps({"data": {"node": {"title": "Draft title"}}})),
    )
    kind, cid, meta, err = gha.resolve_item_content(SAMPLE_SSOT, "DI_abc123")
    assert kind == "draft"
    assert cid == "DI_abc123"
    assert err is None


def test_resolve_item_content_graphql_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("graphql resolve failed"))
    kind, cid, meta, err = gha.resolve_item_content(SAMPLE_SSOT, VALID_PVTI)
    assert kind is None
    assert "graphql resolve failed" in (err or "")


def test_resolve_item_content_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok("bad"))
    kind, cid, meta, err = gha.resolve_item_content(SAMPLE_SSOT, VALID_PVTI)
    assert kind is None
    assert "invalid graphql JSON" in (err or "")


def test_resolve_item_content_graphql_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"errors": [{"message": "not found"}]})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    kind, cid, meta, err = gha.resolve_item_content(SAMPLE_SSOT, VALID_PVTI)
    assert kind is None
    assert err == "not found"


def test_resolve_item_content_item_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"data": {"node": None}})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    kind, cid, meta, err = gha.resolve_item_content(SAMPLE_SSOT, VALID_PVTI)
    assert kind is None
    assert "not found" in (err or "")


def test_resolve_item_content_unsupported_typename(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        {
            "data": {
                "node": {
                    "id": VALID_PVTI,
                    "content": {"__typename": "PullRequest", "id": "PR_1"},
                }
            }
        }
    )
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    kind, cid, meta, err = gha.resolve_item_content(SAMPLE_SSOT, VALID_PVTI)
    assert kind is None
    assert "unsupported content type" in (err or "")


def test_edit_item_body_draft_gh_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("body edit failed"))
    ok, detail = gha.edit_item_body(SAMPLE_SSOT, VALID_PVTI, "new body")
    assert not ok
    assert "body edit failed" in detail


def test_edit_item_body_issue_gh_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("issue", "7", {"repo": "o/r", "title": "T"}, None),
    )
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_fail("issue edit failed"))
    ok, detail = gha.edit_item_body({**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI, "body")
    assert not ok
    assert "issue edit failed" in detail


def test_resolve_repository_id_empty_name_part() -> None:
    project_cli._REPO_ID_CACHE.clear()
    rid, err = gha.resolve_repository_id({**SAMPLE_SSOT, "default_repo": "o/r"}, "/")
    assert rid is None
    assert "invalid repository" in (err or "")


def test_promote_mutation_resolve_fallback_when_number_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_cli._REPO_ID_CACHE.clear()
    resolve_calls: list[str] = []

    def fake_resolve(ssot, iid):
        resolve_calls.append(iid)
        if len(resolve_calls) == 1:
            return "draft", "DI_d1", {"title": "T"}, None
        return "issue", "77", {"repo": "o/r"}, None

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "convertProjectV2DraftIssueItemToIssue": {
                                "item": {
                                    "id": VALID_PVTI,
                                    "content": {"__typename": "Issue"},
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "resolve_item_content", fake_resolve)
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert ok
    assert meta["issue_number"] == "77"


def test_set_item_assignee_draft_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        project_cli,
        "resolve_item_content",
        lambda *a, **k: ("draft", "DI_x", {"title": "T"}, None),
    )
    ok, detail = gha.set_item_assignee(SAMPLE_SSOT, VALID_PVTI, "alice")
    assert not ok
    assert "DraftIssue" in detail


def test_fetch_project_item_by_id_empty_item_id() -> None:
    """Line 427: return None, 'empty item id' when iid is blank."""
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, "")
    assert item is None
    assert "empty item id" in (err or "")


def test_fetch_project_item_by_id_graphql_errors_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 453-454: errors[0] is a dict with 'message'."""
    payload = json.dumps({"errors": [{"message": "Node not accessible"}]})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is None
    assert err == "Node not accessible"


def test_fetch_project_item_by_id_graphql_errors_non_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lines 453-454: errors[0] is not a dict → str(errors)."""
    payload = json.dumps({"errors": ["some string error"]})
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is None
    assert err is not None


def test_fetch_project_item_by_id_non_dict_field_node(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 478: non-dict entries in fieldValues.nodes are skipped via continue."""
    payload = json.dumps({
        "data": {
            "node": {
                "id": VALID_PVTI,
                "content": {"__typename": "Issue", "body": ""},
                "fieldValues": {
                    "nodes": [
                        None,
                        "bad-string",
                        42,
                    ]
                },
            }
        }
    })
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is not None
    assert err is None


def test_fetch_project_item_by_id_empty_field_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Line 484: entries where field_name resolves to empty string are skipped."""
    payload = json.dumps({
        "data": {
            "node": {
                "id": VALID_PVTI,
                "content": {"__typename": "Issue", "body": ""},
                "fieldValues": {
                    "nodes": [
                        {"__typename": "text", "text": "val", "field": {"name": ""}},
                        {"__typename": "text", "text": "val2", "field": None},
                    ]
                },
            }
        }
    })
    monkeypatch.setattr(project_cli, "run_gh", lambda *a, **k: _gh_ok(payload))
    item, err = gha.fetch_project_item_by_id(SAMPLE_SSOT, VALID_PVTI)
    assert item is not None
    assert err is None


def test_promote_post_mutation_resolve_not_issue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_cli._REPO_ID_CACHE.clear()

    def fake_resolve(ssot, iid):
        return "draft", "DI_d1", {"title": "T"}, None

    def fake_gh(args: list[str], *, timeout_s: float = 60.0):
        joined = " ".join(args)
        if "repository(owner" in joined:
            return _gh_ok(json.dumps({"data": {"repository": {"id": "R_x"}}}))
        if "convertProjectV2DraftIssueItemToIssue" in joined:
            return _gh_ok(
                json.dumps(
                    {
                        "data": {
                            "convertProjectV2DraftIssueItemToIssue": {
                                "item": {
                                    "id": VALID_PVTI,
                                    "content": {"__typename": "Issue"},
                                }
                            }
                        }
                    }
                )
            )
        return _gh_fail("unexpected")

    monkeypatch.setattr(project_cli, "resolve_item_content", fake_resolve)
    monkeypatch.setattr(project_cli, "run_gh", fake_gh)
    ok, detail, meta = gha.promote_draft_item_to_issue(
        {**SAMPLE_SSOT, "default_repo": "o/r"}, VALID_PVTI
    )
    assert not ok
    assert "not Issue" in detail or "draft" in detail.lower()

