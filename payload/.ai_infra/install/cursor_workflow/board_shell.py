"""
File: board_shell.py
Path: .ai_infra/install/cursor_workflow/board_shell.py
Role: Load board-shell schema (kit template or local overlay) and compare live views/fields.
Used By:
 - project_handlers.run_board_bootstrap
Depends On:
 - PyYAML (optional soft; falls back to json if schema is .json — YAML preferred)
Notes:
 - Views are desired-state for check/coach only; no view mutations.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

VIEW_N = re.compile(r"^View\s*\d+$", re.IGNORECASE)

_LAYOUT_ALIASES = {
    "BOARD": "BOARD_LAYOUT",
    "BOARD_LAYOUT": "BOARD_LAYOUT",
    "TABLE": "TABLE_LAYOUT",
    "TABLE_LAYOUT": "TABLE_LAYOUT",
    "ROADMAP": "ROADMAP_LAYOUT",
    "ROADMAP_LAYOUT": "ROADMAP_LAYOUT",
}


def project_templates_board_dir(root: Path) -> Path:
    return Path(root).resolve() / ".ai_infra" / "templates" / "project-board"


def resolve_board_shell_schema_path(root: Path) -> Path:
    """Prefer local overlay; else kit template."""
    root = Path(root).resolve()
    overlay = root / ".local" / "user_settings" / "board-shell.schema.yaml"
    if overlay.is_file():
        return overlay
    return project_templates_board_dir(root) / "board-shell.schema.yaml"


def load_board_shell_schema(root: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Return (schema dict, error)."""
    path = resolve_board_shell_schema_path(root)
    if not path.is_file():
        return None, f"board-shell schema missing: {path}"
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML required to load board-shell.schema.yaml"
    try:
        data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        return None, f"invalid board-shell schema YAML: {exc}"
    if not isinstance(data, dict):
        return None, "board-shell schema root must be a mapping"
    return data, None


def normalize_layout(raw: Any) -> str:
    key = str(raw or "").strip().upper().replace(" ", "_")
    return _LAYOUT_ALIASES.get(key, key)


def required_field_names(schema: dict[str, Any]) -> list[str]:
    fields = schema.get("fields") if isinstance(schema.get("fields"), dict) else {}
    required = fields.get("required") if isinstance(fields, dict) else None
    names: list[str] = []
    if isinstance(required, list):
        for item in required:
            if isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]).strip())
            elif isinstance(item, str) and item.strip():
                names.append(item.strip())
    return names


def visible_columns(schema: dict[str, Any]) -> set[str]:
    views = schema.get("views") if isinstance(schema.get("views"), dict) else {}
    cols = views.get("visible_columns") if isinstance(views, dict) else None
    if not isinstance(cols, list):
        return {"Priority", "Size", "Estimate", "Start date"}
    return {str(c).strip() for c in cols if str(c).strip()}


def tier1_column_names(schema: dict[str, Any]) -> set[str]:
    """Columns that must appear on minimum board/table views (subset of visible)."""
    # Agents care about these four; Title/Assignees/Status/Linked PRs usually present.
    wanted = {"Priority", "Size", "Estimate", "Start date"}
    cols = visible_columns(schema)
    return wanted & cols if cols else wanted


def minimum_views(schema: dict[str, Any]) -> list[dict[str, Any]]:
    views = schema.get("views") if isinstance(schema.get("views"), dict) else {}
    minimum = views.get("minimum") if isinstance(views, dict) else None
    if not isinstance(minimum, list):
        return []
    return [v for v in minimum if isinstance(v, dict) and v.get("name")]


def recommended_views(schema: dict[str, Any]) -> list[dict[str, Any]]:
    views = schema.get("views") if isinstance(schema.get("views"), dict) else {}
    recommended = views.get("recommended") if isinstance(views, dict) else None
    if not isinstance(recommended, list):
        return []
    return [v for v in recommended if isinstance(v, dict) and v.get("name")]


def _view_by_name(live_views: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    want = name.strip().casefold()
    want_alnum = re.sub(r"[^a-z0-9]+", "", want)
    for view in live_views:
        got = str(view.get("name") or "").strip()
        if got.casefold() == want:
            return view
        got_alnum = re.sub(r"[^a-z0-9]+", "", got.casefold())
        if want_alnum and got_alnum == want_alnum:
            return view
    return None


def compare_views_to_schema(
    schema: dict[str, Any],
    live_views: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """
    Return (problems, warnings).

    problems: missing minimum view names (FAIL candidates — caller may WARN or FAIL).
    warnings: View N names, missing columns, missing recommended views, layout mismatches.
    """
    problems: list[str] = []
    warnings: list[str] = []
    tier1 = tier1_column_names(schema)

    for view in live_views:
        name = str(view.get("name") or "view").strip() or "view"
        if VIEW_N.match(name):
            warnings.append(
                f"rename default view {name!r} "
                "(schema minimum: Status board / Prioritized backlog)"
            )

    for spec in minimum_views(schema):
        want_name = str(spec.get("name") or "").strip()
        found = _view_by_name(live_views, want_name)
        if found is None:
            problems.append(f"missing minimum view {want_name!r}")
            continue
        want_layout = normalize_layout(spec.get("layout"))
        got_layout = normalize_layout(found.get("layout"))
        if want_layout and got_layout and want_layout != got_layout:
            warnings.append(
                f"view {want_name!r} layout={got_layout} expected={want_layout}"
            )
        layout = got_layout or want_layout
        if layout in {"BOARD_LAYOUT", "TABLE_LAYOUT"}:
            raw_fields = found.get("fields")
            field_list: list[Any] = raw_fields if isinstance(raw_fields, list) else []
            fields = {
                str(n).strip()
                for n in field_list
                if str(n).strip()
            }
            missing = sorted(tier1 - fields)
            if missing:
                warnings.append(
                    f"{want_name} ({layout}) missing columns: {', '.join(missing)}"
                )

    for spec in recommended_views(schema):
        want_name = str(spec.get("name") or "").strip()
        if _view_by_name(live_views, want_name) is None:
            warnings.append(f"recommended view missing: {want_name!r}")

    return problems, warnings


def schema_must_match_prose_names(schema: dict[str, Any]) -> list[str]:
    """Names used in tests/docs sync (minimum + recommended)."""
    names: list[str] = []
    for spec in minimum_views(schema) + recommended_views(schema):
        n = str(spec.get("name") or "").strip()
        if n:
            names.append(n)
    return names
