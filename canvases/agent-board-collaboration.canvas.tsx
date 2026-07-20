import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  CollapsibleSection,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Spacer,
  Stack,
  Stat,
  Table,
  Text,
  Toggle,
  computeDAGLayout,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

type FlowMode = "slice" | "side";

const VERIFIED = "2026-07-20";
const SOURCES =
  "project-board-collaboration.md · project-board-ssot/SKILL.md · board-shell-onboard/SKILL.md · .cursor/agents/*.md · agent-roster edges";

const STATUS_STEPS = ["Ready", "In progress", "In review", "Done"];

const ROSTER_NODES = [
  { id: "project-board" },
  { id: "implementer" },
  { id: "verifier" },
  { id: "workflow-drift-guard" },
  { id: "enterprise-auditor" },
  { id: "integrator-mas-agent" },
  { id: "test-runner" },
];

const ROSTER_EDGES = [
  { from: "project-board", to: "implementer" },
  { from: "implementer", to: "verifier" },
  { from: "implementer", to: "workflow-drift-guard" },
  { from: "workflow-drift-guard", to: "project-board" },
  { from: "workflow-drift-guard", to: "implementer" },
  { from: "enterprise-auditor", to: "implementer" },
  { from: "integrator-mas-agent", to: "implementer" },
  { from: "integrator-mas-agent", to: "test-runner" },
  { from: "integrator-mas-agent", to: "enterprise-auditor" },
];

const EDGE_LABELS: Record<string, string> = {
  "project-board→implementer": "handoff next=implementer",
  "implementer→verifier": "Exit --next verifier",
  "implementer→workflow-drift-guard": "P0/P1 after drift-validate",
  "workflow-drift-guard→project-board": "dual-write remediation",
  "workflow-drift-guard→implementer": "dual-write remediation",
  "enterprise-auditor→implementer": "Notes + artifact paths",
  "integrator-mas-agent→implementer": "escalate product src/",
  "integrator-mas-agent→test-runner": "escalate coverage",
  "integrator-mas-agent→enterprise-auditor": "escalate architecture",
};

const PER_AGENT_ENTRY_EXIT = [
  [
    "project-board",
    "status + list",
    "Full triage; handoff to implementer",
  ],
  [
    "implementer",
    "status + claim --agent implementer",
    "handoff --agent implementer --next … --to in_review or →Done",
  ],
  [
    "test-runner",
    "status + slice card",
    "→In review or →Done; --agent test-runner",
  ],
  [
    "verifier",
    "status + related card",
    "→Done or leave In review; --agent verifier",
  ],
  [
    "integrator-mas-agent",
    "status + claim",
    "→Done; --agent integrator-mas-agent",
  ],
  [
    "enterprise-auditor",
    "status + audit card",
    "→In review/Done; --agent enterprise-auditor + artifact paths",
  ],
  [
    "workflow-drift-guard",
    "Must status + list In progress",
    "Drift card →Done; --agent workflow-drift-guard; remediation via Notes/Ready — no silent tracker edits",
  ],
  [
    "researcher",
    "status (+ research card)",
    "Research card →Done; --agent researcher + AGENT_BRIEF / pack paths",
  ],
];

const BOARD_TIER1 = [
  [
    "Start date",
    "claim / set-status / handoff → in_progress",
    "UTC today if empty when set_start_date_on_claim + fields.start_date.field_id",
    "All agents on first In progress",
    "WARN only on failure; parent op still succeeds",
  ],
  [
    "Size / Estimate",
    "create-from-template / set-field",
    "Points table in project-board-ssot skill (defaults s/1 when guessed)",
    "Triage + create",
    "Priority required; Estimate = points not hours",
  ],
  [
    "Promote Draft→Issue",
    "Before PR / explicit",
    "promote-to-issue --last --agent <name> [--repo owner/repo]",
    "implementer (typical)",
    "convertProjectV2DraftIssueItemToIssue; same PVTI_; claim does NOT auto-promote; fine-grained PAT caveat",
  ],
  [
    "Linked PR",
    "PR open (Issue-backed)",
    "mention-pr --pr N → Notes; auto-promote when promote_to_issue_on_pr (default true)",
    "implementer (typical)",
    "FAIL if promote fails; Linked pull requests column works after Issue",
  ],
];

