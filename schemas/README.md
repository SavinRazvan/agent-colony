<!--
File: README.md
Path: schemas/README.md
Role: JSON schema stubs for workflow kit metadata (not agent runtime config).
Used By:
 - MCP inventory evolution
 - docs/roadmap alignment
Depends On:
 - .ai_infra/scripts/pr/prepare.py (GATES authoritative)
Notes:
 - Pattern A: gates are hardcoded in prepare.py; schema documents shape only.
-->

# Schemas

| File | Purpose |
|------|---------|
| [`gate.json`](gate.json) | Shape of one `GATES` entry (string argv array) |

Gate **order and commands** live only in `.ai_infra/scripts/pr/prepare.py`.
