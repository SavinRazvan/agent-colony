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
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

type FlowMode = "slice" | "side";

const VERIFIED = "2026-08-06";
const SOURCES =
  "project-board-collaboration.md · token-efficiency.md · board-ssot/SKILL.md · board-shell/SKILL.md · agent-relations · agent-roster · .cursor/agents/*.md · ADR-007 · ADR-008";

const STATUS_STEPS = ["Ready", "In progress", "In review", "Done"];

/** Manual board-centered positions — auto DAG crossed labels on this dense graph. */
const NODE_W = 118;
const NODE_H = 36;
const DAG_W = 720;
const DAG_H = 320;

type RosterId =
  | "board"
  | "implementer"
  | "test-runner"
  | "verifier"
  | "integrator"
  | "auditor"
  | "drift-guard";

/** Centers: x,y of node box top-left. Lane: primary slice across mid-row. */
const NODE_POS: Record<RosterId, { x: number; y: number; lane: "primary" | "side" }> =
  {
    board: { x: 24, y: 142, lane: "primary" },
    implementer: { x: 200, y: 142, lane: "primary" },
    "test-runner": { x: 400, y: 142, lane: "primary" },
    verifier: { x: 580, y: 142, lane: "primary" },
    integrator: { x: 200, y: 28, lane: "side" },
    auditor: { x: 400, y: 28, lane: "side" },
    "drift-guard": { x: 300, y: 256, lane: "side" },
  };

type RosterEdge = {
  from: RosterId;
  to: RosterId;
  kind: "primary" | "side" | "back";
  label: string;
};

const ROSTER_EDGES: RosterEdge[] = [
  {
    from: "board",
    to: "implementer",
    kind: "primary",
    label: "handoff next=implementer",
  },
  {
    from: "implementer",
    to: "test-runner",
    kind: "primary",
    label: "when tests/coverage gate PR",
  },
  {
    from: "test-runner",
    to: "verifier",
    kind: "primary",
    label: "tests gate the PR",
  },
  {
    from: "implementer",
    to: "verifier",
    kind: "primary",
    label: "Exit --next verifier (no test gate)",
  },
  {
    from: "implementer",
    to: "drift-guard",
    kind: "side",
    label: "P0/P1 after drift-validate / goal pulse",
  },
  {
    from: "drift-guard",
    to: "board",
    kind: "back",
    label: "remediation Notes/Ready",
  },
  {
    from: "drift-guard",
    to: "implementer",
    kind: "back",
    label: "remediation Notes/Ready",
  },
  {
    from: "auditor",
    to: "implementer",
    kind: "side",
    label: "CHK-* artifacts → Ready",
  },
  {
    from: "auditor",
    to: "drift-guard",
    kind: "side",
    label: "orch Phase 3 goal pulse",
  },
  {
    from: "auditor",
    to: "verifier",
    kind: "side",
    label: "audit-orchestration Phase 3",
  },
  {
    from: "integrator",
    to: "implementer",
    kind: "side",
    label: "escalate product src/",
  },
  {
    from: "integrator",
    to: "test-runner",
    kind: "side",
    label: "escalate coverage",
  },
  {
    from: "integrator",
    to: "auditor",
    kind: "side",
    label: "escalate architecture",
  },
];

type DagView = "slice" | "all";

