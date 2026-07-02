<!--
File: logging-and-errors.md
Path: .ai_infra/docs/operations/logging-and-errors.md
Role: Logging and error-handling guidance for kit scripts and consumer projects.
Used By:
 - Implementer orientation
Depends On:
 - .ai_infra/scripts/pr/prepare.py
Notes:
 - Kit scripts use subprocess exit codes; consumers add app logging in their own codebases.
-->

# Logging and error handling (MAS Workflow Kit)

## Kit scripts

- PR workflow scripts (`prepare.py`, `merge.py`, etc.) return non-zero exit codes on failure.
- Capture stderr from gate subprocesses; do not swallow failures in agent handoffs.
- Use `python .ai_infra/scripts/architecture/check_governance_consistency.py` after policy edits.

## Consumer projects

- Add structured logging in **your application code** — not in universal agent prose.
- Protect secrets: `.env` per `local-artifact-protection.mdc`.
- For product overlays, follow overlay-specific observability docs when installed under `overlays/docs/`.

## Agent handoffs

- Report *prepare gates green* or paste **failing command + stderr** only.
- Do not duplicate full gate output in `updates-log.md`.
