# `.ai_infra/docs/` — kit documentation

**Audience:** Kit maintainers browse from the git repo. After `activate`, consumers receive a **slim subset** — see [folder-charter](governance/folder-charter.md).

## Start here

| You are | Read first |
|---------|------------|
| **New consumer** | [PLUGIN-USER-GUIDE](operations/PLUGIN-USER-GUIDE.md) → [consumer-quickstart](operations/consumer-quickstart.md) |
| **Kit maintainer** | [repository-map](handoff/repository-map.md) → [PLUGIN-ARCHITECTURE](handoff/PLUGIN-ARCHITECTURE.md) → [IMPLEMENTATION-STATUS](handoff/IMPLEMENTATION-STATUS.md) |
| **Governance / policy** | [governance/README](governance/README.md) |

## Folders

| Folder | Index | Role |
|--------|-------|------|
| [`operations/`](operations/) | [operations/README.md](operations/README.md) | Workflow SOPs, install, consumer quickstart, MCP, upgrade |
| [`governance/`](governance/) | [governance/README.md](governance/README.md) | Rules overlap, drift prevention, folder charter, module boundaries |
| [`handoff/`](handoff/) | — | Maintainer status, plugin architecture, repository map, marketplace publish |
| [`architecture/`](architecture/) | — | Consumer C4-lite three-plane view |
| [`roadmap/`](roadmap/) | [roadmap/README.md](roadmap/README.md) | Alignment audit schema |
| [`maintainer/`](maintainer/) | — | Patterns **not** copied to consumers |
| [`decisions/`](decisions/) | [decisions/README.md](decisions/README.md) | ADR index |

## Key files (`handoff/` — kit-dev only)

| File | Role |
|------|------|
| [IMPLEMENTATION-STATUS.md](handoff/IMPLEMENTATION-STATUS.md) | Shipped vs spec, test counts, coverage |
| [PLUGIN-ARCHITECTURE.md](handoff/PLUGIN-ARCHITECTURE.md) | Plugin bundle, three planes, install profiles |
| [repository-map.md](handoff/repository-map.md) | SSOT vs generated vs consumer install (**not shipped** to consumers) |
| [marketplace-publish.md](handoff/marketplace-publish.md) | Listing copy, versioning, publish checklist |

## Key files (consumer-shipped)

| File | Role |
|------|------|
| [workflow-architecture.md](architecture/workflow-architecture.md) | Three planes (C4-lite) — copied on activate |
| [PLUGIN-USER-GUIDE.md](operations/PLUGIN-USER-GUIDE.md) | Plugin manual — copied on activate |
| [consumer-quickstart.md](operations/consumer-quickstart.md) | Install + verify cheat sheet — copied on activate |

## UI templates

[`.ai_infra/templates/local-workspace/`](../templates/local-workspace/) — Control Center dashboards and tracker exemplars.
