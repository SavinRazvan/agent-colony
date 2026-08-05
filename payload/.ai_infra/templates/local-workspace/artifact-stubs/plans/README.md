# `.local/plans/` (plan snapshot history)

Dated plan-mode snapshots — **not** live SSOT. Under `board_only`, active plan lives on the GitHub Project card body.

No Build chrome when opening these files directly — agents read and execute from here; humans use `plan open` for IDE Build.

- **Snapshot:** `python3 -m cursor_workflow plan snapshot --slug <slug>`
- **List:** `python3 -m cursor_workflow plan list`
- **Build bridge (human):** `python3 -m cursor_workflow plan open --slug <slug>` (`--force` to overwrite Cursor twin)

See ADR-010 and `.cursor/skills/canvas-artifacts/SKILL.md`.
