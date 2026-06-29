---
name: {{AGENT_ID}}
model: auto
description: {{ONE_LINE_DESCRIPTION}}
---

# {{AGENT_TITLE}}

## Anchor (mandatory)

**Entry:** Read `.local/index-and-planning/current/session-pointer.md`, then {{SKILL_OR_DOC_PATH}}.

**Exit:** Update `session-pointer.md`, append `change-index.md` (Agent: `{{AGENT_ID}}`), one line in `history/updates-log.md`.

## Role

{{FACTUAL_ROLE — what this agent owns and what it must not do}}

## Read first

- `.local/index-and-planning/current/session-pointer.md`
- {{BOUNDED_READ_LIST — max 5 paths}}

## Loop

1. {{Step 1 — procedural}}
2. {{Step 2}}
3. **Verify:** {{script commands only — no invented gates}}

## Boundaries

| Do | Do not |
|----|--------|
| {{allowed}} | {{forbidden — e.g. bypass prepare.py, edit GATES in prose}} |

## Handoff format

{{slice}} • paths • commands PASS/FAIL • next agent

## MCP integration

| Tier | Server | Use when |
|------|--------|----------|
| Kit | `workflow-kit` | {{kit tools}} |
| External | See `.cursor/mcp.registry.yaml` | Only if listed for `{{AGENT_ID}}` |

Before **CallMcpTool**: read tool descriptor schema. Do not invent tool names.
User setup: `.ai_infra/docs/operations/connect-external-mcp.md`
