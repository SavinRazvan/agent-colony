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

const VERIFIED = "2026-08-06";
const SOURCES =
  ".cursor/agents/drift-guard.md · drift-audit/SKILL.md · board-ssot/SKILL.md · ADR-007";

const GOALS = [
  "Continuous goal/plan/agent-doctrine/docs coherence (+ DRIFT scripts)",
  "DRIFT-001…012 script-first; goal pulse prose in drift artifacts",
  "Write drift/ only — no product code; remediations via Notes/Ready",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "list" },
  { id: "validate" },
  { id: "audit" },
  { id: "todos" },
  { id: "card" },
  { id: "handoff" },
];

const BOARD_EDGES = [
  { from: "status", to: "list" },
  { from: "list", to: "validate" },
  { from: "validate", to: "audit" },
  { from: "audit", to: "todos" },
  { from: "todos", to: "card" },
  { from: "card", to: "handoff" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "validate" },
  { id: "audit" },
  { id: "todos" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "validate" },
  { from: "validate", to: "audit" },
  { from: "audit", to: "todos" },
  { from: "todos", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project entry",
  list: "list in_progress",
  validate: "drift validate",
  audit: "drift-audit.md",
  todos: "drift-todos.md",
  card: "drift-pass card",
  handoff: "Ready / Notes",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  validate: "drift validate",
  audit: "drift-audit.md",
  todos: "drift-todos.md",
  close: "updates-log",
};

const READ_FIRST = [
  [".cursor/skills/drift-audit/SKILL.md", "Drift audit + goal pulse"],
  [".cursor/skills/board-ssot/SKILL.md", "Board SSOT when enabled"],
  ["python3 -m cursor_workflow drift validate", "CLI entry"],
  ["DRIFT-009 / 010 / 011 / 012", "Board + agent roster pulse"],
  ["project export", "DRIFT-010 evidence"],
  [".local/plans/", "DRIFT-012 snapshot-only under board_only"],
  [".cursor/skills/canvas-artifacts/SKILL.md", "ADR-010 canvas/plan tiers"],
];

const PATTERNS = [
  ["Write scope", "Drift artifacts only — no product-code"],
  ["Board lifecycle", "list --status in_progress; close drift-pass → done"],
  ["Tier-1", "Shared Board rights; no silent tracker dual-write"],
  ["Dual-write remediation", "Notes or handoff to board / implementer via Ready"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/drift-guard via --agent"],
];

const ARTIFACTS = [
  [".local/workflow-artifacts/drift/drift-audit.md", "Exit", "Maintainers / implementer"],
  [".local/workflow-artifacts/drift/drift-todos.md", "Exit", "Maintainers / implementer"],
  ["history/updates-log.md", "Exit", "Continuity readers"],
  ["Board drift-pass card Status", "done / in_review", "board / implementer"],
  [
    ".local/generated-data/project-board-snapshot.json",
    "project export",
    "DRIFT-010 · deprecated HTML ICC (EA-010) offline only",
  ],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "Later flush"],
];

const PEERS = [
  ["Outbound", "board", "Dual-write remediation via Ready"],
  ["Outbound", "implementer", "Dual-write remediation via Ready"],
  ["Inbound", "implementer", "Invokes on P0/P1 after drift-validate"],
  ["Inbound", "auditor", "audit-orchestration Phase 3 — after tracker/doc edits"],
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
  const nodeW = 118;
  const nodeH = 36;
  const layout = computeDAGLayout({
    nodes,
    edges,
    direction: "horizontal",
    nodeWidth: nodeW,
    nodeHeight: nodeH,
    rankGap: 36,
    nodeGap: 16,
  });

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ maxWidth: 920 }}
    >
      {layout.edges.map((e, i) => (
        <line
          key={i}
          x1={e.sourceX}
          y1={e.sourceY}
          x2={e.targetX}
          y2={e.targetY}
          stroke={tokens.stroke.secondary}
          strokeWidth={1.5}
          strokeDasharray={e.isBackEdge ? "4 3" : undefined}
        />
      ))}
      {layout.nodes.map((n) => (
        <g key={n.id}>
          <rect
            x={n.x}
            y={n.y}
            width={nodeW}
            height={nodeH}
            rx={4}
            fill={tokens.fill.secondary}
            stroke={tokens.stroke.primary}
          />
          <text
            x={n.x + nodeW / 2}
            y={n.y + nodeH / 2 + 4}
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

export default function AgentDriftGuardCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>drift-guard</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="warning" size="sm">
            drift artifacts only
          </Pill>
        </Row>
        <Text tone="secondary">
          drift-guard Agent Colony — Continuous goal/plan/agent-doctrine/docs
          coherence + DRIFT-001…012; remediations via Notes/Ready (not auditor
          deep scorecard).
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="MUST status" label="Entry when board on" />
        <Stat value="DRIFT-009…012" label="Board + roster pulse" />
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
            ? "Entry MUST: project entry (live|conserve|offline_artifacts) when board on."
            : "Fallback: session-pointer. Resume board sync when available."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. project entry (prefer over unfiltered list; board required when on).</Text>
          <Text>2. Run drift validate; check DRIFT-009 / 010 / 011 / 012 (kit-dev).</Text>
          <Text>3. Goal pulse: board Acceptance/Notes + plan pointers + roster.</Text>
          <Text>4. project export --reuse-if-fresh for DRIFT-010 when needed.</Text>
          <Text>
            5. Write drift-audit.md + drift-todos.md under
            .local/workflow-artifacts/drift/.
          </Text>
          <Text>
            6. drift-pass card done/in_review; gaps → Notes or handoff to
            board/implementer via Ready; updates-log.
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
              Write scope limited to drift artifacts — no product-code changes.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Entry MUST: project entry when board SSOT enabled; scoped list only in live mode.
            </Text>
            <Text>
              Exit: drift-pass card Status done/in_review; dual-write findings → Notes
              or handoff to board/implementer via Ready.
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
        Kit server agent-colony-mcp for drift validate — prefer cursor_workflow project
        for board. External: only servers listed for this agent in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
