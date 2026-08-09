<!--
File: CONTRIBUTING.md
Path: CONTRIBUTING.md
Role: Kit-dev human setup — clone, venv, gates; points to AGENTS.md for agent doctrine.
Used By:
 - README.md (kit maintainers CTA)
 - .ai_infra/docs/README.md
Depends On:
 - AGENTS.md
 - .ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md
Notes:
 - Consumer install lives in .ai_infra/docs/operations/consumer-quickstart.md — not here.
-->

# Contributing (kit-dev)

This page is for people developing the **agent-colony** product repository itself.

**Consumers** installing into an app repo: start at [README.md](README.md) → [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md).

**Agents** working in this repo: read **[AGENTS.md](AGENTS.md)** first (identity, board SSOT, roster, gates).

---

## Setup

```bash
gh repo clone SavinRazvan/agent-colony
cd agent-colony
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

1. Open the folder in Cursor.
2. Confirm `.local/user_settings/github.collaboration.yaml` (owner + `project_ssot`).
3. Entry when board SSOT is on:

```bash
python3 -m agent_colony project status
python3 -m agent_colony project list --status ready
# create / claim — see: python3 -m agent_colony project guide
```

---

## Maintainer gates

```bash
make gates
make drift-validate
make doc-validate
```

Before release / plugin ship: `make sync-plugin` · `make check-plugin` · see [marketplace-publish.md](.ai_infra/docs/handoff/marketplace-publish.md).

Do **not** run `agent_colony update --force` against this kit-dev tree — use `make sync-plugin` instead.

---

## Further reading

| Doc | Role |
|-----|------|
| [AGENTS.md](AGENTS.md) | Agent doctrine, continuation, commit trailers |
| [repository-map.md](.ai_infra/docs/handoff/repository-map.md) | SSOT vs generated vs consumer install |
| [PLUGIN-ARCHITECTURE.md](.ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md) | Plugin bundle, three planes |
| [IMPLEMENTATION-STATUS.md](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) | Shipped vs spec, test counts, canvases |
| [Docs index](.ai_infra/docs/README.md) | Full `.ai_infra/docs/` navigation |

---

## License

By contributing, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).
