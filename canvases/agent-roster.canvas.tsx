import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Stack,
  Table,
  Text,
  Toggle,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

const VERIFIED = "2026-08-06";
const SOURCES = "Aggregated from .cursor/agents/*.md (post goal-pulse / CHK-*)";

const AGENTS = [
  {
    id: "implementer",
    description:
      "implementer Agent Colony — Disciplined implementation slices with trackers and Pattern A gates.",
  },
  {
    id: "verifier",
    description:
      "verifier Agent Colony — Check “done” claims against fresh evidence (try to disprove; no code fixes).",
  },
  {
    id: "test-runner",
    description: "test-runner Agent Colony — Module-focused tests, regressions, coverage.",
  },
  {
    id: "drift-guard",
    description:
      "drift-guard Agent Colony — Continuous goal/plan/agent-doctrine/docs coherence plus operational DRIFT scripts; handoff remediations only.",
  },
  {
    id: "auditor",
    description:
      "auditor Agent Colony — Deep/periodic evidence architecture audit (CHK-* security/perf/granularity/docs); not continuous plan pulse.",
  },
  {
    id: "board",
    description:
      "board Agent Colony — Wire Project SSOT, triage cards, and coach first-run board shell via project_ssot CLI.",
  },
  {
    id: "integrator",
    description:
      "integrator Agent Colony — Integrates new agents, skills, MCP, and infrastructure expansions into the Agent Colony — procedural, evidence-only, Pattern A compliant.",
  },
  {
    id: "researcher",
    description:
      "researcher Agent Colony — Brief-driven multi-round research (GitHub/local) into _research_results packs; hard-stop on product code.",
  },
];

type RosterId =
  | "board"
  | "implementer"
  | "test-runner"
  | "verifier"
  | "integrator"
  | "auditor"
  | "drift-guard"
  | "researcher";

type EdgeKind = "primary" | "side" | "back";
type DagView = "slice" | "all";

const NODE_W = 118;
const NODE_H = 36;
const DAG_W = 720;
const DAG_H = 360;

/** Manual board-centered positions — auto DAG + on-edge labels overlapped. */
const NODE_POS: Record<RosterId, { x: number; y: number }> = {
  board: { x: 24, y: 142 },
  implementer: { x: 200, y: 142 },
  "test-runner": { x: 400, y: 142 },
  verifier: { x: 580, y: 142 },
  integrator: { x: 200, y: 28 },
  auditor: { x: 400, y: 28 },
  "drift-guard": { x: 300, y: 256 },
  researcher: { x: 580, y: 256 },
};

