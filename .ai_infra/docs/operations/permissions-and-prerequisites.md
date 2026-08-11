<!--
File: permissions-and-prerequisites.md
Path: .ai_infra/docs/operations/permissions-and-prerequisites.md
Role: Canonical checklist — what users must install, authorize, and configure before Agent Colony agents and the plugin work as documented.
Used By:
 - README.md
 - PLUGIN-USER-GUIDE.md
 - consumer-quickstart.md
 - AGENTS.md
 - workflow-activate skill
Depends On:
 - PLUGIN-USER-GUIDE.md
 - consumer-quickstart.md
 - connect-external-mcp.md
 - project-board-collaboration.md
Notes:
 - Copied to consumer projects via manifest copy_ai_infra: docs/operations.
 - Agent Colony does not ship a GitHub OAuth app; auth uses gh CLI + git on the user's machine.
-->

# What you need — permissions & prerequisites

> **Read this before `/implementer`.** It lists everything you must have on your machine and what you must approve on GitHub so the **Cursor plugin**, **agents**, and **board SSOT** behave as documented.
>
> Install path: [consumer-quickstart](consumer-quickstart.md) · Full manual: [PLUGIN-USER-GUIDE](PLUGIN-USER-GUIDE.md)

---

## At a glance

| Layer | Required for | What you give / install |
|-------|----------------|-------------------------|
| **Cursor IDE** | Plugin + agents | Open your app folder; allow terminal, workspace read/write, network |
| **Python 3.11+** | Activate + CLI | Local venv (`.venv`) created by `/workflow-activate` |
| **GitHub CLI (`gh`)** | PR workflow; board SSOT when enabled | **`repo`** (PRs/issues); **`read:project`** + **`project`** (board SSOT only) |
| **Git credentials** | Push branches, open PRs | SSH key or HTTPS — standard git setup (not stored by the kit) |
| **GitHub account access** | Board + repo operations | Write access to your **code repo** and **GitHub Project** |
| **MCP** (optional) | Extra tools (DeepWiki, custom APIs) | Per-server tokens only when you opt in |

**Agent Colony does not ask for a separate GitHub app or a token pasted into chat.** Agents call `gh` and git using **your** logged-in session.

---

## Two setup profiles

Pick the profile that matches how you use the kit.

### Profile A — Plugin + agents (no board SSOT)

Use when `project_ssot.enabled: false` — local trackers only.

