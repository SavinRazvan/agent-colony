# `.local/canvases/` (session evidence)

Gitignored ephemeral canvases saved from Cursor managed path or agent analysis.

- **Product / onboarding canvases:** edit `canvases/*.canvas.tsx` in the repo (git SSOT).
- **IDE preview:** `python3 -m agent_colony canvas sync --name <base>`
- **Save ephemeral:** `python3 -m agent_colony canvas save --slug <slug>`

See ADR-010 and `.cursor/skills/canvas-artifacts/SKILL.md`.
