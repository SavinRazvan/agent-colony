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
  computeDAGLayout,
  useHostTheme,
} from "cursor/canvas";

const VERIFIED = "2026-08-05";
const SOURCES = "Aggregated from .cursor/agents/*.md (post goal-pulse / CHK-*)";

const AGENTS = [
  {
    id: "implementer",
    description:
      "implementer Agent Colony — Disciplined implementation slices with trackers and Pattern A gates.",
  },
  {
    id: "verifier",
    description: "verifier Agent Colony — Claims vs evidence; minimal high-signal checks.",
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
      "board Agent Colony — Independent-governed helper — list/create/move GitHub Project SSOT cards via project_ssot CLI.",
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

const ROSTER_NODES = [
  { id: "board" },
  { id: "implementer" },
  { id: "verifier" },
  { id: "drift-guard" },
  { id: "auditor" },
  { id: "integrator" },
  { id: "test-runner" },
  { id: "researcher" },
];

const ROSTER_EDGES = [
  { from: "board", to: "implementer" },
  { from: "implementer", to: "verifier" },
  { from: "implementer", to: "test-runner" },
  { from: "implementer", to: "drift-guard" },
  { from: "test-runner", to: "verifier" },
  { from: "drift-guard", to: "board" },
  { from: "drift-guard", to: "implementer" },
  { from: "auditor", to: "implementer" },
  { from: "auditor", to: "drift-guard" },
  { from: "auditor", to: "verifier" },
  { from: "integrator", to: "implementer" },
  { from: "integrator", to: "test-runner" },
  { from: "integrator", to: "auditor" },
];

const EDGE_LABELS: Record<string, string> = {
  "board→implementer": "handoff next=implementer",
  "implementer→verifier": "Exit --next verifier",
  "implementer→test-runner": "when tests/coverage gate PR",
  "implementer→drift-guard": "P0/P1 after drift-validate / goal pulse",
  "test-runner→verifier": "tests gate the PR",
  "drift-guard→board": "remediation Notes/Ready",
  "drift-guard→implementer": "remediation Notes/Ready",
  "auditor→implementer": "CHK-* artifacts → Ready",
  "auditor→drift-guard": "orch Phase 3 goal pulse",
  "auditor→verifier": "audit-orchestration Phase 3",
  "integrator→implementer": "escalate product src/",
  "integrator→test-runner": "escalate coverage",
  "integrator→auditor": "escalate architecture",
};

const RESEARCHER_REDIRECTS = [
  ["implementer", "Product code / commits"],
  ["verifier", "Claims vs evidence"],
  ["auditor", "Architecture audits"],
  ["drift-guard", "Drift / tracker coherence"],
  ["integrator", "Kit surface integration"],
  ["pr-workflow", "Git commit/push/PR (maintainer skills)"],
];

function RosterDag({ tokens }: { tokens: ReturnType<typeof useHostTheme>["tokens"] }) {
  const nodeW = 130;
  const nodeH = 40;
  const layout = computeDAGLayout({
    nodes: ROSTER_NODES,
    edges: ROSTER_EDGES,
    direction: "horizontal",
    nodeWidth: nodeW,
    nodeHeight: nodeH,
    rankGap: 48,
    nodeGap: 20,
  });

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ maxWidth: 960 }}
    >
      {layout.edges.map((e, i) => {
        const label = EDGE_LABELS[`${e.from}→${e.to}`] ?? "";
        const mx = (e.sourceX + e.targetX) / 2;
        const my = (e.sourceY + e.targetY) / 2 - 6;
        return (
          <g key={i}>
            <line
              x1={e.sourceX}
              y1={e.sourceY}
              x2={e.targetX}
              y2={e.targetY}
              stroke={tokens.stroke.secondary}
              strokeWidth={1.5}
              strokeDasharray={e.isBackEdge ? "4 3" : undefined}
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
            width={nodeW}
            height={nodeH}
            rx={4}
            fill={
              n.id === "researcher"
                ? tokens.fill.tertiary
                : tokens.fill.secondary
            }
            stroke={tokens.stroke.primary}
          />
          <text
            x={n.x + nodeW / 2}
            y={n.y + nodeH / 2 + 4}
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

export default function AgentRosterCanvas() {
  const { tokens } = useHostTheme();

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
          DRIFT-001…012), integrator-protocol, …
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
        <CardHeader>Handoff DAG (explicit edges only)</CardHeader>
        <CardBody>
          <RosterDag tokens={tokens} />
          <Text tone="tertiary" size="small">
            researcher has no product handoff edges — see redirects below.
          </Text>
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
