"""
File: __main__.py
Path: agent_colony/__main__.py
Role: Entrypoint for python -m agent_colony.
Used By:
 - Makefile, README install examples
Depends On:
 - agent_colony/cli.py
"""

from agent_colony.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
