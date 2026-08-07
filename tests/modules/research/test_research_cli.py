"""
File: test_research_cli.py
Path: tests/modules/research/test_research_cli.py
Role: Unit tests for research init/fetch/validate CLI (local path; no network).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/research_cli.py
 - .ai_infra/templates/research-corpus/
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CW_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(CW_DIR) not in sys.path:
    sys.path.insert(0, str(CW_DIR))

import research_cli  # noqa: E402


def _seed_templates(tmp: Path) -> None:
    src = REPO_ROOT / ".ai_infra" / "templates" / "research-corpus"
    dst = tmp / ".ai_infra" / "templates" / "research-corpus"
    shutil.copytree(src, dst)


def test_validate_slug() -> None:
    assert research_cli.validate_slug("") is not None
    assert research_cli.validate_slug("Bad") is not None
    assert research_cli.validate_slug("ok-slug_1") is None


def test_research_init_fetch_validate_local(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    fixture = tmp_path / "fixture-repo"
    fixture.mkdir()
    (fixture / "README.md").write_text("# fixture\n", encoding="utf-8")

    class NS:
        pass

    init = NS()
    init.directory = tmp_path
    init.slug = "demo-pack"
    init.source = f"path:{fixture}"
    init.question = "How is the README structured?"
    init.lenses = "architecture,cli"
    init.consumers = "implementer"
    init.mode = "external"
    init.rounds_max = 6
    init.notes = ""
    init.brief = None
    init.force = False
    assert research_cli.cmd_research_init(init) == 0

    pack = tmp_path / "_research_results" / "sources" / "demo-pack"
    assert (pack / "BRIEF.md").is_file()
    assert (pack / "findings" / "architecture.md").is_file()
    assert (tmp_path / "_research_results" / "RESEARCH_BOUNDARIES.md").is_file()

    fetch = NS()
    fetch.directory = tmp_path
    fetch.slug = "demo-pack"
    fetch.source = f"path:{fixture}"
    fetch.force = False
    assert research_cli.cmd_research_fetch(fetch) == 0
    assert (pack / "SOURCE.md").is_file()
    index = json.loads((pack / "INDEX.json").read_text(encoding="utf-8"))
    assert index["status"] == "fetched"
    assert index["resolved_path"] == str(fixture.resolve())

    validate = NS()
    validate.directory = tmp_path
    validate.slug = "demo-pack"
    assert research_cli.cmd_research_validate(validate) == 0


def test_research_validate_missing_pack(tmp_path: Path) -> None:
    _seed_templates(tmp_path)

    class NS:
        directory = tmp_path
        slug = "missing"

    assert research_cli.cmd_research_validate(NS()) == research_cli.EXIT_FAIL


def test_research_init_rejects_bad_slug(tmp_path: Path) -> None:
    _seed_templates(tmp_path)

    class NS:
        directory = tmp_path
        slug = "BAD"
        source = "path:."
        question = "q"
        lenses = "architecture"
        consumers = "implementer"
        mode = "external"
        rounds_max = 6
        notes = ""
        brief = None
        force = False

    assert research_cli.cmd_research_init(NS()) == research_cli.EXIT_USAGE


def test_load_card_template_research() -> None:
    if str(CW_DIR) not in sys.path:
        sys.path.insert(0, str(CW_DIR))
    import project_atomics

    body = project_atomics.load_card_template(REPO_ROOT, "research")
    assert "## Acceptance" in body
    assert "## Brief" in body
    assert "research" in project_atomics._TEMPLATE_NAMES


def test_structural_validate_index_errors() -> None:
    errs = research_cli.structural_validate_index({"schema_version": "9"})
    assert any("schema_version" in e for e in errs)


def test_parse_source() -> None:
    assert research_cli._parse_source("path:/tmp/x")[0] == "path"
    kind, loc, ref = research_cli._parse_source("github:owner/repo@main")
    assert kind == "github" and loc == "owner/repo" and ref == "main"
    kind2, loc2, ref2 = research_cli._parse_source(
        "https://github.com/SavinRazvan/grok-build"
    )
    assert kind2 == "github" and loc2 == "SavinRazvan/grok-build" and ref2 is None
    kind3, loc3, _ref3 = research_cli._parse_source(
        "https://github.com/SavinRazvan/grok-build.git"
    )
    assert kind3 == "github" and loc3 == "SavinRazvan/grok-build"
    kind4, loc4, ref4 = research_cli._parse_source(
        "https://github.com/SavinRazvan/grok-build/tree/main/crates"
    )
    assert kind4 == "github" and loc4 == "SavinRazvan/grok-build" and ref4 == "main"
    with pytest.raises(ValueError):
        research_cli._parse_source("")


def test_fetch_refuses_without_force_when_source_exists(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    fixture = tmp_path / "fixture-repo"
    fixture.mkdir()
    (fixture / "README.md").write_text("# x\n", encoding="utf-8")

    class NS:
        pass

    init = NS()
    init.directory = tmp_path
    init.slug = "once"
    init.source = f"path:{fixture}"
    init.question = "q"
    init.lenses = "architecture"
    init.consumers = "implementer"
    init.mode = "external"
    init.rounds_max = 6
    init.notes = ""
    init.brief = None
    init.force = False
    assert research_cli.cmd_research_init(init) == 0

    fetch = NS()
    fetch.directory = tmp_path
    fetch.slug = "once"
    fetch.source = f"path:{fixture}"
    fetch.force = False
    assert research_cli.cmd_research_fetch(fetch) == 0
    assert research_cli.cmd_research_fetch(fetch) == research_cli.EXIT_USAGE


def test_rounds_completed_cannot_exceed_rounds_max() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": "x",
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": ["architecture"],
            "findings": [],
            "curated_count": 0,
            "status": "in_progress",
            "rounds_completed": 7,
            "rounds_max": 6,
        }
    )
    assert any("rounds_completed" in e for e in errs)


def test_clone_github_prefers_gh(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **_kwargs):  # noqa: ANN001
        calls.append(list(cmd))

        class P:
            returncode = 0
            stdout = ""
            stderr = ""

        dest = Path(cmd[4]) if cmd[0] == "gh" else Path(cmd[-1])
        dest.mkdir(parents=True, exist_ok=True)
        (dest / ".git").mkdir(exist_ok=True)
        return P()

    monkeypatch.setattr(research_cli.subprocess, "run", fake_run)
    monkeypatch.setattr(research_cli, "_git_sha", lambda _p: "abc123")
    dest = tmp_path / "cache"
    ok, how = research_cli._clone_github("octocat/Hello-World", None, dest)
    assert ok and how == "gh repo clone"
    assert calls and calls[0][0] == "gh"


@pytest.mark.live
def test_live_public_github_fetch_smoke(tmp_path: Path) -> None:
    """Optional: RESEARCH_LIVE=1 pytest -m live … — tiny public clone."""
    import os

    if os.environ.get("RESEARCH_LIVE") != "1":
        pytest.skip("Set RESEARCH_LIVE=1 for live GitHub fetch smoke")
    _seed_templates(tmp_path)

    class NS:
        pass

    init = NS()
    init.directory = tmp_path
    init.slug = "hello-world"
    init.source = "https://github.com/octocat/Hello-World"
    init.question = "smoke"
    init.lenses = "architecture"
    init.consumers = "implementer"
    init.mode = "external"
    init.rounds_max = 1
    init.notes = ""
    init.brief = None
    init.force = False
    assert research_cli.cmd_research_init(init) == 0

    fetch = NS()
    fetch.directory = tmp_path
    fetch.slug = "hello-world"
    fetch.source = "https://github.com/octocat/Hello-World"
    fetch.force = False
    assert research_cli.cmd_research_fetch(fetch) == 0

    pack = tmp_path / "_research_results" / "sources" / "hello-world"
    assert (pack / "SOURCE.md").is_file()

    validate = NS()
    validate.directory = tmp_path
    validate.slug = "hello-world"
    assert research_cli.cmd_research_validate(validate) == 0