const PER_AGENT_ENTRY_EXIT = [
  [
    "board",
    "project entry",
    "Full triage; handoff to implementer",
  ],
  [
    "implementer",
    "project entry → claim --agent implementer",
    "handoff --agent implementer --next … --to in_review or →Done",
  ],
  [
    "test-runner",
    "project entry → slice card",
    "→In review or →Done; --agent test-runner",
  ],
  [
    "verifier",
    "project entry → related card",
    "→Done or leave In review; --agent verifier",
  ],
  [
    "integrator",
    "project entry → claim",
    "→Done; --agent integrator",
  ],
  [
    "auditor",
    "project entry → audit card",
    "→In review/Done; --agent auditor + CHK-* / alignment artifact paths",
  ],
  [
    "drift-guard",
    "Must project entry (then scoped list if live)",
    "Drift card →Done; goal pulse + DRIFT-001…012; remediation via Notes/Ready — no silent tracker edits",
  ],
  [
    "researcher",
    "project entry (+ research card)",
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
    "Points table in board-ssot skill (defaults s/1 when guessed)",
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
    "implementer, board, integrator, verifier, test-runner, auditor (Exit)",
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
    "drift-guard",
    "After drift validate pass",
    "board, implementer (via Notes / Ready)",
    "Dual-write evidence; remediation handoff — no silent tracker edits",
  ],
  [
    ".local/workflow-artifacts/enterprise-architecture-audit/enterprise-architecture-audit.md + enterprise-audit-actions.md",
    "auditor",
    "Audit complete",
    "implementer",
    "implementer applies tracker actions from Notes paths",
  ],
  [
    ".local/workflow-artifacts/alignment/alignment-audit.md + alignment-todos.md",
    "auditor (optional)",
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
    "agent_colony project CLI",
    "EXIT_QUEUED (6) on rate-limit",
    "Any agent / human (outbox flush)",
    "Local buffer — not a second Status SSOT",
  ],
  [
    ".local/generated-data/project-board-snapshot.json",
    "project export [--reuse-if-fresh] (read-only)",
    "DRIFT-010 refresh (+ kit-dev DRIFT-011 roster in validate)",
    "drift-guard · ICC (EA-010)",
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
  "project entry (live|conserve|offline_artifacts); then get/claim one card",
  "Read Notes: @owner.github_user/agent · YYYY-MM-DDTHH:MM:SSZ · …",
  "Follow handoff line: item_id=… · Status=a→b · next=@user/agent",
  "Follow artifact paths in Notes (e.g. auditor → implementer)",
  "Claim with project claim --last --agent <this-agent> after create",
];

const SLICE_FLOW = [
  "board: project entry → triage Ready → handoff next=implementer",
  "implementer: claim --agent implementer → code + prepare.py resolve_gates() → handoff --next verifier (or test-runner when tests gate)",
  "test-runner (when tests gate PR): project entry → slice card → test-index / test-plan → in_review → verifier",
  "verifier: project entry → related card → evidence check → done or in_review with failure Notes",
];

const SIDE_FLOW = [
  "auditor: audit card → CHK-* / enterprise-architecture-audit/ + alignment/ → Notes paths → implementer (Phase 3: drift-guard goal pulse / verifier)",
  "implementer: make drift-validate → P0/P1 or goal-pulse gaps → hand off drift-guard",
  "drift-guard: board In progress + Acceptance/Notes → drift validate (DRIFT-001…012 kit-dev) → .local/workflow-artifacts/drift/ → card done; remediation via Notes/Ready",
  "integrator: integration card → integrate validate → escalate to implementer | test-runner | auditor",
];

function anchor(
  id: RosterId,
  side: "left" | "right" | "top" | "bottom" | "center",
): { x: number; y: number } {
  const p = NODE_POS[id];
  const cx = p.x + NODE_W / 2;
  const cy = p.y + NODE_H / 2;
  if (side === "left") return { x: p.x, y: cy };
  if (side === "right") return { x: p.x + NODE_W, y: cy };
  if (side === "top") return { x: cx, y: p.y };
  if (side === "bottom") return { x: cx, y: p.y + NODE_H };
  return { x: cx, y: cy };
}

/** Pick ports so primary stays mid-row; side/back use vertical ports. */
function edgePorts(
  from: RosterId,
  to: RosterId,
  kind: RosterEdge["kind"],
): { s: { x: number; y: number }; t: { x: number; y: number } } {
  if (kind === "primary") {
    return { s: anchor(from, "right"), t: anchor(to, "left") };
  }
  if (from === "drift-guard" && to === "board") {
    return { s: anchor(from, "left"), t: anchor(to, "bottom") };
  }
  if (from === "drift-guard" && to === "implementer") {
    return { s: anchor(from, "top"), t: anchor(to, "bottom") };
  }
  if (NODE_POS[from].y < NODE_POS[to].y) {
    return { s: anchor(from, "bottom"), t: anchor(to, "top") };
  }
  if (NODE_POS[from].y > NODE_POS[to].y) {
    return { s: anchor(from, "top"), t: anchor(to, "bottom") };
  }
  return { s: anchor(from, "right"), t: anchor(to, "left") };
}

function edgePath(
  from: RosterId,
  to: RosterId,
  kind: RosterEdge["kind"],
): string {
  const { s, t } = edgePorts(from, to, kind);
  if (kind === "primary" && from === "implementer" && to === "verifier") {
    // Arc above the mid-row so it clears test-runner
    const midX = (s.x + t.x) / 2;
    const midY = s.y - 52;
    return `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
  }
  if (kind === "back" && from === "drift-guard" && to === "board") {
    const midX = 80;
    const midY = 300;
    return `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
  }
  const midX = (s.x + t.x) / 2;
  const midY = (s.y + t.y) / 2;
  return `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
}

function CollaborationDag({
  tokens,
  view,
}: {
  tokens: ReturnType<typeof useHostTheme>["tokens"];
  view: DagView;
}) {
  const edges =
    view === "slice"
      ? ROSTER_EDGES.filter((e) => e.kind === "primary")
      : ROSTER_EDGES;
  const nodeIds: RosterId[] =
    view === "slice"
      ? ["board", "implementer", "test-runner", "verifier"]
      : (Object.keys(NODE_POS) as RosterId[]);

  return (
    <Stack gap={12}>
      <svg
        width="100%"
        viewBox={`0 0 ${DAG_W} ${DAG_H}`}
        style={{ maxWidth: 720 }}
      >
        {/* Primary lane band */}
        <rect
          x={12}
          y={128}
          width={DAG_W - 24}
          height={64}
          rx={6}
          fill={tokens.fill.tertiary}
          opacity={0.45}
        />
        <text
          x={20}
          y={122}
          fill={tokens.text.tertiary}
          fontSize={9}
        >
          Primary slice lane
        </text>

        {edges.map((e) => (
          <path
            key={`${e.from}→${e.to}`}
            d={edgePath(e.from, e.to, e.kind)}
            fill="none"
            stroke={
              e.kind === "primary"
                ? tokens.accent.primary
                : tokens.stroke.secondary
            }
            strokeWidth={e.kind === "primary" ? 2 : 1.25}
            strokeDasharray={e.kind === "back" ? "5 3" : undefined}
            opacity={e.kind === "primary" ? 1 : 0.85}
          />
        ))}

        {nodeIds.map((id) => {
          const p = NODE_POS[id];
          const isHub = id === "board";
          return (
            <g key={id}>
              <rect
                x={p.x}
                y={p.y}
                width={NODE_W}
                height={NODE_H}
                rx={4}
                fill={isHub ? tokens.fill.primary : tokens.fill.secondary}
                stroke={
                  isHub ? tokens.accent.primary : tokens.stroke.primary
                }
                strokeWidth={isHub ? 2 : 1}
              />
              <text
                x={p.x + NODE_W / 2}
                y={p.y + NODE_H / 2 + 4}
                textAnchor="middle"
                fill={tokens.text.primary}
                fontSize={11}
                fontWeight={isHub ? 600 : 400}
              >
                {id}
              </text>
            </g>
          );
        })}
      </svg>

      <Row gap={10} wrap>
        <Pill size="sm" tone="info" active>
          solid accent = primary slice
        </Pill>
        <Pill size="sm" tone="neutral">
          solid muted = side escalate
        </Pill>
        <Pill size="sm" tone="neutral">
          dashed = back / remediation
        </Pill>
      </Row>

      <Table
        headers={["From", "To", "Kind", "Via"]}
        rows={edges.map((e) => [e.from, e.to, e.kind, e.label])}
        striped
      />
    </Stack>
  );
}

export default function AgentBoardCollaborationCanvas() {
  const { tokens } = useHostTheme();
  const [flowMode, setFlowMode] = useCanvasState<FlowMode>("flowMode", "slice");
  const [dagView, setDagView] = useCanvasState<DagView>("dagView", "slice");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Agent × GitHub Project collaboration</H1>
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
            Entry: prefer project entry (live scoped list → conserve snapshot →
            offline_artifacts). One export --reuse-if-fresh per parent wave.
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
            /board + board-shell until board-bootstrap --check
            matches the Playground six-view default (Priority/Size/Estimate/Start
            date on Status board + Prioritized backlog).
          </Text>
          <Text>
            /auditor is architecture-impacting / pre-merge — not day-0.
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
        <CardHeader
          trailing={
            <Toggle
              checked={dagView === "all"}
              onChange={(on) => setDagView(on ? "all" : "slice")}
              label={
                dagView === "all" ? "All handoffs" : "Primary slice only"
              }
            />
          }
        >
          Collaboration DAG (board-centered)
        </CardHeader>
        <CardBody>
          <Callout tone="neutral" title="GitHub Project = continuation hub">
            Every agent Entry reads board Status + card body; Exit updates Status
            and attributed Notes. Mid-row = typical slice; side/back edges are
            escalations and remediation — labels live in the table (not on the
            lines).
          </Callout>
          <Spacer size={10} />
          <CollaborationDag tokens={tokens} view={dagView} />
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
              ? "Typical slice (board-ssot SKILL § Multi-agent handoffs)"
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
