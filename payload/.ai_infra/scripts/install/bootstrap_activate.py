#!/usr/bin/env python3
"""
File: bootstrap_activate.py
Path: .ai_infra/scripts/install/bootstrap_activate.py
Role: Zero-dep first-install activate from Cursor plugin payload (no agent_colony on PYTHONPATH).
Used By:
 - .cursor/skills/workflow-activate/SKILL.md
 - consumer-quickstart.md § First activate troubleshooting
Depends On:
 - Sibling payload tree (.ai_infra/manifest.yaml) or discover_cursor_plugin_payload
Notes:
 - Run as: python3 <payload>/.ai_infra/scripts/install/bootstrap_activate.py --directory <app>
 - Or from kit-dev: python3 .ai_infra/scripts/install/bootstrap_activate.py --directory <app>
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _payload_from_this_script() -> Path | None:
    """Resolve payload/ or kit root from this file's location under .ai_infra/scripts/install/."""
    here = Path(__file__).resolve()
    # .../<root>/.ai_infra/scripts/install/bootstrap_activate.py → root = parents[3]
    try:
        root = here.parents[3]
    except IndexError:
        return None
    nested = root / "payload"
    if (nested / ".ai_infra" / "manifest.yaml").is_file():
        return nested
    if (root / ".ai_infra" / "manifest.yaml").is_file():
        return root
    return None


def _load_activate_cli(payload: Path):
    cli_path = payload / ".ai_infra" / "install" / "agent_colony" / "activate_cli.py"
    if not cli_path.is_file():
        raise FileNotFoundError(f"activate_cli.py missing under {payload}")
    # Ensure paths.py (sibling of install/) is importable for kit_root().
    ai_infra = str(payload / ".ai_infra")
    if ai_infra not in sys.path:
        sys.path.insert(0, ai_infra)
    pkg = str(payload / ".ai_infra" / "install" / "agent_colony")
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    spec = importlib.util.spec_from_file_location("activate_cli_bootstrap", cli_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {cli_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap Agent Colony activate from plugin payload (first install)."
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("."),
        help="Consumer app workspace (default: cwd)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional payload/ or kit root (default: auto-discover)",
    )
    parser.add_argument("--profile", default="with_mcp", choices=("default", "with_mcp"))
    parser.add_argument("--no-venv", action="store_true", help="Skip .venv creation")
    parser.add_argument("--no-verify", action="store_true", help="Skip post-install verify gates")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    payload = args.source
    if payload is not None:
        payload = payload.resolve()
        if (payload / "payload" / ".ai_infra" / "manifest.yaml").is_file():
            payload = payload / "payload"
        elif not (payload / ".ai_infra" / "manifest.yaml").is_file():
            print(f"bootstrap_activate: FAIL — no manifest under {payload}", file=sys.stderr)
            return 1
    else:
        payload = _payload_from_this_script()
        if payload is None:
            # Late import after path setup is impossible — duplicate tiny discover here.
            home = Path.home()
            plugins = home / ".cursor" / "plugins"
            found: list[Path] = []
            if plugins.is_dir():
                for pattern in (
                    "cache/agent-colony/agent-colony/*/payload",
                    "cache/agent-colony/*/payload",
                ):
                    for match in plugins.glob(pattern):
                        if (match / ".ai_infra" / "manifest.yaml").is_file():
                            found.append(match.resolve())
            if found:
                payload = max(set(found), key=lambda p: p.stat().st_mtime)

    if payload is None:
        print(
            "bootstrap_activate: FAIL — could not find plugin payload. "
            "Run /add-plugin https://github.com/SavinRazvan/agent-colony first, "
            "or pass --source <path-to-payload>.",
            file=sys.stderr,
        )
        return 1

    activate_cli = _load_activate_cli(payload)
    ns = argparse.Namespace(
        directory=args.directory.resolve(),
        source=payload,
        profile=args.profile,
        with_venv=not args.no_venv,
        with_mcp_json=True,
        verify=not args.no_verify,
        force=bool(args.force),
        allow_settings_pending=True,
    )
    print(f"bootstrap_activate: source={payload}")
    return int(activate_cli.cmd_activate(ns))


if __name__ == "__main__":
    raise SystemExit(main())
