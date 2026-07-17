"""
File: test_verify_all.py
Path: tests/modules/architecture_scripts/test_verify_all.py
Role: Coverage for the maintainer verify-all matrix runner (verify_all.py).
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/verify_all.py
"""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ARCH_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "architecture"
if str(ARCH_DIR) not in sys.path:
    sys.path.insert(0, str(ARCH_DIR))

import verify_all as va  # noqa: E402


def _fake_run_factory(exit_codes: dict[str, int] | None = None):
    exit_codes = exit_codes or {}

    def _fake_run(cmd, cwd=None, capture_output=None, text=None):  # noqa: ANN001
        name = cmd[-1] if cmd else ""
        code = 0
        for key, value in exit_codes.items():
            if key in " ".join(str(c) for c in cmd):
                code = value
        return SimpleNamespace(stdout=f"ran {name}\n", stderr="", returncode=code)

    return _fake_run


def test_run_step_captures_output_and_exit_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        va.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="out\n", stderr="err\n", returncode=3),
    )
    result = va._run_step("demo", ["true"], tmp_path)
    assert result.exit_code == 3
    assert "out" in result.output and "err" in result.output


def test_run_verify_all_includes_ci_seed_when_planning_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(va.subprocess, "run", _fake_run_factory())
    results = va.run_verify_all(tmp_path, sys.executable)
    names = [r.name for r in results]
    assert "ci-seed" in names
    assert names[0] == "ci-seed"
    assert "sync-plugin" in names
    assert "contributors-validate" in names


def test_run_verify_all_skips_ci_seed_when_planning_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    planning = tmp_path / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    monkeypatch.setattr(va.subprocess, "run", _fake_run_factory())
    results = va.run_verify_all(tmp_path, sys.executable)
    names = [r.name for r in results]
    assert "ci-seed" not in names
    assert names[0] == "sync-plugin"


def test_format_report_marks_failures_and_appends_output() -> None:
    results = [
        va.StepResult(name="ok-step", command=["true"], exit_code=0, output=""),
        va.StepResult(name="bad-step", command=["false"], exit_code=1, output="boom details"),
    ]
    report = va.format_report(results)
    assert "[PASS] ok-step" in report
    assert "[FAIL] bad-step" in report
    assert "boom details" in report
    assert "summary: failed=1 total=2" in report


def test_exit_code_for_all_pass() -> None:
    results = [va.StepResult(name="a", command=[], exit_code=0, output="")]
    assert va.exit_code_for(results) == 0


def test_exit_code_for_any_failure() -> None:
    results = [
        va.StepResult(name="a", command=[], exit_code=0, output=""),
        va.StepResult(name="b", command=[], exit_code=1, output=""),
    ]
    assert va.exit_code_for(results) == 1


def test_write_preflight_json_truncates_long_output(tmp_path: Path) -> None:
    long_output = "x" * 3000
    results = [va.StepResult(name="a", command=["cmd"], exit_code=1, output=long_output)]
    out = tmp_path / "preflight" / "verify-all.json"
    va.write_preflight_json(results, out)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["command"] == "python -m cursor_workflow verify all"
    assert len(payload["steps"][0]["output_tail"]) == 2000
    assert payload["exit_code"] == 1


def test_write_preflight_json_empty_output(tmp_path: Path) -> None:
    results = [va.StepResult(name="a", command=["cmd"], exit_code=0, output="")]
    out = tmp_path / "preflight" / "verify-all.json"
    va.write_preflight_json(results, out)
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["steps"][0]["output_tail"] == ""


def test_main_text_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(va.subprocess, "run", _fake_run_factory())
    code = va.main(["--directory", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "summary: failed=0" in captured.out


def test_main_json_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(va.subprocess, "run", _fake_run_factory())
    code = va.main(["--directory", str(tmp_path), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["exit_code"] == code
    assert "steps" in payload


def test_main_writes_preflight_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(va.subprocess, "run", _fake_run_factory({"gates": 1}))
    out = tmp_path / "preflight" / "verify-all.json"
    code = va.main(["--directory", str(tmp_path), "--preflight-out", str(out)])
    assert code == 1
    assert out.is_file()


def test_main_guard_via_runpy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(va.subprocess, "run", _fake_run_factory())
    monkeypatch.setattr(sys, "argv", ["verify_all.py", "--directory", str(tmp_path)])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(ARCH_DIR / "verify_all.py"), run_name="__main__")
    assert exc_info.value.code == 0