| # | Requirement |
|---|-------------|
| 1 | [Cursor](https://cursor.com) with your **app repo** open (not the kit product repo `agent-colony`) |
| 2 | Python **3.11+** |
| 3 | Plugin: `/add-plugin https://github.com/SavinRazvan/agent-colony` |
| 4 | Activate: `/workflow-activate` → wait for **`VERIFY PASS`** |
| 5 | Identity: edit `.local/user_settings/github.collaboration.yaml` → `contributors validate` |
| 6 | **`gh auth login`** with **`repo`** scope (for `/review-pr` → `/merge-pr`) |
| 7 | **Git push/pull** to your remote |

### Profile B — Full kit (GitHub Project board SSOT) — recommended

Use when `project_ssot.enabled: true` and `sync_policy: board_only`.

Everything in **Profile A**, plus:

| # | Requirement |
|---|-------------|
| 8 | **`gh auth refresh -h github.com -s read:project,project`** (keep existing `repo`) |
| 9 | A **GitHub Project** with **write access** for your user (org Projects need membership + Project access) |
| 10 | **Default repository** on the Project set to your app repo (human UI when creating the Project) |
| 11 | **`/board`** — paste Project URL + repo URL; confirm proposed YAML |
| 12 | **Human UI:** Project views (minimal **2-view** or kit default **6-view**) — agents cannot API-create views today |
| 13 | **`project doctor`** + **`board-bootstrap --check` exit 0** before `/implementer` |

---

## 1. Cursor IDE (plugin + agents)

The plugin loads agents, skills, and rules into Cursor. **Activate** copies infrastructure into **your project folder**.

| Capability | Why agents need it |
|------------|-------------------|
| **Your app folder open** | Activate and agents write `.cursor/`, `.ai_infra/`, `.local/` under your repo |
| **Agent chat** (`/` menu) | `/workflow-activate`, `/implementer`, `/board`, PR slash skills |
| **Terminal / shell** | `python3 -m agent_colony …`, `gh …`, `pytest` |
| **Workspace read/write** | Code edits, trackers, workflow artifacts under `.local/` |
| **Network** | Plugin install from GitHub, `gh` API, optional MCP servers |
| **MCP enabled** (recommended) | Built-in `agent-colony-mcp`; DeepWiki seeded on consumer activate |
| **Browser MCP** (optional) | Only if **you explicitly ask** for help clicking GitHub Project UI during board shell setup |

**Cursor does not replace `gh auth login`.** GitHub permissions are configured on your machine via the GitHub CLI (§2).

---

## 2. GitHub CLI (`gh`) — main GitHub authorization

When board SSOT is on, agents read and write the **GitHub Project** via `gh project …` GraphQL. PR skills use `gh pr …`.

### Required OAuth scopes

| Scope | Required? | Used for |
|-------|-----------|----------|
| **`repo`** | **Yes** | Issues, PRs, repo reads/writes, link PRs to board cards |
| **`read:project`** | **Yes** (board SSOT) | Read Project, fields, items |
| **`project`** | **Yes** (board SSOT) | Write Status, Notes, Priority/Size/Estimate, claim/handoff |
| **`workflow`** | Optional | CI / Actions checks when driven via `gh` |

### Setup

**First login (new machine):**

```bash
gh auth login -h github.com
```

Choose HTTPS, authenticate via browser or device code, and allow access to the repos you use.

**Add Project scopes to an existing login:**

```bash
gh auth refresh -h github.com -s read:project,project
# Keeps existing repo (and workflow) scopes — refresh adds Project access.
```

**No browser (WSL, headless, SSH — `xdg-open: no method available`):**

1. Run `gh auth login` or `gh auth refresh …` and leave the terminal open.
2. Copy the **one-time code** from the terminal.
3. Open **[https://github.com/login/device](https://github.com/login/device)** in any browser.
4. Paste the code → sign in → **approve GitHub + Project permissions**.
5. Return to the terminal — expect `✓ Authentication complete.`

**Verify:**

```bash
gh auth status
# Token scopes should include: repo, project
# (read:project may show separately or be covered when project is present)

python3 -m agent_colony project doctor    # when board SSOT on
python3 -m agent_colony project status
```

If `gh` reports **missing required scopes `[read:project]` / `[project]`**, re-run `gh auth refresh -h github.com -s read:project,project` and complete the device link again.

### Token type: classic vs fine-grained PAT

| Method | Recommendation |
|--------|----------------|
| **`gh auth login` (OAuth via `gh`)** | **Preferred** — simplest for Projects |
| **Classic PAT** | Works — needs `repo` + `project` (+ `read:project`) |
| **Fine-grained PAT** | **Partial** — some Project mutations fail (e.g. Draft→Issue `promote-to-issue`) |

If you see `Resource not accessible by fine-grained personal access token`, use **`gh auth login`** or a **classic PAT** with `project` + `repo`. `project doctor` notes this when relevant.

---

## 3. GitHub account & org access (beyond scopes)

OAuth scopes are necessary but not sufficient. Your **GitHub user** must be able to reach the resources:

| Access | Why |
|--------|-----|
| **Read/write on your code repo** | Create Issues, open/merge PRs, push feature branches |
| **Read/write on the GitHub Project** | Board is the coordination SSOT when enabled |
| **Org Projects** (if org-owned) | Account must be a member with Project access |
| **Merge rights** (for `/merge-pr`) | Repo policy must allow your user to merge |

### Human-only in GitHub UI (not API-automated today)

- Project **views** (2-view minimal or 6-view default)
- Column visibility on **Status board** and **Prioritized backlog**
- Filters, layout, view rename

See [board-shell skill](../../../.cursor/skills/board-shell/SKILL.md) and [project-board-collaboration](project-board-collaboration.md).

---

## 4. Git (separate from `gh`)

| What | Required? | Notes |
|------|-----------|-------|
| **Push/pull to remote** | Yes (PR workflow) | SSH key or HTTPS credentials — standard git |
| **Private repo clone** (researcher) | If researching private repos | Machine must already authenticate for `git clone` |

The kit **does not store** git credentials. Research agent: no kit-side GitHub token — clone uses your local auth.

---

## 5. What the kit stores locally (secrets)

| Path | Contains | Gitignored? |
|------|----------|-------------|
| `.local/user_settings/github.collaboration.yaml` | Name, `@handle`, board field ids — **no token** | Yes |
| `.local/user_settings/mcp.secrets.yaml` | Optional MCP tokens (`mcp auth`) | Yes |
| `.cursor/mcp.user.json` | MCP server transport config | Yes |

Never commit tokens or paste them into Agent chat.

---

## 6. MCP servers (optional)

| Server | Auth |
|--------|------|
| **`agent-colony-mcp`** (built-in, `with_mcp` profile) | None extra — uses local CLI |
| **DeepWiki** (default seed on consumer activate) | **None** — public remote server |
| **GitHub remote MCP** (stretch / opt-in) | Copilot OAuth seat **or** PAT with `repo` |
| **Custom MCP** (Slack, DB, browser, …) | Per server — env vars / `mcp auth --token-env …` |

Guide: [connect-external-mcp.md](connect-external-mcp.md) · Worksheet: `.local/user_settings/mcp.agents.yaml`

---

## 7. PR workflow permissions (`/review-pr` → `/merge-pr`)

Uses the same **`gh` + `repo`** session:

| Action | Permission |
|--------|------------|
| `gh pr view`, `gh pr create` | `repo` |
| `gh pr merge` | `repo` + merge rights on the repo |
| `project mention-pr` (board SSOT) | `repo` + `project` |
| Post-merge board → Done (`merge.py`) | `project` write |

Optional: **`workflow`** scope to inspect CI via `gh`.

---

## 8. What you do **not** need

- No Agent Colony GitHub App install
- No org-wide admin (unless your org policy requires it for Projects)
- No token pasted into chat or committed to git
- No Cursor-specific GitHub OAuth (beyond normal `gh` on your machine)
- No browser automation unless you explicitly request it for board shell UI help

---

## Quick verification checklist

### Profile A (no board)

```bash
python3 -m agent_colony contributors validate
python3 -m agent_colony health
gh auth status    # expect repo
```

### Profile B (board SSOT)

```bash
python3 -m agent_colony contributors validate
gh auth status    # expect repo + project
python3 -m agent_colony project doctor
python3 -m agent_colony project board-bootstrap --check
python3 -m agent_colony project status
```

Expect **`board-bootstrap --check` exit 0** before day-to-day `/implementer`.

---

## Related docs

| Doc | Topic |
|-----|-------|
| [consumer-quickstart.md](consumer-quickstart.md) | 5-step install with screenshots |
| [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md) | Full plugin manual |
| [project-board-collaboration.md](project-board-collaboration.md) | Board Entry/Exit, Tier-1 fields, outbox |
| [connect-external-mcp.md](connect-external-mcp.md) | Optional MCP servers |
| [abbreviations-notepad.md](abbreviations-notepad.md) | SSOT, Pattern A, DRIFT glossary |
