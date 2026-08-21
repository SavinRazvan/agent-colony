<!--
File: asd-ste100-prose.md
Path: .ai_infra/docs/operations/asd-ste100-prose.md
Role: Free-path Use ASD-STE100 prose guide for agent-facing instructions (token efficiency research).
Used By:
 - .cursor/agents/*.md
 - .cursor/skills/*
 - token-efficiency.md
 - AGENTS.md
Depends On:
 - token-efficiency.md
Notes:
 - Inspired by ASD-STE100 writing principles. No ASD dictionary. No purchase. Not a compliance claim.
-->

# Use ASD-STE100

**Mandatory for agents.** Write instructions, Notes, and handoffs with this guide.

Inspired by [ASD-STE100](https://asd-ste100.org/) writing principles. This kit ships a **free** guide only.

| Do | Do not |
|----|--------|
| Follow this file | Buy or license ASD materials for this kit |
| Use **kit vocabulary** below | Embed ASD’s dictionary in the repo |
| Say *inspired by ASD-STE100* | Claim *ASD-STE100 compliant* |

Research goal: clearer prose → fewer tokens → measure before/after byte and line counts.

## Writing rules (free principles)

1. Use short sentences. Prefer under 20 words.
2. Put one instruction in each bullet.
3. Use active voice. Prefer imperatives: `Run project entry.`
4. Give each word one meaning in this kit (see vocabulary).
5. Link to skills or CLI. Do not paste long procedures.
6. Prefer tables for commands.
7. Say *prepare gates green* or paste failing stderr only. Do not paste full gate lists.

## Kit vocabulary (ours — not ASD’s dictionary)

| Term | Meaning | Do not also say |
|------|---------|-----------------|
| **Use ASD-STE100** | Follow this file | “STE style” without this link |
| Entry | `python -m agent_colony project entry` | Unfiltered `list` / full `export` as default |
| Claim | `project claim --last --agent <id>` | Vague “take the card” |
| Handoff | `project handoff --last …` | Separate Status + Notes as the default recipe |
| Gates green | `prepare.py` passed | Pasting full `GATES` / gate subprocess lists |
| Board SSOT | GitHub Project writable Status when enabled | Local tracker Status under `board_only` |
| Tier-1 | Status, Priority, Size, Estimate, dates, Assignee, PR link | “All the fields” without the skill |
| EXIT_QUEUED | Exit code 6 — outbox; flush later | Retry loops on GraphQL throttle |

## When agents write

| Surface | Rule |
|---------|------|
| Agent cards | Keep Anchors short. Point here + `token-efficiency.md`. |
| Skills (`.cursor/skills/`) | Procedure lives in the skill. Cards link to sections. |
| Maintainer slash skills (`.agents/skills/`) | One command per step; link `pr-workflow` for detail. |
| Board Notes | Attributed one-liners. No gate dumps. |
| Chat handoff | One line: Status · next · Tasks `[P…]` |

## Related

- [token-efficiency.md](token-efficiency.md) — read/write contract
- [board-ssot skill](../../../.cursor/skills/board-ssot/SKILL.md) — Tier-1 and Continuation
- Official standard (reference only): [asd-ste100.org](https://asd-ste100.org/)
