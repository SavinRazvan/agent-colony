<!--
File: continuity-index.md
Path: .ai_infra/templates/local-workspace/exemplars/continuity-index.md
Role: Exemplar for install → .local/index-and-planning/history/continuity-index.md
Used By:
 - Agent slice close (board SSOT + local artifact cross-index)
Depends On:
 - token-efficiency.md, project-board-collaboration.md
Notes:
 - Rolling local index (≥3 calendar days). Board Notes keep full card lifetime.
-->

# Continuity index (rolling ≥3 days)

Local cross-index between **board item_ids** and **local artifact paths** touched during recent slices.
Board card **Notes** (timestamped by CLI) retain the full card lifetime from day 1; this file is a
thin local resume cache only.

**Retention:** keep entries for **≥3 calendar days** (UTC date on each row). On update, drop rows
older than three days unless still referenced in `change-index.md`.

**Row format:** `YYYY-MM-DDTHH:MM:SSZ · item_id=<PVTI_…> · paths=<comma-separated> · agent=<name> · note=<short>`

(none yet)
