---
name: canvas-artifacts
description: Three-tier canvas and plan snapshot workflow via agent_colony canvas/plan CLI (ADR-010).
---

# Canvas and plan artifacts (Pattern A)

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

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
- `sync --all` requires `--force`.

## Plan CLI

```bash
python3 -m agent_colony plan snapshot --slug slice-170 --agent implementer --board-item PVTI_xxx
python3 -m agent_colony plan list
python3 -m agent_colony plan open --slug slice-170
python3 -m agent_colony plan open --slug slice-170 --force
python3 -m agent_colony plan snapshot --slug my-plan --from cursor-plan:my-plan.plan.md
```

Never treat `.local/plans/` as active backlog under `board_only`.

## Agent rituals

1. **Product canvas:** edit repo → `canvas sync --name …` → Open Canvas in IDE.
2. **Ephemeral canvas:** write via Cursor canvas skill → `canvas save --slug …`.
3. **Plan mode exit:** `plan snapshot --slug …` with board item id when known.

### Consumer plans (Path A)

Agents **never depend on** the IDE Build button:

1. `plan list` — discover slugs
2. Read `.local/plans/<latest>-<slug>.plan.md` (+ `.meta.yaml`)
3. Execute todos as implementer
4. **Human-only:** `plan open --slug …` → Plans UI → Build
5. After plan-mode work: `plan snapshot --from cursor-plan:…`

`plan snapshot` preserves YAML frontmatter (`name` / `overview` / `todos`) for Build.

**Indexing:** only `*.plan.md` (+ `*.meta.yaml`) in `plan list`. Orphans → re-snapshot or remove.

Canon: [ADR-010](../../.ai_infra/docs/decisions/ADR-010-canvas-plan-local-artifacts.md)
