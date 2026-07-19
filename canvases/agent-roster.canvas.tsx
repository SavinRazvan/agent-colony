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

const VERIFIED = "2026-07-19";
const SOURCES = "Aggregated from .cursor/agents/*.md";

const AGENTS = [
  {
    id: "implementer",
    description: "Disciplined implementation slices with trackers and Pattern A gates",
  },
  {
    id: "verifier",
    description: "Claims vs evidence; minimal high-signal checks",
  },
  {
    id: "test-runner",
    description: "Module-focused tests, regressions, coverage",
  },
  {
    id: "workflow-drift-guard",
    description:
      "Operational workflow drift detection; plan/tracker/session coherence and handoff parity",
  },
  {
    id: "enterprise-auditor",
    description:
      "Evidence-only enterprise architecture audit; writes workflow artifacts and tracker hooks for other agents",
  },
  {
    id: "project-board",
    description:
      "Independent-governed helper — list/create/move GitHub Project SSOT cards via project_ssot CLI",
  },
  {
    id: "integrator-mas-agent",
    description:
      "Integrates new agents, skills, MCP, and infrastructure expansions — procedural, evidence-only, Pattern A",
  },
  {
    id: "researcher",
    description:
      "Shipped/proven corpus researcher — adaptive Brief; packs under _research_results/ (opt-in after init); hard-stop on product code",
  },
];

const ROSTER_NODES = [
  { id: "project-board" },
  { id: "implementer" },
  { id: "verifier" },
  { id: "workflow-drift-guard" },
  { id: "enterprise-auditor" },
  { id: "integrator-mas-agent" },
  { id: "test-runner" },
  { id: "researcher" },
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

const RESEARCHER_REDIRECTS = [
  ["implementer", "Product code changes"],
  ["verifier", "Claims vs evidence"],
  ["enterprise-auditor", "Architecture audits"],
  ["pr-workflow", "Git commit/push/PR (not researcher)"],
];

function RosterDag({ tokens }: { tokens: ReturnType<typeof useHostTheme>["tokens"] }) {
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
              n.id === "researcher"
                ? tokens.fill.tertiary
                : tokens.fill.secondary
            }
            stroke={tokens.stroke.primary}
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

export default function AgentRosterCanvas() {
  const { tokens } = useHostTheme();

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Kit agent roster</H1>
          <Pill tone="info" size="sm">
            8 agents
          </Pill>
        </Row>
        <Text tone="secondary">
          Explicit handoff edges from agent cards (skill chain test-runner→verifier
          when tests gate PR). researcher is shipped/proven and non-product —
          corpus opt-in; redirects to product agents for code/PR.
        </Text>
        <Callout tone="info" title="Board lifecycle (all 8)">
          Tier-1: Start date on claim or first In progress; Size↔Estimate points
          table in project-board-ssot skill. Promote Draft→Issue via promote-to-issue or mention-pr (auto when
          promote_to_issue_on_pr) before shippable PR — claim does not auto-promote.
          Notes: @owner.github_user/&lt;agent&gt; · YYYY-MM-DDTHH:MM:SSZ · … via
          append-notes --agent. See agent-board-collaboration canvas.
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
          <Table
            headers={["Agent", "When"]}
            rows={RESEARCHER_REDIRECTS}
          />
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
            [
              "implementer",
              "workflow-drift-guard",
              "P0/P1 after make drift-validate",
            ],
            ["project-board", "implementer", "handoff next=implementer"],
            [
              "workflow-drift-guard",
              "project-board | implementer",
              "Dual-write remediation via Ready",
            ],
            [
              "enterprise-auditor",
              "implementer",
              "Notes with artifact paths for implementer",
            ],
            [
              "integrator-mas-agent",
              "implementer | test-runner | enterprise-auditor",
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
