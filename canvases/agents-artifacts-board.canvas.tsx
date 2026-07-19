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

/**
 * Whole-picture hub: agents ↔ GitHub Project board ↔ local artifacts.
 * Not an agent-* canvas — excluded from DOC-008 roster scan (same as board-ssot-vs-kit).
 */

const VERIFIED = "2026-07-19";
const SOURCES =
  "ADR-008 · project-board-ssot/SKILL.md · project-board-collaboration.md · agent cards · HYGIENE post-COV100";

const NODE_W = 118;
const NODE_H = 36;

type ViewMode = "loop" | "who-writes";

const LOOP_NODES = [
  { id: "yaml" },
  { id: "entry" },
  { id: "board" },
  { id: "agent" },
  { id: "code" },
  { id: "artifacts" },
  { id: "exit" },
  { id: "pr" },
];

const LOOP_EDGES = [
  { from: "yaml", to: "entry" },
  { from: "entry", to: "board" },
  { from: "board", to: "agent" },
  { from: "agent", to: "code" },
  { from: "agent", to: "artifacts" },
  { from: "code", to: "pr" },
  { from: "artifacts", to: "exit" },
  { from: "exit", to: "board" },
  { from: "pr", to: "board" },
];

const LOOP_LABELS: Record<string, string> = {
  yaml: "project_ssot YAML",
  entry: "Entry: project status",
  board: "GitHub Project",
  agent: "Cursor agent",
  code: "Code + tests",
  artifacts: ".local artifacts",
  exit: "Exit: Status + Notes",
  pr: "PR Pattern A",
};

const EDGE_HINTS: Record<string, string> = {
  "yaml→entry": "enabled + board_only",
  "entry→board": "list / claim",
  "board→agent": "card body + Notes",
  "agent→code": "implement / test",
  "agent→artifacts": "audit · drift · verify",
  "code→pr": "review → prepare → merge",
  "artifacts→exit": "paths in Notes",
  "exit→board": "only writable Status",
  "pr→board": "mention-pr · merge Done",
};

const WHO_WRITES: string[][] = [
  [
    "project-board",
    "Board Status / Notes / fields",
    "(rarely) continuity Notes only",
    "Triage Ready; handoff next=…",
  ],
  [
    "implementer",
    "claim · handoff · promote · mention-pr",
    "session/plan/change-index (offline mirror)",
    "Ships code; PR path",
  ],
  [
    "test-runner",
    "Notes on slice card",
    "test-index · coverage-index · updates-log",
    "Coverage evidence",
  ],
  [
    "verifier",
    "Done or In review + failure Notes",
    "verification-*.md under workflow-artifacts",
    "Claims vs evidence",
  ],
  [
    "enterprise-auditor",
    "Audit card Status + artifact paths in Notes",
    "enterprise-architecture-audit/ · alignment/",
    "Evidence-only — no product fixes",
  ],
  [
    "workflow-drift-guard",
    "Drift-pass card Done; remediation via Ready",
    "drift/drift-audit.md · drift-todos.md",
    "Never silent dual-write Status",
  ],
  [
    "integrator-mas-agent",
    "Integration card → Done",
    "integrate validate evidence in Notes",
    "Escalate product/coverage/arch",
  ],
  [
    "researcher",
    "Research card → Done",
    "_research_results packs (gitignored)",
    "No product PRs",
  ],
];

const ARTIFACT_LANES: string[][] = [
  [
    "Board (writable SSOT)",
    "GitHub Project Status · Notes · Linked PRs",
    "All agents via cursor_workflow project …",
    "ADR-008 board_only — only Status writer",
  ],
  [
    "PR Pattern A (local evidence)",
    ".local/workflow-artifacts/pr/{review,prep,merge}.md",
    "review-pr · prepare-pr · merge-pr",
    "Gates in prepare.py — not a second Status",
  ],
  [
    "Audit / alignment",
    ".local/workflow-artifacts/enterprise-architecture-audit/",
    "enterprise-auditor",
    "Actions backlog for implementer",
  ],
  [
    "Drift",
    ".local/workflow-artifacts/drift/",
    "workflow-drift-guard",
    "DRIFT-009 watches dual-write",
  ],
  [
    "Release / smoke",
    ".local/workflow-artifacts/release/",
    "maintainer · live-board-smoke",
    "Opt-in PROJECT_SSOT_LIVE",
  ],
  [
    "Offline fallback trackers",
    ".local/index-and-planning/current/*",
    "When board off / unavailable",
    "Never compete with board Status",
  ],
  [
    "Outbox (rate-limit buffer)",
    ".local/generated-data/board-outbox.jsonl",
    "Any agent on EXIT_QUEUED (6)",
    "Flush later — not a second SSOT",
  ],
];

