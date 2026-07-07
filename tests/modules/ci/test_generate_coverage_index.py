"""
File: test_generate_coverage_index.py
Path: tests/modules/ci/test_generate_coverage_index.py
Role: Tests for coverage-index generator script.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/ci/generate_coverage_index.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "ci" / "generate_coverage_index.py"


def _load_gen():
    if "generate_coverage_index" in sys.modules:
        del sys.modules["generate_coverage_index"]
    spec = importlib.util.spec_from_file_location("generate_coverage_index", GEN_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_markdown_reports_full_coverage() -> None:
    mod = _load_gen()
    data = {
        "files": {
            ".ai_infra/paths.py": {"summary": {"num_statements": 10, "missing_lines": 0}},
            "cursor_workflow/cli.py": {"summary": {"num_statements": 5, "missing_lines": 0}},
        }
    }
    text = mod.render_markdown(REPO_ROOT, data, test_count=605)
    assert "605 passed" in text
    assert "Total statements: `15`" in text
    assert "100.00%" in text
    assert "## Module Coverage" in text


def test_render_markdown_lists_files_below_threshold() -> None:
    mod = _load_gen()
    data = {
        "files": {
            ".ai_infra/paths.py": {"summary": {"num_statements": 10, "missing_lines": 5}},
        }
    }
    text = mod.render_markdown(REPO_ROOT, data, test_count=1)
    assert ".ai_infra/paths.py" in text
    assert "50.00%" in text


def test_module_key_branches() -> None:
    mod = _load_gen()
    assert mod._module_key("cursor_workflow/cli.py") == "cursor_workflow"
    assert mod._module_key(".ai_infra/scripts/pr/foo.py") == ".ai_infra/scripts/pr"
    assert mod._module_key(".ai_infra/install/cursor_workflow/x.py") == ".ai_infra/install/cursor_workflow"
    assert mod._module_key(".ai_infra/mcp_servers/workflow_mcp/x.py") == ".ai_infra/mcp_servers/workflow_mcp"
    assert mod._module_key(".ai_infra/bootstrap.py") == ".ai_infra/bootstrap.py"
    assert mod._module_key("other/foo.py") == "other/foo.py"


def test_main_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_gen()
    cov = {
        "files": {
            ".ai_infra/paths.py": {"summary": {"num_statements": 2, "missing_lines": 0}},
        }
    }
    cov_file = tmp_path / "coverage.json"
    cov_file.write_text(json.dumps(cov), encoding="utf-8")

    def _fake_run(cmd, cwd, capture_output, text):  # noqa: ANN001
        if "--collect-only" in cmd:
            return SimpleNamespace(returncode=0, stdout="605 tests collected in 0.1s\n", stderr="")
        if "--cov-report=json" in cmd:
            (Path(cwd) / "coverage.json").write_text(json.dumps(cov), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)
    out = tmp_path / "out" / "coverage-index.md"
    code = mod.main(["--directory", str(tmp_path), "--output", str(out)])
    assert code == 0
    assert out.is_file()
    assert "Total statements" in out.read_text(encoding="utf-8")


def test_collect_test_count_parses_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_gen()

    def _ok(*_a, **_k):  # noqa: ANN001
        return SimpleNamespace(returncode=0, stdout="609 tests collected in 0.2s\n", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", _ok)
    assert mod._collect_test_count(tmp_path) == 609


def test_aggregate_skips_out_of_scope_files() -> None:
    mod = _load_gen()
    data = {
        "files": {
            "tests/foo.py": {"summary": {"num_statements": 99, "missing_lines": 0}},
            ".ai_infra/paths.py": {"summary": {"num_statements": 1, "missing_lines": 0}},
        }
    }
    total, miss, count, _mods = mod._aggregate(data)
    assert total == 1
    assert miss == 0
    assert count == 2


def test_main_returns_one_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_gen()

    def _fail(*_a, **_k):  # noqa: ANN001
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(mod.subprocess, "run", _fail)
    code = mod.main(["--directory", str(tmp_path)])
    assert code == 1
