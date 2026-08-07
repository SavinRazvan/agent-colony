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
  ".cursor/agents/board.md · board-ssot/SKILL.md · board-shell/SKILL.md · ADR-006 · ADR-008";

const GOALS = [
  "Independent-governed helper for GitHub Project SSOT",
  "First-run: coach default Playground shell (board-shell)",
  "List/create/move cards via project_ssot CLI",
  "Triage Ready cards and hand off to implementer",
];

const BOARD_NODES = [
  { id: "yaml" },
  { id: "bootstrap" },
  { id: "status" },
  { id: "list" },
  { id: "triage" },
  { id: "create" },
  { id: "claim" },
  { id: "handoff" },
];

const BOARD_EDGES = [
  { from: "yaml", to: "bootstrap" },
  { from: "bootstrap", to: "status" },
  { from: "status", to: "list" },
  { from: "list", to: "triage" },
  { from: "triage", to: "create" },
  { from: "create", to: "claim" },
  { from: "claim", to: "handoff" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "trackers" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "trackers" },
  { from: "trackers", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  yaml: "project_ssot YAML",
  bootstrap: "board-bootstrap --check",
  status: "project entry",
  list: "list ready",
  triage: "move Status",
  create: "create-from-template",
  claim: "claim --last",
  handoff: "→ implementer",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  trackers: "local trackers",
  close: "updates-log",
};

const READ_FIRST = [
  [".cursor/skills/board-ssot/SKILL.md", "Board SSOT canon"],
  [".cursor/skills/board-shell/SKILL.md", "First-run Playground shell coach"],
  [".ai_infra/templates/project-board/board-shell.schema.yaml", "Kit default desired state"],
  [".local/user_settings/github.collaboration.yaml", "project_ssot block"],
  [".ai_infra/templates/project-board/README.md", "Card templates"],
  ["ADR-006", "Independent-governed agent"],
  ["ADR-008", "Project board SSOT (board_only)"],
  [".cursor/skills/canvas-artifacts/SKILL.md", "ADR-010 canvas/plan tiers"],
];

const PATTERNS = [
  ["Independent-governed", "Not in default PR pipelines"],
  ["First-run shell", "board-bootstrap --check → views-setup until Playground six-view green"],
  ["Loop", "status → list ready → create-from-template + claim --last → handoff"],
  ["Triage Tier-1", "set-field Priority/Size/Estimate (skill Size↔Estimate table)"],
  ["Promote", "promote-to-issue OR mention-pr auto (promote_to_issue_on_pr) before shippable PR"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/board via --agent"],
];

const ARTIFACTS = [
  ["change-index.md", "Exit", "Next agents / humans"],
  ["history/updates-log.md", "Exit", "Continuity readers"],
  ["Board Status + Notes", "Every triage", "implementer / next agent"],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "Later flush"],
  [
    ".local/plans/",
    "plan snapshot|list (history)",
    "Agents execute; humans plan open",
  ],
  [
    ".local/canvases/",
    "canvas save (session evidence)",
    "canvas-artifacts skill",
  ],
];

const PEERS = [
  ["Outbound", "implementer", "handoff next=implementer (typical)"],
  ["Inbound", "drift-guard", "Dual-write remediation via Ready"],
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

export default function AgentBoardCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>board</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            independent-governed
          </Pill>
        </Row>
        <Text tone="secondary">
          board Agent Colony — Independent-governed helper — list/create/move
          GitHub Project SSOT cards via project_ssot CLI.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board SSOT triage" />
        <Stat value="implementer" label="Typical handoff next" />
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
            ? "Entry: YAML + skill + project entry (quota-aware). Primary board triage agent."
            : "Fallback: session-pointer + local trackers. Resume board sync when available."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. Read YAML + board-ssot skill; project entry.</Text>
          <Text>2. list --status ready (or other triage views).</Text>
          <Text>3. create-from-template + claim --last for new work.</Text>
          <Text>4. Move Status for every triage action.</Text>
          <Text>
            5. Exit: Status for every triage; change-index; updates-log; handoff
            next=implementer|….
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
              Primary writer of board Status/Notes during triage — not product code.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Rights: list/create/move GitHub Project SSOT cards via agent_colony
              project CLI.
            </Text>
            <Text>
              Exit: Status for every triage; change-index; updates-log; handoff
              --next implementer (typical).
            </Text>
            <Text>
              Rate-limit: EXIT_QUEUED (6) → outbox status / flush; do not hammer
              GraphQL.
            </Text>
            <Text>CLI helper: project guide. ADR-006 independent-governed · ADR-008 board_only SSOT.</Text>
          </Stack>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Peers</H2>
        <Table headers={["Direction", "Agent", "Evidence"]} rows={PEERS} />
      </Stack>

      <Callout tone="neutral" title="MCP">
        Prefer agent_colony project for all board operations. External: only
        servers listed for this agent in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