const ARTIFACT_FLOWS = [
  [
    "Board card body (Acceptance / Rollback / Notes)",
    "All agents (Exit append-notes --agent)",
    "Entry read; Exit handoff",
    "All agents",
    "Continuation index; @user/agent · UTC · …; next=@user/agent",
  ],
  [
    ".local/index-and-planning/current/change-index.md",
    "implementer, project-board, integrator, verifier, test-runner, enterprise-auditor (Exit)",
    "Slice close / triage",
    "Next agents, humans, ICC",
    "Append row; scope pointer for continuation",
  ],
  [
    ".local/index-and-planning/history/updates-log.md",
    "All agents (Exit one-liner)",
    "Slice close",
    "Drift / continuity readers",
    "One UTC line per close",
  ],
  [
    ".local/index-and-planning/current/test-index.md / test-plan.md",
    "test-runner",
    "When tests or ownership change",
    "test-runner (Entry); implementer when slice touches tests",
    "Test scope and coverage tracking",
  ],
  [
    ".local/workflow-artifacts/drift/drift-audit.md + drift-todos.md",
    "workflow-drift-guard",
    "After drift validate pass",
    "project-board, implementer (via Notes / Ready)",
    "Dual-write evidence; remediation handoff — no silent tracker edits",
  ],
  [
    ".local/workflow-artifacts/enterprise-architecture-audit/enterprise-architecture-audit.md + enterprise-audit-actions.md",
    "enterprise-auditor",
    "Audit complete",
    "implementer",
    "implementer applies tracker actions from Notes paths",
  ],
  [
    ".local/workflow-artifacts/alignment/alignment-audit.md + alignment-todos.md",
    "enterprise-auditor (optional)",
    "Governance drift findings",
    "implementer (advisory)",
    "Optional alignment pass; no auto-remediation",
  ],
  [
    ".local/workflow-artifacts/pr/ (review.md, prep.md, merge.md)",
    "Maintainer PR scripts (local)",
    "PR Pattern A phases",
    "verifier",
    "Required for merge readiness when maintainer workflow in play",
  ],
  [
    "_research_results/",
    "researcher only",
    "Research corpus work",
    "researcher",
    "Local gitignored corpus; no product handoff edges",
  ],
  [
    ".local/generated-data/board-outbox.jsonl",
    "cursor_workflow project CLI",
    "EXIT_QUEUED (6) on rate-limit",
    "Any agent / human (outbox flush)",
    "Local buffer — not a second Status SSOT",
  ],
  [
    ".local/generated-data/project-board-snapshot.json",
    "project export (read-only)",
    "DRIFT-010 refresh",
    "workflow-drift-guard · ICC (EA-010)",
    "Read-only export; never writes Status",
  ],
  [
    "session-pointer.md / plan.md / work-tracker.md",
    "Fallback trackers (offline only)",
    "When board disabled or CLI fallback",
    "All agents (offline Entry)",
    "Offline SSOT only — resume board sync when available",
  ],
];

const NEXT_AGENT_STEPS = [
  "List Ready / In progress / In review on board (project status · project list)",
  "Read Notes: @owner.github_user/agent · YYYY-MM-DDTHH:MM:SSZ · …",
  "Follow handoff line: item_id=… · Status=a→b · next=@user/agent",
  "Follow artifact paths in Notes (e.g. enterprise-auditor → implementer)",
  "Claim with project claim --last --agent <this-agent> after create",
];

const SLICE_FLOW = [
  "project-board: status + list → triage Ready → handoff next=implementer",
  "implementer: claim --agent implementer → code + gates → handoff --next verifier (typical)",
  "test-runner (when tests gate PR): status + slice card → test-index / test-plan → in_review",
  "verifier: status + related card → evidence check → done or in_review with failure Notes",
];

