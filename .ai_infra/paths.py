"""
File: paths.py
Path: .ai_infra/paths.py
Role: Resolve kit paths under .ai_infra/ for kit repo and installed consumer projects.
Used By:
 - .ai_infra/scripts/install/scaffold.py
 - .ai_infra/scripts/architecture/check_governance_consistency.py
 - .ai_infra/bootstrap.py
Depends On:
 - pathlib
Notes:
 - Kit root is parent of .ai_infra/. Editable install via pyproject; scripts may use bootstrap + `import paths`.
"""

from __future__ import annotations

from pathlib import Path

_AI_INFRA_DIR = Path(__file__).resolve().parent
_KIT_ROOT = _AI_INFRA_DIR.parent
_AI_INFRA_MARKER = ".ai_infra"


def kit_root() -> Path:
    return _KIT_ROOT


def ai_infra_dir(root: Path | None = None) -> Path:
    base = root or _KIT_ROOT
    canonical = base / _AI_INFRA_MARKER
    if canonical.is_dir():
        return canonical
    raise FileNotFoundError(f"not found: {canonical}")


def kit_root_from_script(script_path: str | Path) -> Path:
    """Infer project root from a script under .ai_infra/."""
    resolved = Path(script_path).resolve()
    parts = resolved.parts
    if _AI_INFRA_MARKER in parts:
        return Path(*parts[: parts.index(_AI_INFRA_MARKER)])
    raise FileNotFoundError(f"cannot infer kit root from {resolved}")


def ui_local_workspace(root: Path | None = None) -> Path:
    base = root or _KIT_ROOT
    path = ai_infra_dir(base) / "templates" / "local-workspace"
    if path.is_dir():
        return path
    raise FileNotFoundError(f"not found: {path}")


def user_settings_templates(root: Path | None = None) -> Path:
    """Exemplars copied into `.local/user_settings/` at scaffold."""
    base = root or _KIT_ROOT
    path = ai_infra_dir(base) / "templates" / "user-settings" / "exemplars"
    if path.is_dir():
        return path
    raise FileNotFoundError(f"not found: {path}")


def mcp_package_dir(root: Path | None = None) -> Path:
    base = root or _KIT_ROOT
    path = ai_infra_dir(base) / "mcp_servers" / "workflow_mcp"
    if path.is_dir():
        return path
    raise FileNotFoundError(f"not found: {path}")


def docs_dir(name: str, root: Path | None = None) -> Path:
    base = root or _KIT_ROOT
    path = ai_infra_dir(base) / "docs" / name
    if path.is_dir():
        return path
    raise FileNotFoundError(f"not found: {path}")


def scripts_dir(name: str, root: Path | None = None) -> Path:
    base = root or _KIT_ROOT
    path = ai_infra_dir(base) / "scripts" / name
    if path.is_dir():
        return path
    raise FileNotFoundError(f"not found: {path}")


def pr_script(name: str, root: Path | None = None) -> Path:
    """Resolve a file under .ai_infra/scripts/pr/."""
    path = scripts_dir("pr", root) / name
    if path.is_file():
        return path
    raise FileNotFoundError(f"not found: {path}")


def architecture_script(name: str, root: Path | None = None) -> Path:
    """Resolve a file under .ai_infra/scripts/architecture/."""
    path = scripts_dir("architecture", root) / name
    if path.is_file():
        return path
    raise FileNotFoundError(f"not found: {path}")


def pr_script_rel(name: str) -> str:
    """Relative path for agent prose templates."""
    return f".ai_infra/scripts/pr/{name}"


def resolve_project_python(root: Path | None = None) -> str:
    """Return `.venv/bin/python` when present so gates/pytest work without manual activate."""
    import sys

    base = (root or _KIT_ROOT).resolve()
    venv_py = base / ".venv" / "bin" / "python"
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable
