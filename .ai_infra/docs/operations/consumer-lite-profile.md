<!--
File: consumer-lite-profile.md
Path: .ai_infra/docs/operations/consumer-lite-profile.md
Role: Spec for consumer_lite install profile — allowlists, exclusions, upgrade path.
Used By:
 - workflow-activate skill
 - consumer-quickstart.md
 - ADR-011
Depends On:
 - manifest.yaml
 - token-efficiency-program.md
Notes:
 - Shipped to consumers via copy_ai_infra docs/operations.
-->

# Consumer lite profile

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)

Optional install profile for smaller fixed Cursor overhead. Canon: [ADR-011](../decisions/ADR-011-consumer-lite-profile.md).

## Activate

```bash
python3 -m agent_colony activate --directory . --profile consumer_lite
# or via slash skill after plugin install:
/workflow-activate
# (pass --profile consumer_lite when prompted or in CLI)
```

Profile marker written to `.local/generated-data/install-profile.json`:

```json
{"profile": "consumer_lite", "kit_version": "0.7.2"}
```

## Included (6 skills, 6 agents)

| Skills | Agents |
|--------|--------|
| `board-ssot`, `implementer-loop`, `evidence-first`, `test-coverage`, `workflow-activate`, `mcp-connect` | `board`, `implementer`, `test-runner`, `verifier`, `drift-guard`, `integrator` |

## Maintainer slash skills (`.agents/skills`)

Lite keeps PR workflow slash skills only (kit **0.7.1+**):

| Kept on lite | Pruned on lite |
|--------------|----------------|
| `review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`, `full-pr-workflow` | `audit-alignment`, `PR_WORKFLOW.md`, `RESEARCH_WORKFLOW.md` |

All use `disable-model-invocation`. `README.md` is kept.

## Excluded

| Excluded | Why | Upgrade |
|----------|-----|---------|
| Skills: `board-shell`, `auditor-protocol`, `drift-audit`, `audit-*`, `research-corpus`, `canvas-artifacts`, `update-agent-colony` | Size / maintainer / day-0 non-critical | `update --force --profile with_mcp` |
| Agents: `researcher`, `auditor` | Research + deep audit | Full profile |

## First-run board (no `board-shell` skill)

Lite omits `board-shell/` on disk. **Do not** use `doc skill-section --skill board-shell` on lite — file absent.

Use **`/board`** agent + § **First-run (lite profile)** in [board.md](../../../.cursor/agents/board.md):

1. **CONSENT GATE** — ask before YAML save / shell setup
2. **TURN PROTOCOL** — one view per turn; human UI via [views-setup.md](../../templates/project-board/views-setup.md)
3. Exit when `board-bootstrap --check` returns **0**

Full profile: use `board-shell` skill or `doc skill-section --skill board-shell`.

## Thin-index on lite

| Skill | DRIFT-016 validates |
|-------|---------------------|
| 6 allowlisted skills | yes |
| `board-shell`, `auditor-protocol`, etc. | skip (not on disk) |

## Rules (global 4+3 tiering)

All profiles share tiering after kit 0.7.0:

- **alwaysApply (4):** `project-ssot-precedence`, `implementation-workflow-governance`, `pr-workflow-enforcement`, `local-artifact-protection`
- **requestable (3):** `commit-trailer-format`, `file-docstring-header-relations`, `advisory-audit-alignment-enforcement`

Scaffold does not rewrite rule files per profile.

## AGENTS stub

Lite installs copy [AGENTS.stub-lite.md](../../templates/AGENTS.stub-lite.md) when `AGENTS.md` is missing.

## Upgrade to full kit

> **Plain `update` upgrades lite to full.** `python3 -m agent_colony update --directory .` uses default profile **`with_mcp`** and restores **15 skills / 8 agents** on version bump. To **stay on lite** after a kit refresh, pass `--profile consumer_lite` explicitly:
>
> ```bash
> python3 -m agent_colony update --profile consumer_lite --force --directory .
> # or re-activate:
> python3 -m agent_colony activate --directory . --profile consumer_lite
> ```

```bash
python3 -m agent_colony update --force --profile with_mcp --directory .
python3 -m agent_colony health
python3 -m agent_colony drift validate --profile consumer
```

Restores 15 skills, 8 agents, full thin-index validation, and all `.agents/skills` dirs.

## When to use lite vs full

| Use lite | Use full (`with_mcp`) |
|----------|----------------------|
| Day-to-day implement/verify/test on board SSOT | Need `/researcher`, `/auditor`, canvas, full audit skills |
| Token-sensitive long sessions | Maintainer PR workflow + alignment audits |
| First consumer adopt | Kit-dev or integrator expanding agents/skills |
