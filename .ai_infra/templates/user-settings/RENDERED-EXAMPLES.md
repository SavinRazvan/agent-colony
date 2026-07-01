# Rendered examples — GitHub collaboration

Side-by-side: **legacy external-product style** vs **MAS Workflow Kit default** (from `github.collaboration.yaml`).

Replace `Your Full Name` and `@yourhandle` with values from `.local/user_settings/github.collaboration.yaml`.

---

## Commit message

### Kit default (`ai_disclosure_mode: assisted_by`)

```text
docs(notebooks): frame notebooks as assertion-backed proof artifacts

Update root README, architecture docs, notebook standards, and evaluator
guides to describe hardened tutorial/check outputs, flagship proof paths, and
what governed vs live notebooks demonstrate for reviewers.

Author: Your Full Name
GitHub-User: @yourhandle
Assisted-by: Cursor
```

### Legacy opt-in (`ai_disclosure_mode: co_author_trailer`)

Only enable if your org requires Git `Co-authored-by` for tools:

```text
docs(adapters): close PyPI extraction handoff and update strategy references

Replace in-tree adapter package references with external repo pins
and lockstep version pins across handoffs, strategy, operations, and architecture docs.

Author: Your Full Name
GitHub-User: @yourhandle
Assisted-by: Cursor
Co-authored-by: Cursor <cursoragent@cursor.com>
```

---

## Pull request body

### Kit default (no `Made with Cursor`)

```markdown
## Summary
- Shared local-shell.css + site-nav.js for local HTML dashboards
- Landing index.html, aligned ICC + module-audit stub; docs + folder charter updates

## Test plan
- [ ] pytest -q
- [ ] make gates

## Collaboration
- Action-By: Your Full Name
- GitHub-User: @yourhandle
- Agent/s: review-pr | prepare-pr | merge-pr
```

### Architecture-impacting PR (add alignment)

```markdown
## Collaboration
- Action-By: Your Full Name
- GitHub-User: @yourhandle
- Agent/s: enterprise-auditor | review-pr | prepare-pr | merge-pr
- Alignment: `.local/workflow-artifacts/alignment/`
```

---

## Local phase artifact header (`prep.md`)

Scripts stamp this; values should match `.local/user_settings/github.collaboration.yaml`:

```markdown
## Attribution
- Action-By: Your Full Name
- Prepared-By: Your Full Name
- GitHub-User: @yourhandle
- Agent/s: review-pr | prepare-pr | merge-pr
- Branch: feature/my-branch
- HEAD SHA: abc123...
```

---

## Multi-agent feature slice

When several agents touch one PR, list the pipeline (not fake human co-authors):

```yaml
# github.collaboration.yaml
pipelines:
  multi_agent_feature:
    agents: [implementer, test-runner, verifier, review-pr, prepare-pr]
```

```text
Assisted-by: Cursor:implementer
Assisted-by: Cursor:test-runner
Assisted-by: Cursor:verifier
```

```markdown
- Agent/s: implementer | test-runner | verifier | review-pr | prepare-pr
```
