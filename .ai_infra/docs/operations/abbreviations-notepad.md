<!--
File: abbreviations-notepad.md
Path: .ai_infra/docs/operations/abbreviations-notepad.md
Role: Glossary for MAS Workflow Kit workflow terminology.
Used By:
 - README.md
 - AGENTS.md
Depends On:
 - .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
Notes:
 - Keep definitions short for newcomers.
-->

# Abbreviations Notepad

Quick reference for reading `README.md`, `AGENTS.md`, and kit docs.

## MAS Workflow Kit flow (plain language)

1. Install kit via `cursor_workflow activate` (plugin) or `cursor_workflow install` (kit clone).
2. Agents read `.local/` trackers (`session-pointer.md` → `plan.md` → `work-tracker.md`).
3. Maintainer PR workflow runs via `.ai_infra/scripts/pr/*` (Pattern A).
4. Optional MCP (`workflow-kit`) wraps the same scripts.

## Core abbreviations

| Abbreviation | Meaning |
|---|---|
| MCP | Model Context Protocol — Cursor tool server integration |
| PR | Pull request — maintainer merge workflow |
| ADR | Architecture Decision Record — `.ai_infra/docs/decisions/` |
| GATES | Hardcoded subprocess list in `prepare.py` |
| Pattern A | Script-first workflow; agents invoke one command per action |

## Planes

| Term | Path |
|------|------|
| Cursor contract | `.cursor/`, `.agents/` |
| Infrastructure | `.ai_infra/` |
| Runtime | `.local/` (gitignored) |

## Agents (default kit)

| Agent | Role |
|-------|------|
| implementer | Slice implementation |
| integrator-mas-agent | Extend agents/skills/MCP into kit infrastructure |
| test-runner | Module tests and coverage |
| verifier | Evidence-based verification |
| enterprise-auditor | Architecture audits |
| researcher | Optional research corpus (off by default) |
