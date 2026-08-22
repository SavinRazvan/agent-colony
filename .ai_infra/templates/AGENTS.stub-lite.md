# AGENTS.md

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## Installing?

1. Agent chat:

```text
/add-plugin https://github.com/SavinRazvan/agent-colony
```

2. Open **your app folder** → Agent chat:

```text
/workflow-activate
```

Use CLI for lite profile explicitly:

```bash
python3 -m agent_colony activate --directory . --profile consumer_lite
```

Details: [consumer-lite-profile.md](.ai_infra/docs/operations/consumer-lite-profile.md) · [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md).

## Just installed?

1. Edit `.local/user_settings/github.collaboration.yaml` → your name + `@handle`
2. `source .venv/bin/activate && python3 -m agent_colony contributors validate` (**must PASS**)
3. If `project_ssot.enabled: true`:
   - `gh auth status` — refresh Project scopes if needed
   - Agent chat **`/board`** + paste **Project URL** + **repo URL**
   - `python3 -m agent_colony project doctor` (expect **ok**)
   - **First-run lite:** follow § First-run (lite profile) in `.cursor/agents/board.md` — CONSENT + TURN PROTOCOL; **not** `board-shell` skill (absent on lite)
   - Re-run `board-bootstrap --check` until **exit 0**
   - `python3 -m agent_colony project status`
4. If Project SSOT disabled: read `session-pointer.md` → `plan.md` → `work-tracker.md`
5. **`/implementer`** when bootstrap is green

**Upgrade to full kit:** `python3 -m agent_colony update --force --profile with_mcp --directory .`

---

## Project intent

**Agent Colony (lite profile)** — 6 agents, 6 skills, board SSOT when enabled. Merge gates: `resolve_gates()` in `.ai_infra/scripts/pr/prepare.py`.

## First reads

1. [consumer-lite-profile.md](.ai_infra/docs/operations/consumer-lite-profile.md)
2. [token-efficiency.md](.ai_infra/docs/operations/token-efficiency.md)
3. [PLUGIN-USER-GUIDE.md](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md)
4. Board SSOT: `python3 -m agent_colony project entry --digest`

## Rules

**7 rules** — 4 always-on + 3 requestable (load at commit, new files, or architecture-impacting prepare). See [token-efficiency-program.md](.ai_infra/docs/operations/token-efficiency-program.md).

## Commits

Required trailers: `.cursor/rules/commit-trailer-format.mdc` — `python3 -m agent_colony contributors validate`.

## Quality gates

Say *prepare gates green* — do not paste full gate lists.
