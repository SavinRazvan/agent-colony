"""
File: test_research_cli.py
Path: tests/modules/research/test_research_cli.py
Role: Unit tests for research init/fetch/validate CLI (local path; no network).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/research_cli.py
 - .ai_infra/templates/research-corpus/
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CW_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
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
