# mas-workflow-kit-project-ssot

**Product:** MAS Workflow Kit — Project SSOT. Collaborators and agents share one **GitHub Project** as the **only writable SSOT** for backlog/status; **local artifacts** hold PR gates, audits, and evidence. Configured in `github.collaboration.yaml` like identity.

| | |
|--|--|
| **Board** | [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) |
| **Product repo** | [mas-workflow-kit-project-ssot](https://github.com/SavinRazvan/mas-workflow-kit-project-ssot) |
| **Lineage (read-only)** | [mas-workflow-kit](https://github.com/SavinRazvan/mas-workflow-kit) — historical upstream; never merge doctrine back |
| **Agent handoff (READ FIRST)** | [HANDOFF.md](./HANDOFF.md) |

**Agents (8):** `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `researcher`, `integrator-mas-agent`, `workflow-drift-guard`, `project-board` — see [AGENTS.md](./AGENTS.md). Board CLI: `python3 -m cursor_workflow project …`. **Continuation:** every agent reads the Project on Entry and updates Status/Notes on Exit ([project-board-collaboration.md](.ai_infra/docs/operations/project-board-collaboration.md)).

**STANDALONE 2026-07-18:** this repository **is** the product (already separated). Do not treat it as a temporary sandbox or a port queue into upstream `mas-workflow-kit`.

**Lineage:** Tree originally mirrored from [`mas-workflow-kit`](https://github.com/SavinRazvan/mas-workflow-kit) `main` (tip `8a779fa` / tag `v0.4.0`). Follow [HANDOFF.md](./HANDOFF.md) for board+local SSOT. This workspace applies **7 universal** Cursor rules (6 kit + `project-ssot-precedence`).

## Clone (new Cursor window)

```bash
gh repo clone SavinRazvan/mas-workflow-kit-project-ssot
cd mas-workflow-kit-project-ssot
```

Open the folder in Cursor → point the agent at **`HANDOFF.md`**.

## Install the plugin (consumers — other app repos)

In **Agent chat** (not terminal), from **your application** workspace:

```text
/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot
```

Click the **MAS Workflow Kit — Project SSOT** card, then run **`/workflow-activate`** in that same app folder. That copies `.cursor/`, `.ai_infra/`, `.local/` trackers, and agents into the consumer project.

This repository is the **product kit** (develop + ship). Consumer apps **install + activate** it; they do not need upstream `mas-workflow-kit`.

## Kit quick navigation

- **Plugin manual** — [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md)
- **Consumer quickstart** — [consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md)
- **Agent entry** — [AGENTS.md](./AGENTS.md)
- **Docs index** — [.ai_infra/docs/README.md](.ai_infra/docs/README.md)

After editing `.local/user_settings/github.collaboration.yaml`:

```bash
source .venv/bin/activate
python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow health
```

## License

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)
