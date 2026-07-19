"""
File: test_research_cli_coverage.py
Path: tests/modules/research/test_research_cli_coverage.py
Role: Branch and error-path coverage for research_cli.py beyond happy local paths.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/research_cli.py
Notes:
 - No live network; mocks subprocess for git/gh clone paths.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

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


def test_cache_dir_path() -> None:
    root = Path("/tmp/root")
    assert research_cli.cache_dir(root, "slug") == root / "_research_results" / "cache" / "slug"


def test_read_template_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing template"):
        research_cli._read_template(tmp_path, "nope.md")


def test_parse_github_locator_invalid() -> None:
    with pytest.raises(ValueError, match="owner/repo"):
        research_cli._parse_github_locator("onlyowner")


def test_git_sha_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        research_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr=""),
    )
    assert research_cli._git_sha(tmp_path) is None


def test_git_sha_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import subprocess

    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd=["git"], timeout=30)

    monkeypatch.setattr(research_cli.subprocess, "run", raise_timeout)
    assert research_cli._git_sha(tmp_path) is None


def test_structural_validate_index_not_object() -> None:
    errs = research_cli.structural_validate_index([])
    assert errs == ["INDEX.json root must be an object"]


def test_structural_validate_index_missing_fields() -> None:
    errs = research_cli.structural_validate_index({"schema_version": "1"})
    assert any("missing required field" in e for e in errs)


def test_structural_validate_index_bad_slug_type() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": 123,
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": ["a"],
            "findings": [],
            "curated_count": 0,
            "status": "init",
        }
    )
    assert any("slug must be a string" in e for e in errs)


def test_structural_validate_index_bad_mode_and_status() -> None:
    base = {
        "schema_version": "1",
        "slug": "x",
        "mode": "bad",
        "source": "path:.",
        "question": "q",
        "lenses": ["a"],
        "findings": [],
        "curated_count": 0,
        "status": "bad",
    }
    errs = research_cli.structural_validate_index(base)
    assert any("mode must be" in e for e in errs)
    assert any("status must be" in e for e in errs)


def test_structural_validate_index_lenses_and_findings() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": "x",
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": [],
            "findings": "not-list",
            "curated_count": -1,
            "status": "init",
        }
    )
    assert any("lenses must be" in e for e in errs)
    assert any("findings must be an array" in e for e in errs)
    assert any("curated_count" in e for e in errs)


def test_structural_validate_index_findings_row_errors() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": "x",
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": ["a"],
            "findings": [{"id": "", "lens": "a", "path": "p", "summary": "s", "confidence": "bad"}],
            "curated_count": 0,
            "status": "init",
        }
    )
    assert any("findings[0].id" in e for e in errs)
    assert any("confidence must be" in e for e in errs)


def test_structural_validate_index_rounds_bounds() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": "x",
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": ["a"],
            "findings": [],
            "curated_count": 0,
            "status": "init",
            "rounds_completed": 99,
            "rounds_max": 0,
        }
    )
    assert any("rounds_completed must be" in e for e in errs)
    assert any("rounds_max must be" in e for e in errs)


def test_init_missing_templates(tmp_path: Path) -> None:
    class NS:
        directory = tmp_path
        slug = "x"
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


def test_init_pack_exists_without_force(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    pack = tmp_path / "_research_results" / "sources" / "dup"
    pack.mkdir(parents=True)

    class NS:
        directory = tmp_path
        slug = "dup"
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


def test_init_bad_mode(tmp_path: Path) -> None:
    _seed_templates(tmp_path)

    class NS:
        directory = tmp_path
        slug = "x"
        source = "path:."
        question = "q"
        lenses = "architecture"
        consumers = "implementer"
        mode = "invalid"
        rounds_max = 6
        notes = ""
        brief = None
        force = False

    assert research_cli.cmd_research_init(NS()) == research_cli.EXIT_USAGE


def test_init_from_brief_file(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    brief_path = tmp_path / "custom-brief.md"
    brief_path.write_text("# Custom brief\n", encoding="utf-8")

    class NS:
        directory = tmp_path
        slug = "brief-pack"
        source = "path:."
        question = "q"
        lenses = "architecture"
        consumers = "implementer"
        mode = "external"
        rounds_max = 6
        notes = ""
        brief = brief_path
        force = False

    assert research_cli.cmd_research_init(NS()) == 0
    assert "Custom brief" in (tmp_path / "_research_results" / "sources" / "brief-pack" / "BRIEF.md").read_text()


def test_init_brief_missing(tmp_path: Path) -> None:
    _seed_templates(tmp_path)

    class NS:
        directory = tmp_path
        slug = "x"
        source = "path:."
        question = "q"
        lenses = "architecture"
        consumers = "implementer"
        mode = "external"
        rounds_max = 6
        notes = ""
        brief = tmp_path / "missing-brief.md"
        force = False

    assert research_cli.cmd_research_init(NS()) == research_cli.EXIT_USAGE


def test_clone_github_git_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **_kwargs):  # noqa: ANN001
        calls.append(list(cmd))
        dest = Path(cmd[4]) if cmd[0] == "gh" else Path(cmd[-1])
        if cmd[0] == "gh":
            return SimpleNamespace(returncode=1, stdout="", stderr="gh clone failed")
        dest.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(research_cli.subprocess, "run", fake_run)
    ok, how = research_cli._clone_github("octocat/Hello-World", "main", tmp_path / "dest")
    assert ok
    assert how == "git clone"
    assert calls[-1][0] == "git"


def test_clone_github_both_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        research_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="failed"),
    )
    ok, detail = research_cli._clone_github("o/r", None, tmp_path / "dest")
    assert not ok
    assert "git clone failed" in detail


def test_clone_github_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def raise_os(*a, **k):
        raise OSError("no gh")

    monkeypatch.setattr(research_cli.subprocess, "run", raise_os)
    ok, detail = research_cli._clone_github("o/r", None, tmp_path / "dest")
    assert not ok


def test_fetch_missing_pack(tmp_path: Path) -> None:
    class NS:
        directory = tmp_path
        slug = "missing"
        source = "path:."
        force = False

    assert research_cli.cmd_research_fetch(NS()) == research_cli.EXIT_USAGE


def test_fetch_bad_source(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    pack = tmp_path / "_research_results" / "sources" / "x"
    pack.mkdir(parents=True)

    class NS:
        directory = tmp_path
        slug = "x"
        source = ""
        force = False

    assert research_cli.cmd_research_fetch(NS()) == research_cli.EXIT_USAGE


def test_fetch_path_not_found(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    pack = tmp_path / "_research_results" / "sources" / "x"
    pack.mkdir(parents=True)

    class NS:
        directory = tmp_path
        slug = "x"
        source = "path:does-not-exist"
        force = False

    assert research_cli.cmd_research_fetch(NS()) == research_cli.EXIT_FAIL


def test_fetch_github_cache_exists(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "gh-pack"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    cache = tmp_path / "_research_results" / "cache" / slug
    cache.mkdir(parents=True)

    args = SimpleNamespace(
        directory=tmp_path,
        slug=slug,
        source="github:octocat/Hello-World",
        force=False,
    )

    assert research_cli.cmd_research_fetch(args) == research_cli.EXIT_USAGE


def test_fetch_github_clone_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_templates(tmp_path)
    slug = "gh-fail"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    monkeypatch.setattr(research_cli, "_clone_github", lambda *a, **k: (False, "clone failed"))

    args = SimpleNamespace(
        directory=tmp_path,
        slug=slug,
        source="github:octocat/Hello-World",
        force=False,
    )

    assert research_cli.cmd_research_fetch(args) == research_cli.EXIT_FAIL


def test_fetch_github_happy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "gh-ok"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    (pack / "INDEX.json").write_text(
        json.dumps(
            {
                "schema_version": "1",
                "slug": slug,
                "mode": "external",
                "source": "github:octocat/Hello-World",
                "question": "q",
                "lenses": ["architecture"],
                "findings": [],
                "curated_count": 0,
                "status": "init",
            }
        ),
        encoding="utf-8",
    )
    cache = tmp_path / "_research_results" / "cache" / slug
    cache.mkdir(parents=True)
    monkeypatch.setattr(research_cli, "_clone_github", lambda loc, ref, dest: (True, "gh repo clone"))
    monkeypatch.setattr(research_cli, "_git_sha", lambda p: "deadbeef")

    args = SimpleNamespace(
        directory=tmp_path,
        slug=slug,
        source="github:octocat/Hello-World@main",
        force=True,
    )

    assert research_cli.cmd_research_fetch(args) == 0
    assert (pack / "SOURCE.md").is_file()


def test_fetch_corrupt_index_json(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    fixture = tmp_path / "src"
    fixture.mkdir()
    slug = "corrupt-idx"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    (pack / "INDEX.json").write_text("{bad json", encoding="utf-8")

    args = SimpleNamespace(
        directory=tmp_path,
        slug=slug,
        source=f"path:{fixture}",
        force=False,
    )

    assert research_cli.cmd_research_fetch(args) == 0


def test_validate_missing_files(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    pack = tmp_path / "_research_results" / "sources" / "incomplete"
    pack.mkdir(parents=True)
    (pack / "BRIEF.md").write_text("# b\n", encoding="utf-8")

    class NS:
        directory = tmp_path
        slug = "incomplete"

    assert research_cli.cmd_research_validate(NS()) == research_cli.EXIT_FAIL


def test_validate_invalid_json(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "bad-json"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    for name in ("BRIEF.md", "SOURCE.md", "INDEX.json"):
        (pack / name).write_text("x" if name != "INDEX.json" else "{bad", encoding="utf-8")

    args = SimpleNamespace(directory=tmp_path, slug=slug)

    assert research_cli.cmd_research_validate(args) == research_cli.EXIT_FAIL


def test_validate_jsonschema_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "schema-err"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    index = {
        "schema_version": "1",
        "slug": slug,
        "mode": "external",
        "source": "path:.",
        "question": "q",
        "lenses": ["architecture"],
        "findings": [],
        "curated_count": 0,
        "status": "init",
    }
    for name, content in (
        ("BRIEF.md", "# b\n"),
        ("SOURCE.md", "# s\n"),
        ("INDEX.json", json.dumps(index)),
    ):
        (pack / name).write_text(content, encoding="utf-8")

    class FakeSchemaError(Exception):
        pass

    def fake_validate(*a, **k):
        raise FakeSchemaError("schema mismatch")

    fake_jsonschema = SimpleNamespace(validate=fake_validate)
    monkeypatch.setitem(sys.modules, "jsonschema", fake_jsonschema)

    args = SimpleNamespace(directory=tmp_path, slug=slug)

    assert research_cli.cmd_research_validate(args) == research_cli.EXIT_FAIL


def test_validate_complete_missing_map(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "complete-missing"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    index = {
        "schema_version": "1",
        "slug": slug,
        "mode": "external",
        "source": "path:.",
        "question": "q",
        "lenses": ["architecture"],
        "findings": [],
        "curated_count": 0,
        "status": "complete",
    }
    for name, content in (
        ("BRIEF.md", "# b\n"),
        ("SOURCE.md", "# s\n"),
        ("INDEX.json", json.dumps(index)),
    ):
        (pack / name).write_text(content, encoding="utf-8")

    args = SimpleNamespace(directory=tmp_path, slug=slug)

    assert research_cli.cmd_research_validate(args) == research_cli.EXIT_FAIL


def test_validate_complete_ok(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "complete-ok"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    index = {
        "schema_version": "1",
        "slug": slug,
        "mode": "external",
        "source": "path:.",
        "question": "q",
        "lenses": ["architecture"],
        "findings": [],
        "curated_count": 0,
        "status": "complete",
    }
    for name, content in (
        ("BRIEF.md", "# b\n"),
        ("SOURCE.md", "# s\n"),
        ("INDEX.json", json.dumps(index)),
        ("MAP.md", "# m\n"),
        ("CURATED.md", "# c\n"),
        ("AGENT_BRIEF.md", "# a\n"),
    ):
        (pack / name).write_text(content, encoding="utf-8")

    args = SimpleNamespace(directory=tmp_path, slug=slug)

    assert research_cli.cmd_research_validate(args) == 0


def test_parse_source_strips_git_suffix_and_bare_path() -> None:
    kind, loc, _ref = research_cli._parse_source(
        "https://github.com/o/x.git.git.git"
    )
    assert kind == "github" and loc == "o/x.git"
    _kind2, loc2, _ref2 = research_cli._parse_source("/tmp/local")
    assert _kind2 == "path" and loc2 == "/tmp/local"


def test_git_sha_success_and_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    def ok_run(*a, **k):
        return SimpleNamespace(returncode=0, stdout="abc123\n", stderr="")

    monkeypatch.setattr(research_cli.subprocess, "run", ok_run)
    assert research_cli._git_sha(repo) == "abc123"

    def fail_run(*a, **k):
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(research_cli.subprocess, "run", fail_run)
    assert research_cli._git_sha(repo) is None


def test_structural_validate_index_invalid_slug_string() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": "INVALID",
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": ["a"],
            "findings": [],
            "curated_count": 0,
            "status": "init",
        }
    )
    assert any("slug must match" in e for e in errs)


def test_structural_validate_index_findings_not_object() -> None:
    errs = research_cli.structural_validate_index(
        {
            "schema_version": "1",
            "slug": "x",
            "mode": "external",
            "source": "path:.",
            "question": "q",
            "lenses": ["a"],
            "findings": ["bad"],
            "curated_count": 0,
            "status": "init",
        }
    )
    assert any("findings[0] must be an object" in e for e in errs)


def test_fetch_bad_slug() -> None:
    args = SimpleNamespace(directory=Path("/tmp"), slug="BAD", source="path:.", force=False)
    assert research_cli.cmd_research_fetch(args) == research_cli.EXIT_USAGE


def test_validate_bad_slug() -> None:
    args = SimpleNamespace(directory=Path("/tmp"), slug="BAD")
    assert research_cli.cmd_research_validate(args) == research_cli.EXIT_USAGE


def test_clone_github_rmtree_before_git(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "stale").write_text("x", encoding="utf-8")

    def fake_run(cmd, **_kwargs):  # noqa: ANN001
        if cmd[0] == "gh":
            return SimpleNamespace(returncode=1, stdout="", stderr="gh fail")
        Path(cmd[-1]).mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(research_cli.subprocess, "run", fake_run)
    ok, _how = research_cli._clone_github("o/r", None, dest)
    assert ok


def test_fetch_without_index_file(tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    fixture = tmp_path / "src"
    fixture.mkdir()
    slug = "no-index"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)

    args = SimpleNamespace(
        directory=tmp_path,
        slug=slug,
        source=f"path:{fixture}",
        force=False,
    )
    assert research_cli.cmd_research_fetch(args) == 0
    assert (pack / "INDEX.json").is_file()


def test_validate_jsonschema_import_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_templates(tmp_path)
    slug = "no-jsonschema"
    pack = tmp_path / "_research_results" / "sources" / slug
    pack.mkdir(parents=True)
    index = {
        "schema_version": "1",
        "slug": slug,
        "mode": "external",
        "source": "path:.",
        "question": "q",
        "lenses": ["architecture"],
        "findings": [],
        "curated_count": 0,
        "status": "init",
    }
    for name, content in (
        ("BRIEF.md", "# b\n"),
        ("SOURCE.md", "# s\n"),
        ("INDEX.json", json.dumps(index)),
    ):
        (pack / name).write_text(content, encoding="utf-8")

    real_import = __import__

    def fake_import(name, *args, **kwargs):  # noqa: ANN001
        if name == "jsonschema":
            raise ImportError("no jsonschema")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    args = SimpleNamespace(directory=tmp_path, slug=slug)
    assert research_cli.cmd_research_validate(args) == 0

