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
const SOURCES = ".cursor/agents/verifier.md · board-ssot/SKILL.md § Continuation";

const GOALS = [
  "Claims vs evidence; minimal high-signal checks",
  "Restate claim, gather evidence, run smallest decisive checks",
  "Verdict: Verified | Partial | Not verified with one next action",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "notes" },
  { id: "claim" },
  { id: "restate" },
  { id: "checks" },
  { id: "verdict" },
  { id: "handoff" },
  { id: "next" },
];

const BOARD_EDGES = [
  { from: "status", to: "notes" },
  { from: "notes", to: "claim" },
  { from: "claim", to: "restate" },
  { from: "restate", to: "checks" },
  { from: "checks", to: "verdict" },
  { from: "verdict", to: "handoff" },
  { from: "handoff", to: "next" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "restate" },
  { id: "checks" },
  { id: "verdict" },
  { id: "handoff" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "restate" },
  { from: "restate", to: "checks" },
  { from: "checks", to: "verdict" },
  { from: "verdict", to: "handoff" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project entry",
  notes: "board card Notes",
  claim: "claim card",
  restate: "restate claim",
  checks: "smallest checks",
  verdict: "Verified|Partial|Not",
  handoff: "handoff / claim",
  next: "next agent",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  restate: "restate claim",
  checks: "smallest checks",
  verdict: "Verified|Partial|Not",
  handoff: "handoff / close",
};

const READ_FIRST = [
  [".cursor/agents/verifier.md", "Agent card (canon)"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".local/index-and-planning/current/session-pointer.md", "Fallback Entry"],
  [".local/workflow-artifacts/pr/", "When maintainer workflow in play"],
  [".cursor/skills/canvas-artifacts/SKILL.md", "ADR-010 canvas/plan tiers"],
];

const PATTERNS = [
  ["Consume only", "Do NOT create-from-template"],
  ["Board lifecycle", "Evidence on handed-off card; promote not primary path"],
  ["Tier-1", "Shared Board rights; Start date on claim / first In progress"],
  ["Checks", "pytest · prepare.py resolve_gates() · governance · verify_publish"],
  ["Merge gate", "Do not approve merge without pr/ artifacts when maintainer workflow active"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/verifier via --agent verifier"],
];

const ARTIFACTS = [
  ["change-index.md", "If findings change status", "Next agents / humans"],
  ["Board Status + Notes", "Exit (done or in_review + failure Notes)", "Next agent"],
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
  ["Inbound", "implementer", "Exit recipe prefers --next verifier"],
  ["Inbound", "test-runner", "When tests gate the PR"],
  ["Outbound", "implementer", "Not verified — stay in_review + failure Notes"],
  ["Outbound", "next (generic)", "handoff format per card when verified"],
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

export default function AgentVerifierCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>verifier</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            consume only
          </Pill>
        </Row>
        <Text tone="secondary">
          verifier Agent Colony — Claims vs evidence; minimal high-signal checks.
          No primary skill folder (agent card is canon).
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board-first Anchor" />
        <Stat value="consume only" label="No create-from-template" />
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
            ? "Entry: project entry + board card Notes. Always verify claims vs evidence. No dual-write."
            : "Entry: session-pointer.md. Always verify claims vs evidence."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. Restate the claim under verification.</Text>
          <Text>2. Gather evidence from repo, artifacts, and board Notes.</Text>
          <Text>
            3. Run smallest decisive checks (pytest; same category as prepare.py
            resolve_gates(); governance when policy docs change; verify_publish).
          </Text>
          <Text>4. Verdict: Verified | Partial | Not verified.</Text>
          <Text>5. One next action; handoff/claim. Status done or in_review with failure Notes.</Text>
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
              Verifier consumes artifacts; does not create-from-template or dual-write
              tracker Status.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Entry: project entry + board card Notes. Claim card for verification
              work.
            </Text>
            <Text>
              Exit: handoff/claim; Status done or leave in_review with failure Notes.
            </Text>
            <Text>
              change-index if findings change status. Do not dual-write work-tracker
              Status under board_only.
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
        Kit server agent-colony-mcp for PR scripts / prepare.py resolve_gates() —
        prefer cursor_workflow project for board. External: only servers listed
        for this agent in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
