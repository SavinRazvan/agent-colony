---
name: canvas-artifacts
description: Three-tier canvas and plan snapshot workflow via agent_colony canvas/plan CLI (ADR-010).
---

# Canvas and plan artifacts (Pattern A)

## When

- Editing kit canvases in `canvases/` and needing IDE preview
- Saving ephemeral analysis canvases for history
- Exiting Plan mode and archiving a dated snapshot

## Tiers (do not dual-write)

| Tier | Path | Role |
|------|------|------|
| Git SSOT | `canvases/*.canvas.tsx` | Product / onboarding docs |
| Cursor managed | `~/.cursor/projects/<workspace>/canvases/` | IDE render bridge only |
| Local evidence | `.local/canvases/` | Session canvases (gitignored) |
| Live plan | Board card body or `plan.md` (offline) | Writable SSOT |
| Plan history | `.local/plans/<date>-<slug>.plan.md` | Snapshots only |

## Canvas CLI

```bash
python3 -m agent_colony canvas doctor
python3 -m agent_colony canvas list --tier all
python3 -m agent_colony canvas sync --name mcp-onboarding
python3 -m agent_colony canvas sync --missing
python3 -m agent_colony canvas save --slug billing-review --agent implementer
```

- Use `export default function NameCanvas()` in `.canvas.tsx` files.
- `sync --all` requires `--force` (avoid silent overwrite).

## Plan CLI

```bash
python3 -m agent_colony plan snapshot --slug slice-170 --agent implementer --board-item PVTI_xxx
python3 -m agent_colony plan list
python3 -m agent_colony plan open --slug slice-170          # human Build bridge
python3 -m agent_colony plan open --slug slice-170 --force  # overwrite Cursor twin
python3 -m agent_colony plan snapshot --slug my-plan --from cursor-plan:my-plan.plan.md
```

Never treat `.local/plans/` as active backlog under `board_only`.

## Agent rituals

1. **Product canvas:** edit repo → `canvas sync --name …` → Open Canvas in IDE.
2. **Ephemeral canvas:** write via Cursor canvas skill to managed path → `canvas save --slug …`.
3. **Plan mode exit:** `plan snapshot --slug …` with board item id when known.

### Consumer plans (agent build — Path A)

Agents **never depend on** the IDE Build button. Execute from `.local/plans/`:

1. `plan list` — discover slugs under `.local/plans/`
2. Read `.local/plans/<latest>-<slug>.plan.md` (+ sibling `.meta.yaml`)
3. Execute todos / acceptance as implementer (no Build required)
4. **Human-only:** `plan open --slug …` → Plans UI → Build (copies latest snapshot to `~/.cursor/plans/<slug>.plan.md`)
5. After plan-mode work in Cursor: `plan snapshot --from cursor-plan:…` to re-anchor history in `.local/plans/`

`plan snapshot` from a Cursor plan preserves YAML frontmatter (`name` / `overview` / `todos`) needed for Build.

**Indexing:** only `*.plan.md` (+ sibling `*.meta.yaml`) appear in `plan list` / `index.md`. Plain `.md` files dropped under `.local/plans/` are orphans — remove or re-snapshot via `plan snapshot --from <path>`.

Canon: [ADR-010](../../.ai_infra/docs/decisions/ADR-010-canvas-plan-local-artifacts.md)
