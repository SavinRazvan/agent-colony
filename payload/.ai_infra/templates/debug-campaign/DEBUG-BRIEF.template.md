<!--
File: DEBUG-BRIEF.template.md
Path: .ai_infra/templates/debug-campaign/DEBUG-BRIEF.template.md
Role: Campaign intake template.
Used By:
 - agent_colony debug init
Depends On:
 - INDEX.json
-->

# Debug Brief

```text
campaign_id: {{campaign_id}}
slug: {{slug}}
mode: {{mode}}
item_id: {{item_id}}
source_revision: {{source_revision}}
lenses: {{lenses}}
```

## Scope

(TBD)

## Acceptance

(TBD)

## Rollback

Remove active probes and keep vault evidence protected unless deletion is separately approved.
# Debug brief

| Field | Value |
|-------|-------|
| **slug** | {{slug}} |
| **mode** | {{mode}} |
| **lenses** | {{lenses}} |
| **item_id** | {{item_id}} |
| **consumers** | {{consumers}} |
| **human_status** | {{human_status}} |
| **scope** | {{scope}} |
| **notes** | {{notes}} |

## Symptom

{{symptom}}

## Falsification plan

{{falsification}}

## Acceptance

{{acceptance}}

## Rollback

{{rollback}}