type RosterEdge = {
  from: RosterId;
  to: RosterId;
  kind: EdgeKind;
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

const RESEARCHER_REDIRECTS = [
  ["implementer", "Product code / commits"],
  ["verifier", "Claims vs evidence (no code fixes)"],
  ["auditor", "Architecture audits"],
  ["drift-guard", "Drift / tracker coherence"],
  ["integrator", "Kit surface integration"],
  ["pr-workflow", "Git commit/push/PR (maintainer skills)"],
];

function anchor(
  id: RosterId,
  side: "left" | "right" | "top" | "bottom",
): { x: number; y: number } {
  const p = NODE_POS[id];
  const cx = p.x + NODE_W / 2;
  const cy = p.y + NODE_H / 2;
  if (side === "left") return { x: p.x, y: cy };
  if (side === "right") return { x: p.x + NODE_W, y: cy };
  if (side === "top") return { x: cx, y: p.y };
  return { x: cx, y: p.y + NODE_H };
}

function edgePorts(
  from: RosterId,
  to: RosterId,
  kind: EdgeKind,
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

function edgePath(from: RosterId, to: RosterId, kind: EdgeKind): string {
  const { s, t } = edgePorts(from, to, kind);
  if (kind === "primary" && from === "implementer" && to === "verifier") {
    const midX = (s.x + t.x) / 2;
    const midY = s.y - 52;
    return `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
  }
  if (kind === "back" && from === "drift-guard" && to === "board") {
    return `M ${s.x} ${s.y} Q 80 300 ${t.x} ${t.y}`;
  }
  const midX = (s.x + t.x) / 2;
  const midY = (s.y + t.y) / 2;
  return `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
}

function RosterDag({
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
        <rect
          x={12}
          y={128}
          width={DAG_W - 24}
          height={64}
          rx={6}
          fill={tokens.fill.tertiary}
          opacity={0.45}
        />
        <text x={20} y={122} fill={tokens.text.tertiary} fontSize={9}>
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
          const isResearch = id === "researcher";
          return (
            <g key={id}>
              <rect
                x={p.x}
                y={p.y}
                width={NODE_W}
                height={NODE_H}
                rx={4}
                fill={
                  isHub
                    ? tokens.fill.primary
                    : isResearch
                      ? tokens.fill.tertiary
                      : tokens.fill.secondary
                }
                stroke={
                  isHub
                    ? tokens.accent.primary
                    : isResearch
                      ? tokens.stroke.secondary
                      : tokens.stroke.primary
                }
                strokeWidth={isHub ? 2 : 1}
                strokeDasharray={isResearch ? "4 2" : undefined}
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

        {view === "all" ? (
          <text
            x={NODE_POS.researcher.x + NODE_W / 2}
            y={NODE_POS.researcher.y + NODE_H + 14}
            textAnchor="middle"
            fill={tokens.text.tertiary}
            fontSize={9}
          >
            no product handoff edges
          </text>
        ) : null}
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
        <Pill size="sm" tone="neutral">
          dashed box = researcher (redirects only)
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

export default function AgentRosterCanvas() {
  const { tokens } = useHostTheme();
  const [dagView, setDagView] = useCanvasState<DagView>("dagView", "slice");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Kit agent roster</H1>
          <Pill tone="info" size="sm">
            hub · not an agent
          </Pill>
          <Pill tone="neutral" size="sm">
            8 agents
          </Pill>
        </Row>
        <Text tone="secondary">
          Overview of all live agents (ids match .cursor/agents/*.md). This file is
          a DOC-008 roster hub — there is no agent named &quot;roster&quot;. Deeper
          graph: agent-relations. Per-agent Entry/Exit: agent-board-collaboration.
        </Text>
        <Callout tone="info" title="Live ids (post B-safe rename)">
          auditor · board · drift-guard · implementer · integrator · researcher ·
          test-runner · verifier — skills: board-ssot, implementer-loop,
          test-coverage, auditor-protocol (CHK-*), drift-audit (goal pulse +
          DRIFT-001…016), integrator-protocol, …
        </Callout>
        <Callout tone="neutral" title="Quality lane split (2026-08-04)">
          Continuous plan/agent/docs coherence → drift-guard. Deep
          security/perf/granularity/docs scorecard → auditor. No extra agents.
        </Callout>
        <Callout tone="neutral" title="Board lifecycle (all 8)">
          Tier-1: Start date on claim or first In progress; Size↔Estimate points
          table in board-ssot skill. Promote Draft→Issue via promote-to-issue or
          mention-pr (auto when promote_to_issue_on_pr) before shippable PR —
          claim does not auto-promote. Notes: @owner.github_user/&lt;agent&gt; ·
          YYYY-MM-DDTHH:MM:SSZ · … via append-notes --agent.
        </Callout>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

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
          Handoff DAG (explicit edges only)
        </CardHeader>
        <CardBody>
          <Text tone="secondary" size="small">
            Mid-row = typical slice. Side/back edges and researcher are shown in
            All handoffs. Labels live in the table (not on the lines).
          </Text>
          <RosterDag tokens={tokens} view={dagView} />
        </CardBody>
      </Card>

      <Divider />

      <Stack gap={8}>
        <H2>Goals (one-liner per agent)</H2>
        <Grid columns={2} gap={10}>
          {AGENTS.map((a) => (
            <Stack key={a.id} gap={4}>
              <Text>{a.id}</Text>
              <Text tone="secondary" size="small">
                {a.description}
              </Text>
            </Stack>
          ))}
        </Grid>
      </Stack>

      <Card>
        <CardHeader>researcher → use instead</CardHeader>
        <CardBody>
          <Table headers={["Agent", "When"]} rows={RESEARCHER_REDIRECTS} />
          <Callout tone="info" title="Shipped non-product agent">
            researcher is fully functional (live E2E + verifier PASS 2026-07-19).
            Writes only _research_results/ after research init (opt-in corpus).
            No src/tests/scripts; no git/PR. Not in product handoff DAG —
            consumers read AGENT_BRIEF.md. See agent-researcher canvas.
          </Callout>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Edge evidence (card citations)</H2>
        <Table
          headers={["From", "To", "Evidence"]}
          rows={[
            ["implementer", "verifier", "Exit recipe --next verifier"],
            ["implementer", "test-runner", "When tests/coverage gate PR"],
            ["test-runner", "verifier", "When tests gate the PR"],
            [
              "implementer",
              "drift-guard",
              "P0/P1 after make drift-validate",
            ],
            ["board", "implementer", "handoff next=implementer"],
            [
              "drift-guard",
              "board | implementer",
              "Dual-write remediation via Ready",
            ],
            [
              "auditor",
              "implementer | drift-guard | verifier",
              "Notes + audit-orchestration Phase 3",
            ],
            [
              "integrator",
              "implementer | test-runner | auditor",
              "Escalation table on integrator card",
            ],
          ]}
        />
      </Stack>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact
        paths.
      </Text>
    </Stack>
  );
}