const HAPPY_PATH = [
  "1. Entry — project status → list Ready / In progress",
  "2. claim --last --agent <name> (Start date when configured)",
  "3. Work — code/tests and/or write .local artifacts",
  "4. Exit — handoff --to in_review|done + Notes (@user/agent · UTC · …)",
  "5. PR — mention-pr; merge.py can set card Done",
];

function LoopDag({
  tokens,
}: {
  tokens: ReturnType<typeof useHostTheme>["tokens"];
}) {
  const layout = computeDAGLayout({
    nodes: LOOP_NODES,
    edges: LOOP_EDGES,
    direction: "horizontal",
    nodeWidth: NODE_W,
    nodeHeight: NODE_H,
    rankGap: 36,
    nodeGap: 16,
  });
  return (
    <svg
      width="100%"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ maxWidth: 980 }}
    >
      {layout.edges.map((e, i) => {
        const label = EDGE_HINTS[`${e.from}→${e.to}`] ?? "";
        const mx = (e.sourceX + e.targetX) / 2;
        const my = (e.sourceY + e.targetY) / 2 - 8;
        return (
          <g key={`e-${e.from}-${e.to}-${i}`}>
            <path
              d={`M ${e.sourceX} ${e.sourceY} C ${e.sourceX + 18} ${e.sourceY}, ${e.targetX - 18} ${e.targetY}, ${e.targetX} ${e.targetY}`}
              fill="none"
              stroke={
                e.isBackEdge
                  ? tokens.stroke.tertiary
                  : tokens.stroke.secondary
              }
              strokeWidth={1.25}
              strokeDasharray={e.isBackEdge ? "4 3" : undefined}
            />
            {label ? (
              <text
                x={mx}
                y={my}
                textAnchor="middle"
                fill={tokens.text.secondary}
                fontSize={9}
              >
                {label}
              </text>
            ) : null}
          </g>
        );
      })}
      {layout.nodes.map((n) => {
        const accent =
          n.id === "board" || n.id === "exit" || n.id === "entry";
        return (
          <g key={n.id}>
            <rect
              x={n.x}
              y={n.y}
              width={NODE_W}
              height={NODE_H}
              rx={6}
              fill={
                accent ? tokens.fill.secondary : tokens.fill.tertiary
              }
              stroke={
                n.id === "board" ? tokens.accent.primary : tokens.stroke.primary
              }
              strokeWidth={n.id === "board" ? 1.75 : 1}
            />
            <text
              x={n.x + NODE_W / 2}
              y={n.y + NODE_H / 2 + 4}
              textAnchor="middle"
              fill={tokens.text.primary}
              fontSize={10}
              fontWeight={n.id === "board" ? 600 : 400}
            >
              {LOOP_LABELS[n.id] ?? n.id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function ThreePlanes() {
  const planes: {
    title: string;
    tone: string;
    body: string;
    highlight: boolean;
  }[] = [
    {
      title: "Board",
      tone: "SSOT",
      body: "GitHub Project Status + Notes. Pattern A: claim · handoff · promote · mention-pr.",
      highlight: true,
    },
    {
      title: "Agents",
      tone: "Actors",
      body: "8 Cursor agents. Entry reads board; Exit updates Status. Parent Task-delegates.",
      highlight: false,
    },
    {
      title: "Artifacts",
      tone: "Evidence",
      body: ".local/workflow-artifacts + offline trackers. Never a second Status writer under board_only.",
      highlight: false,
    },
  ];
  return (
    <Grid columns={3} gap={12}>
      {planes.map((p) => (
        <div key={p.title}>
          <Card>
            <CardHeader
              trailing={
                <Pill size="sm" tone="neutral" active={p.highlight}>
                  {p.tone}
                </Pill>
              }
            >
              {p.title}
            </CardHeader>
            <CardBody>
              <Text size="small" tone="secondary">
                {p.body}
              </Text>
            </CardBody>
          </Card>
        </div>
      ))}
    </Grid>
  );
}

export default function AgentsArtifactsBoardCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<ViewMode>("viewMode", "loop");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 1040 }}>
      <Stack gap={6}>
        <H1>Agents · artifacts · board</H1>
        <Text tone="secondary">
          Whole picture for board_only SSOT — who writes Status, who writes
          evidence, and how they meet on Exit.
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill size="sm" tone="neutral" active>
            ADR-008
          </Pill>
          <Pill size="sm" tone="neutral">
            8 agents
          </Pill>
          <Pill size="sm" tone="neutral">
            Pattern A CLI
          </Pill>
          <Text size="small" tone="tertiary">
            Verified {VERIFIED}
          </Text>
        </Row>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="Board" label="Only writable Status" />
        <Stat value=".local" label="Evidence / fallback" />
        <Stat value="Entry" label="project status" />
        <Stat value="Exit" label="Status + Notes" />
      </Grid>

      <Callout tone="info" title="Read order">
        Open this hub first for orientation. Detail hubs: agent-board-collaboration
        (recipes), agent-relations (handoff graph), board-ssot-vs-kit (classic vs
        shipped), per-agent canvases for deep dive.
      </Callout>

      <Callout tone="warning" title="How to render kit canvases">
        Repo path canvases/*.canvas.tsx opens as source in the explorer. Live
        visualization: Ctrl+Shift+P → Open Canvas (managed copies under{" "}
        {`~/.cursor/projects/<workspace-id>/canvases/`}
        ). HTML Control Center is deprecated — prefer the GitHub Project board +
        Open Canvas.
      </Callout>

      <ThreePlanes />

      <Divider />

      <Row gap={12} style={{ alignItems: "center", flexWrap: "wrap" }}>
        <H2>Control loop</H2>
        <Text size="small" tone="secondary">
          {mode === "who-writes" ? "Who writes what" : "DAG loop"}
        </Text>
        <Toggle
          checked={mode === "who-writes"}
          onChange={(on) => setMode(on ? "who-writes" : "loop")}
        />
      </Row>

      {mode === "loop" ? (
        <Stack gap={10}>
          <Text size="small" tone="secondary">
            Board is the hub: Entry pulls work, Exit pushes Status. Artifacts and
            PRs feed Notes — they do not replace Status.
          </Text>
          <LoopDag tokens={tokens} />
          <Stack gap={4}>
            {HAPPY_PATH.map((line) => (
              <div key={line}>
                <Text size="small">{line}</Text>
              </div>
            ))}
          </Stack>
        </Stack>
      ) : (
        <Table
          headers={["Agent", "Writes on board", "Writes under .local", "Role"]}
          rows={WHO_WRITES}
          columnAlign={["left", "left", "left", "left"]}
        />
      )}

      <Divider />

      <H2>Artifact lanes</H2>
      <Text size="small" tone="secondary">
        Each lane has one job. Mixing Status into trackers under board_only is
        dual-write (DRIFT-009).
      </Text>
      <Spacer height={8} />
      <Table
        headers={["Lane", "Path / surface", "Primary writer", "Rule"]}
        rows={ARTIFACT_LANES}
        columnAlign={["left", "left", "left", "left"]}
      />

      <CollapsibleSection title="Side paths (audit / drift)">
        <Stack gap={8}>
          <Text size="small">
            enterprise-auditor → .local audit artifacts → Notes paths →
            implementer Ready cards. Does not mutate product code during audit.
          </Text>
          <Text size="small">
            implementer makes drift-validate → P0/P1 → workflow-drift-guard writes
            drift artifacts → remediation via Notes/Ready (never silent tracker
            Status).
          </Text>
          <Text size="small">
            Rate-limit EXIT_QUEUED (6) → board-outbox.jsonl → project outbox flush
            when GraphQL budget recovers.
          </Text>
        </Stack>
      </CollapsibleSection>

      <Text size="small" tone="tertiary">
        Sources: {SOURCES}
      </Text>
    </Stack>
  );
}
