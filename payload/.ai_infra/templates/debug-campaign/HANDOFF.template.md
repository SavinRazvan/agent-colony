<!--
File: HANDOFF.template.md
Path: .ai_infra/templates/debug-campaign/HANDOFF.template.md
Role: Human handoff projection for debugger campaigns.
Used By:
 - agent_colony debug handoff
Depends On:
 - publish/HANDOFF.json
-->

# Debug Handoff

campaign_id: {{campaign_id}}
slug: {{slug}}
source_revision: {{source_revision}}
validation_state: {{validation_state}}
outcome: {{outcome}}
next_agent: {{next_agent}}

## Next Action

{{next_action}}

## Publish Refs

{{publish_refs}}
# HANDOFF — {{slug}}

| Field | Value |
|-------|-------|
| **campaign_id** | {{campaign_id}} |
| **status** | {{status}} |
| **mode** | {{mode}} |
| **source_revision** | {{source_revision}} |
| **outcome** | {{outcome}} |
| **next_agent** | {{next_agent}} |
| **validation** | {{validation}} |
| **human_status** | {{human_status}} |

## Findings

- DBG: {{dbg_ids}}
- TR: {{tr_ids}}
- SG: {{sg_ids}}

## Active probes

{{active_probes}}

## Publish refs

{{publish_refs}}

## Next action

{{next_action}}
