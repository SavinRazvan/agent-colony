# mas-workflow-kit-project-ssot

**Experiment:** Make a **GitHub Project** the SSOT for backlog/status — replace local tracker markdown so collaborators and agents share one board (configured in `github.collaboration.yaml` like identity).

| | |
|--|--|
| **Board** | [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) |
| **Production kit (do not break)** | [mas-workflow-kit](https://github.com/SavinRazvan/mas-workflow-kit) |
| **Agent handoff (READ FIRST)** | [HANDOFF.md](./HANDOFF.md) |

This repository is an isolated sibling sandbox. If the experiment fails, abandon this repo; leave marketplace `mas-workflow-kit` on markdown SSOT.

**Kit mirror:** This tree includes a full merge of production [`mas-workflow-kit`](https://github.com/SavinRazvan/mas-workflow-kit) `main` (tip `8a779fa` / tag `v0.4.0`). Use kit docs below for agents, skills, PR workflow, and CLI — but follow [HANDOFF.md](./HANDOFF.md) for experiment scope and board-first work.

## Clone (new Cursor window)

```bash
gh repo clone SavinRazvan/mas-workflow-kit-project-ssot
cd mas-workflow-kit-project-ssot
```

Open the folder in Cursor → point the agent at **`HANDOFF.md`**.

## Kit quick navigation (mirrored from production)

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
