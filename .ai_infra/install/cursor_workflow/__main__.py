"""
File: __main__.py
Path: cursor_workflow/__main__.py
Role: Entrypoint for python -m cursor_workflow.
Used By:
 - Makefile, README install examples
Depends On:
 - cursor_workflow/cli.py
"""

from cursor_workflow.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