const SIDE_FLOW = [
  "enterprise-auditor: audit card → write .local/workflow-artifacts/… → Notes paths → implementer",
  "implementer: make drift-validate → P0/P1 → hand off workflow-drift-guard",
  "workflow-drift-guard: must read board In progress → drift artifacts → drift card done; remediation via Notes/Ready to project-board or implementer",
  "integrator-mas-agent: integration card → validate → escalate to implementer | test-runner | enterprise-auditor",
];

function CollaborationDag({
  tokens,
}: {
  tokens: ReturnType<typeof useHostTheme>["tokens"];
}) {
  const layout = computeDAGLayout(ROSTER_NODES, ROSTER_EDGES, {
    direction: "horizontal",
    nodeWidth: 130,
    nodeHeight: 40,
    rankGap: 48,
    nodeGap: 20,
  });
  const w = Math.max(...layout.nodes.map((n) => n.x + n.width)) + 24;
  const h = Math.max(...layout.nodes.map((n) => n.y + n.height)) + 24;
  const byId = Object.fromEntries(layout.nodes.map((n) => [n.id, n]));

  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ maxWidth: 960 }}>
      {layout.edges.map((e, i) => {
        const a = byId[e.from];
        const b = byId[e.to];
        if (!a || !b) return null;
        const x1 = a.x + a.width;
        const y1 = a.y + a.height / 2;
        const x2 = b.x;
        const y2 = b.y + b.height / 2;
        const label = EDGE_LABELS[`${e.from}→${e.to}`] ?? "";
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2 - 6;
        return (
          <g key={i}>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={tokens.stroke.secondary}
              strokeWidth={1.5}
            />
            {label ? (
              <text
                x={mx}
                y={my}
                textAnchor="middle"
                fill={tokens.text.tertiary}
                fontSize={8}
              >
                {label.length > 28 ? label.slice(0, 26) + "…" : label}
              </text>
            ) : null}
          </g>
        );
      })}
      {layout.nodes.map((n) => (
        <g key={n.id}>
          <rect
            x={n.x}
            y={n.y}
            width={n.width}
            height={n.height}
            rx={4}
            fill={
              n.id === "project-board"
                ? tokens.fill.primary
                : tokens.fill.secondary
            }
            stroke={
              n.id === "project-board"
                ? tokens.accent.primary
                : tokens.stroke.primary
            }
          />
          <text
            x={n.x + n.width / 2}
            y={n.y + n.height / 2 + 4}
            textAnchor="middle"
            fill={tokens.text.primary}
            fontSize={9}
          >
            {n.id}
          </text>
        </g>
      ))}
    </svg>
  );
}

