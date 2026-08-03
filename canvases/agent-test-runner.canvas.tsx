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

type SsotMode = "board" | "fallback";

const VERIFIED = "2026-07-20";
const SOURCES =
  ".cursor/agents/test-runner.md · test-coverage/SKILL.md · board-ssot/SKILL.md";

const GOALS = [
  "Module-focused tests, regressions, coverage",
  "Run targeted module tests before full suite",
  "Update test-index and test-plan when tests change",
  "After scoped 100%: doc reality sync (IMPLEMENTATION-STATUS + make coverage-index + make doc-validate)",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "claim" },
  { id: "index" },
  { id: "tests" },
  { id: "coverage" },
  { id: "artifacts" },
  { id: "handoff" },
  { id: "next" },
];

const BOARD_EDGES = [
  { from: "status", to: "claim" },
  { from: "claim", to: "index" },
  { from: "index", to: "tests" },
  { from: "tests", to: "coverage" },
  { from: "coverage", to: "artifacts" },
  { from: "artifacts", to: "handoff" },
  { from: "handoff", to: "next" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "index" },
  { id: "tests" },
  { id: "coverage" },
  { id: "artifacts" },
  { id: "handoff" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "index" },
  { from: "index", to: "tests" },
  { from: "tests", to: "coverage" },
  { from: "coverage", to: "artifacts" },
  { from: "artifacts", to: "handoff" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project status",
  claim: "claim card",
  index: "test-index.md",
  tests: "tests/modules/",
  coverage: "coverage.json",
  artifacts: "test-plan + change-index",
  handoff: "handoff",
  next: "next agent",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  index: "test-index.md",
  tests: "tests/modules/",
  coverage: "coverage.json",
  artifacts: "test-plan + change-index",
  handoff: "handoff / close",
};

const READ_FIRST = [
  [".cursor/skills/test-coverage/SKILL.md", "Test lifecycle canon"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".local/index-and-planning/current/test-index.md", "When tests change"],
  [".local/index-and-planning/current/test-plan.md", "When tests change"],
  ["check_testing_artifacts.py", "Before PR path"],
];

const PATTERNS = [
  ["Consume only", "No create-from-template"],
  ["Board lifecycle", "Exit in_review if tests gate PR else done"],
  ["Tier-1", "Shared Board rights; promote only if opening a shippable PR"],
  ["Module layout", "tests/modules/<module>/ matching source boundaries"],
  ["Coverage evidence", "pytest --cov writes coverage.json only — do not invent alternate names"],
  ["Shell filters", "Prefer grep/python over rg (often absent from PATH)"],
  ["Post-100% sync", "IMPLEMENTATION-STATUS + make coverage-index + make doc-validate"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/test-runner via --agent test-runner"],
];

const ARTIFACTS = [
  ["tests/modules/<module>/", "Implementation / regression", "CI / prepare.py"],
  ["coverage.json", "Coverage evidence run", "test-runner / DOC-006"],
  ["coverage-index.md", "After meaningful coverage / 100% closure", "test-runner / implementer"],
  ["IMPLEMENTATION-STATUS.md", "After scoped 100% / count change", "DOC-006 / maintainers"],
  ["test-index.md", "When tests change", "test-runner / implementer"],
  ["test-plan.md", "When tests change", "test-runner / implementer"],
  ["change-index.md", "Exit", "Next agents / humans"],
  ["Board Status + Notes", "Exit", "Next agent"],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "Later flush"],
];

const PEERS = [
  ["Outbound", "next (generic)", "handoff format per card"],
  ["Inbound", "implementer", "Handoff when tests/coverage needed before merge"],
  ["Inbound", "integrator-mas-agent", "Escalates coverage work to test-runner"],
];

function DagPanel({
  mode,
  tokens,
}: {
  mode: SsotMode;
  tokens: ReturnType<typeof useHostTheme>["tokens"];
}) {
  const nodes = mode === "board" ? BOARD_NODES : FALLBACK_NODES;
  const edges = mode === "board" ? BOARD_EDGES : FALLBACK_EDGES;
  const labels = mode === "board" ? BOARD_LABELS : FALLBACK_LABELS;
  const layout = computeDAGLayout(nodes, edges, {
    direction: "horizontal",
    nodeWidth: 118,
    nodeHeight: 36,
    rankGap: 36,
    nodeGap: 16,
  });
  const w = Math.max(...layout.nodes.map((n) => n.x + n.width)) + 16;
  const h = Math.max(...layout.nodes.map((n) => n.y + n.height)) + 16;
  const byId = Object.fromEntries(layout.nodes.map((n) => [n.id, n]));

  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ maxWidth: 920 }}>
      {layout.edges.map((e, i) => {
        const a = byId[e.from];
        const b = byId[e.to];
        if (!a || !b) return null;
        const x1 = a.x + a.width;
        const y1 = a.y + a.height / 2;
        const x2 = b.x;
        const y2 = b.y + b.height / 2;
        return (
          <line
            key={i}
            x1={x1}
            y1={y1}
            x2={x2}
            y2={y2}
            stroke={tokens.stroke.secondary}
            strokeWidth={1.5}
          />
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
            fill={tokens.fill.secondary}
            stroke={tokens.stroke.primary}
          />
          <text
            x={n.x + n.width / 2}
            y={n.y + n.height / 2 + 4}
            textAnchor="middle"
            fill={tokens.text.primary}
            fontSize={10}
          >
            {labels[n.id] ?? n.id}
          </text>
        </g>
      ))}
    </svg>
  );
}

