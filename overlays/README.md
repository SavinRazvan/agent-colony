# Project overlays

**Use ASD-STE100:** [`.ai_infra/docs/operations/asd-ste100-prose.md`](../.ai_infra/docs/operations/asd-ste100-prose.md)

Per-project rules and optional docs that **extend** the universal **Agent Colony** — not part of core.

## Convention

| Path | Purpose |
|------|---------|
| `overlays/rules/*.mdc` | Product- or domain-specific Cursor rules (install → `.cursor/rules/`) |
| `overlays/docs/` | Optional ops docs merged into project `docs/` at install |

**Kit-dev** ships **7** rules in `.cursor/rules/` (6 universal + `project-ssot-precedence.mdc`). Consumer activate copies the same **7** from `payload/.cursor/rules/`. Add app-domain `.mdc` files here when needed.

## Install

Copy overlay files into the target project:

```bash
cp overlays/rules/*.mdc /path/to/project/.cursor/rules/
```

Customize `.ai_infra/scripts/pr/prepare.py` `resolve_gates()` once. Document extra gates in this README. Say *prepare gates green* — do not paste full gate lists.

## This directory in the kit repo

- `overlays/rules/` — ships **`project-ssot-precedence.mdc`** (keep aligned with `.cursor/rules/`).
- [`project-rules/`](../project-rules/) — deprecated alias; use `overlays/rules/`.

## Anti-patterns

- Do not put product rules in universal `.cursor/rules/` in this product repo.
- Do not duplicate gate lists — point to `prepare.py` `resolve_gates()`.
- Do not treat overlays as agent runtime config (Pattern A: scripts).

See [consumer-quickstart.md](../.ai_infra/docs/operations/consumer-quickstart.md) and [IMPLEMENTATION-STATUS.md](../.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md).