export default function AgentBoardCollaborationCanvas() {
  const { tokens } = useHostTheme();
  const [flowMode, setFlowMode] = useCanvasState<FlowMode>("flowMode", "slice");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Agent × Project board collaboration</H1>
          <Pill tone="info" size="sm">
            board SSOT
          </Pill>
        </Row>
        <Text tone="secondary">
          How kit agents collaborate via GitHub Project Status, roster handoffs,
          and local evidence artifacts.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Callout tone="info" title="SSOT tiers (board_only)">
        <Stack gap={6}>
          <Text>
            GitHub Project = only writable Status SSOT when project_ssot.enabled
            and sync_policy: board_only.
          </Text>
          <Text>
            Local evidence (.local/workflow-artifacts/, change-index, PR artifacts)
            stays local — never competes with board Status.
          </Text>
          <Text>
            .local/generated-data/board-outbox.jsonl = EXIT_QUEUED buffer on
            rate-limit — flush later; not a second Status SSOT.
          </Text>
        </Stack>
      </Callout>

      <Callout tone="warning" title="Day-0 board shell (before day-to-day cards)">
        <Stack gap={6}>
          <Text>
            /project-board + board-shell-onboard until board-bootstrap --check
            matches the Playground six-view default (Priority/Size/Estimate/Start
            date on Status board + Prioritized backlog).
          </Text>
          <Text>
            /enterprise-auditor is architecture-impacting / pre-merge — not day-0.
          </Text>
        </Stack>
      </Callout>

      <Grid columns={4} gap={10}>
        {STATUS_STEPS.map((step, i) => (
          <Stat
            key={step}
            value={String(i + 1)}
            label={step}
            tone={i === STATUS_STEPS.length - 1 ? "success" : "neutral"}
          />
        ))}
      </Grid>
      <Text tone="tertiary" size="small">
        Status path: Ready → In progress → In review → Done
      </Text>

      <Divider />

      <Card>
        <CardHeader>Collaboration DAG (board-centered roster edges)</CardHeader>
        <CardBody>
          <Callout tone="neutral" title="GitHub Project = continuation hub">
            Every agent Entry reads board Status + card body; Exit updates Status
            and attributed Notes. DAG edges are explicit handoffs from agent cards
            — all paths route through board Status/Notes.
          </Callout>
          <Spacer size={10} />
          <CollaborationDag tokens={tokens} />
          <Text tone="tertiary" size="small">
            researcher: no product handoff edges — redirects only (see
            agent-roster canvas).
          </Text>
        </CardBody>
      </Card>

      <Stack gap={10}>
        <Row gap={12} style={{ alignItems: "center" }}>
          <H2 style={{ margin: 0 }}>Flow paths</H2>
          <Toggle
            checked={flowMode === "slice"}
            onChange={(on) => setFlowMode(on ? "slice" : "side")}
            label={
              flowMode === "slice"
                ? "Typical slice flow"
                : "Audit / drift side paths"
            }
          />
        </Row>
        <CollapsibleSection
          title={
            flowMode === "slice"
              ? "Typical slice (project-board-ssot SKILL § Multi-agent handoffs)"
              : "Audit / drift side paths"
          }
          defaultOpen
        >
          <Stack gap={6}>
            {(flowMode === "slice" ? SLICE_FLOW : SIDE_FLOW).map((line) => (
              <Text key={line}>• {line}</Text>
            ))}
            {flowMode === "slice" ? (
              <Text tone="secondary" size="small">
                Chain from skill: implementer → test-runner → verifier (test-runner
                optional when tests gate the PR).
              </Text>
            ) : null}
          </Stack>
        </CollapsibleSection>
      </Stack>

      <Card>
        <CardHeader>
          Per-agent board Entry / Exit (project-board-collaboration.md)
        </CardHeader>
        <CardBody>
          <Table
            headers={["Agent", "Entry", "Exit (board)"]}
            rows={PER_AGENT_ENTRY_EXIT}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>Tier-1 board fields (agents — facts from project CLI)</CardHeader>
        <CardBody>
          <Table
            headers={["Field", "When", "CLI / config", "Typical actor", "Notes"]}
            rows={BOARD_TIER1}
          />
          <Spacer size={8} />
          <Text tone="tertiary" size="small">
            Out of scope for agents by default: Iteration, Labels, Reviewers, End date
            (human / UI).
          </Text>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>Artifact flows (agent cards + ops doc paths only)</CardHeader>
        <CardBody>
          <Table
            headers={[
              "Artifact",
              "Written by",
              "When",
              "Read / used by",
              "How used",
            ]}
            rows={ARTIFACT_FLOWS}
          />
        </CardBody>
      </Card>

      <Callout tone="info" title="How the next agent finds work">
        <Stack gap={6}>
          {NEXT_AGENT_STEPS.map((step) => (
            <Text key={step}>• {step}</Text>
          ))}
        </Stack>
      </Callout>

      <Callout tone="warning" title="Human-only surfaces">
        Views, workflows, Insights, Project README, status updates, Ready
        prioritization / product roadmap. Paste README from
        .ai_infra/templates/project-board/project-readme.md in GitHub UI only —
        agents never edit these.
      </Callout>

      <Text tone="tertiary" size="small">
        Peer views: canvases/agent-relations.canvas.tsx (handoff graph) ·
        agent-roster.canvas.tsx (explicit card edges)
      </Text>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact
        paths.
      </Text>
    </Stack>
  );
}
