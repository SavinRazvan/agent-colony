"""
File: bootstrap.py
Path: .ai_infra/bootstrap.py
Role: Add .ai_infra to sys.path so scripts can `import paths` without a pip package.
Used By:
 - .ai_infra/scripts/install/scaffold.py
 - cursor_workflow/cli.py
 - tests
Depends On:
 - pathlib
 - sys
"""

from __future__ import annotations

import sys
from pathlib import Path

_AI_INFRA_MARKER = ".ai_infra"


def ensure_paths_import(anchor: str | Path) -> Path:
    """Locate .ai_infra/paths.py above anchor; return kit root."""
    resolved = Path(anchor).resolve()
    for candidate in (resolved, *resolved.parents):
        ai_infra = candidate / _AI_INFRA_MARKER
        if (ai_infra / "paths.py").is_file():
            kit = candidate
            ai_str = str(ai_infra)
            if ai_str not in sys.path:
                sys.path.insert(0, ai_str)
            return kit
    raise RuntimeError(f"{_AI_INFRA_MARKER}/paths.py not found above {resolved}")