export default function AgentTestRunnerCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>test-runner</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            consume only
          </Pill>
        </Row>
        <Text tone="secondary">
          Module-focused tests, regressions, coverage.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board-first Anchor" />
        <Stat value="in_review" label="When tests gate PR" tone="warning" />
        <Stat value="EXIT_QUEUED" label="Outbox on rate-limit" tone="warning" />
      </Grid>

      <Stack gap={8}>
        <H2>Goals</H2>
        {GOALS.map((g) => (
          <Text key={g}>• {g}</Text>
        ))}
      </Stack>

      <Divider />

      <Stack gap={10}>
        <Row gap={12} style={{ alignItems: "center" }}>
          <H2 style={{ margin: 0 }}>Workflow</H2>
          <Toggle
            checked={mode === "board"}
            onChange={(on) => setMode(on ? "board" : "fallback")}
            label={mode === "board" ? "board_only SSOT" : "local_trackers fallback"}
          />
        </Row>
        <Callout
          tone="info"
          title={mode === "board" ? "project_ssot.enabled" : "Offline / disabled"}
        >
          {mode === "board"
            ? "Entry: project status + claim. Read test-index when tests change."
            : "Entry: session-pointer.md. Read test-index when tests change."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. Claim card (board) or read session-pointer (fallback).</Text>
          <Text>2. Read test-index / test-plan when tests or ownership change.</Text>
          <Text>3. Run module-focused tests; regressions; coverage when required.</Text>
          <Text>
            4. Coverage evidence: pytest --cov writes coverage.json only; prefer
            grep/python over rg.
          </Text>
          <Text>5. check_testing_artifacts.py before PR path.</Text>
          <Text>
            6. After scoped 100%: sync IMPLEMENTATION-STATUS, make coverage-index,
            make doc-validate.
          </Text>
          <Text>
            7. Exit: Status in_review if tests gate PR else done; update
            change-index + test-index/test-plan.
          </Text>
        </Stack>
      </CollapsibleSection>

      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader>Files & patterns</CardHeader>
          <CardBody>
            <Table
              headers={["Path / pattern", "Role"]}
              rows={[...READ_FIRST, ...PATTERNS]}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Artifacts</CardHeader>
          <CardBody>
            <Table headers={["Path", "When", "Consumed by"]} rows={ARTIFACTS} />
            <Spacer size={8} />
            <Text tone="tertiary" size="small">
              Primary writer of tests/modules/ and test tracker updates for owned
              slices.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>Entry: project status + claim. Consume only — no create-from-template.</Text>
            <Text>
              Exit: must Status in_review if tests gate PR else done; change-index +
              test-index/test-plan.
            </Text>
            <Text>
              Rate-limit: EXIT_QUEUED (6) → outbox status / flush; do not hammer
              GraphQL.
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Peers</H2>
        <Table headers={["Direction", "Agent", "Evidence"]} rows={PEERS} />
      </Stack>

      <Callout tone="neutral" title="MCP">
        Kit server workflow-kit for PR scripts/gates — prefer cursor_workflow project
        for board. External: only servers listed for this agent in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
