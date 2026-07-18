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

const VERIFIED = "2026-07-18";
const SOURCES =
  ".cursor/agents/researcher.md · research-corpus-execution/SKILL.md · research_cli.py · _research_results/";

const GOALS = [
  "Brief-driven multi-round research (GitHub or local path)",
  "Packs under _research_results/sources/<slug>/ + AGENT_BRIEF for MAS",
  "Hard-stop: write only _research_results/ — no product git/PR",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "brief" },
  { id: "cli" },
  { id: "rounds" },
  { id: "done" },
  { id: "notes" },
];

const BOARD_EDGES = [
  { from: "status", to: "brief" },
  { from: "brief", to: "cli" },
  { from: "cli", to: "rounds" },
  { from: "rounds", to: "done" },
  { from: "done", to: "notes" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "brief" },
  { id: "rounds" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "brief" },
  { from: "brief", to: "rounds" },
  { from: "rounds", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project status",
  brief: "Research Brief",
  cli: "research init/fetch",
  rounds: "rounds 1-6 + validate",
  done: "set-status done",
  notes: "AGENT_BRIEF paths",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  brief: "Research Brief",
  rounds: "rounds 1-6 + validate",
  close: "local close",
};

const READ_FIRST = [
  [".cursor/skills/research-corpus-execution/SKILL.md", "Research canon"],
  ["_research_results/RESEARCH_BOUNDARIES.md", "Hard-stop boundaries"],
  [".cursor/skills/project-board-ssot/SKILL.md", "When project_ssot.enabled"],
];

const PATTERNS = [
  ["Hard stop", "Write only _research_results/"],
  ["Brief required", "External mode refuses without BRIEF.md"],
  ["CLI", "research init | fetch | validate"],
  ["Board lifecycle", "create-from-template research → done + pack paths"],
  ["Consumers", "implementer / integrator read AGENT_BRIEF.md"],
  ["Attribution", "@owner.github_user/researcher via --agent"],
];

const ARTIFACTS = [
  ["_research_results/sources/<slug>/", "Pack + AGENT_BRIEF", "implementer / integrator"],
  ["Board Status + Notes", "Research card done + pack paths", "Next agents"],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "Later flush"],
];

const PEERS = [
  ["Use instead", "implementer", "Product code changes"],
  ["Use instead", "pr-workflow", "Git commit/push/PR"],
  ["Use instead", "enterprise-auditor", "Architecture audits"],
  ["Use instead", "verifier", "Claims vs evidence"],
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

export default function AgentResearcherCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>researcher</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="warning" size="sm">
            optional / off by default
          </Pill>
        </Row>
        <Text tone="secondary">
          Optional local research corpus; hard-stop on product code without explicit
          scope.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="_research_results/" label="Only write target" />
        <Stat value="hard stop" label="No product code" tone="warning" />
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
        <Callout tone="warning" title="Hard stop">
          Write only _research_results/. No src/tests/scripts. No git commit/push/PR.
          Use implementer, pr-workflow, enterprise-auditor, or verifier instead for
          those tasks.
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>
            1. Entry: project status (+ research card list); else session-pointer.
          </Text>
          <Text>2. Read _research_results/RESEARCH_BOUNDARIES.md and research-corpus-execution skill.</Text>
          <Text>3. Produce corpus under _research_results/ only.</Text>
          <Text>
            4. If research card: set-status done + Notes with corpus paths.
          </Text>
          <Text>5. Do not touch product code, tests, scripts, or git/PR workflows.</Text>
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
              Research output is read-only input for humans and product agents —
              not shipped product code.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>Entry: project status + research card list when board on.</Text>
            <Text>
              Exit: corpus under _research_results/; research card set-status done +
              Notes with corpus paths.
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
        External research MCP only when listed for this agent in mcp.registry.yaml.
        Prefer cursor_workflow project for board when research card exists.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
