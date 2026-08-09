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

/**
 * Whole-picture hub: agents ↔ GitHub Project board ↔ local artifacts.
 * Not an agent-* canvas — excluded from DOC-008 roster scan (same as board-ssot-vs-trackers).
 */

const VERIFIED = "2026-08-06";
const SOURCES =
  "ADR-008 · ADR-010 · ADR-007 · board-ssot/SKILL.md · canvas-artifacts/SKILL.md · project-board-collaboration.md · agent cards · drift/auditor quality split";

const NODE_W = 128;
const NODE_H = 40;
const LOOP_W = 760;
const LOOP_H = 360;

type ViewMode = "loop" | "who-writes";

type LoopId =
  | "yaml"
  | "entry"
  | "board"
  | "agent"
  | "code"
  | "artifacts"
  | "exit"
  | "pr";

/** Manual positions — auto DAG + on-edge labels overlapped on this cycle. */
const LOOP_POS: Record<LoopId, { x: number; y: number; hub?: boolean }> = {
  yaml: { x: 24, y: 28 },
  entry: { x: 200, y: 28 },
  board: { x: 400, y: 28, hub: true },
  agent: { x: 400, y: 140 },
  code: { x: 200, y: 140 },
  artifacts: { x: 600, y: 140 },
  pr: { x: 200, y: 260 },
  exit: { x: 600, y: 260 },
};

const LOOP_LABELS: Record<LoopId, string> = {
  yaml: "project_ssot YAML",
  entry: "project entry",
  board: "GitHub Project",
  agent: "Cursor agent",
  code: "Code + tests",
  artifacts: ".local artifacts",
  exit: "Exit: Status+Notes",
  pr: "PR Pattern A",
};

type LoopEdge = {
  from: LoopId;
  to: LoopId;
  kind: "main" | "evidence" | "back";
  via: string;
};

const LOOP_EDGES: LoopEdge[] = [
  { from: "yaml", to: "entry", kind: "main", via: "enabled + board_only" },
  { from: "entry", to: "board", kind: "main", via: "get / claim" },
  { from: "board", to: "agent", kind: "main", via: "card body + Notes" },
  { from: "agent", to: "code", kind: "main", via: "implement / test" },
  {
    from: "agent",
    to: "artifacts",
    kind: "evidence",
    via: "audit · drift · verify",
  },
  { from: "code", to: "pr", kind: "main", via: "review → prepare → merge" },
  { from: "artifacts", to: "exit", kind: "evidence", via: "paths in Notes" },
  { from: "exit", to: "board", kind: "back", via: "only writable Status" },
  { from: "pr", to: "board", kind: "back", via: "mention-pr · merge Done" },
];

const WHO_WRITES: string[][] = [
  [
    "board",
    "Board Status / Notes / fields",
    "(rarely) continuity Notes only",
    "Triage Ready; handoff next=…",
  ],
  [
    "implementer",
    "claim · handoff · promote · mention-pr",
    "change-index; live plan on board card (board_only)",
    "Ships code; PR path; plan snapshot on exit",
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
    ".local/workflow-artifacts/pr/ (claims vs evidence Notes)",
    "Claims vs evidence (no code fixes)",
  ],
  [
    "auditor",
    "Audit card Status + CHK-* / alignment paths in Notes",
    ".local/workflow-artifacts/enterprise-architecture-audit/ · alignment/",
    "Deep/periodic — no product fixes; not continuous plan pulse",
  ],
  [
    "drift-guard",
    "Drift-pass card Done; remediation via Ready",
    ".local/workflow-artifacts/drift/drift-audit.md · drift-todos.md",
    "Goal pulse + DRIFT scripts; never silent dual-write Status",
  ],
  [
    "integrator",
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
    "All agents via agent_colony project …",
    "ADR-008 board_only — only Status writer",
  ],
  [
    "Day-0 board shell",
    "board-bootstrap --check · views-setup.md · board-shell",
    "board / human (before claim)",
    "Does not write Status — Playground six-view gate",
  ],
  [
    "PR Pattern A (local evidence)",
    ".local/workflow-artifacts/pr/{review,prep,merge}.md",
    "review-pr · prepare-pr · merge-pr",
    "prepare.py resolve_gates() — not a second Status",
  ],
  [
    "Audit / alignment",
    ".local/workflow-artifacts/enterprise-architecture-audit/",
    "auditor",
    "Actions backlog for implementer",
  ],
  [
    "Drift",
    ".local/workflow-artifacts/drift/",
    "drift-guard",
    "Goal pulse + DRIFT-009…012 (011 roster; 012 plan snapshots)",
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
  [
    "Session canvases (local evidence)",
    ".local/canvases/",
    "Any agent via canvas save",
    "ADR-010 — sync to IDE with canvas sync",
  ],
  [
    "Plan snapshots (history only)",
    ".local/plans/",
    "plan snapshot · plan list (agents); plan open (human Build)",
    "Live plan = board card under board_only — DRIFT-012",
  ],
];

const HAPPY_PATH = [
  "1. Entry — project entry (scoped list in live; snapshot in conserve)",
  "2. claim --last --agent <name> (Start date on In progress when configured)",
  "3. Work — code/tests and/or write .local artifacts",
  "4. Exit — handoff --to in_review|done + Notes (@user/agent · UTC · …)",
  "5. Plan — agents: plan list → read .local/plans/; humans: plan open for Build",
  "6. PR — mention-pr; merge.py can set card Done",
];

function port(
  id: LoopId,
  side: "left" | "right" | "top" | "bottom",
): { x: number; y: number } {
  const p = LOOP_POS[id];
  const cx = p.x + NODE_W / 2;
  const cy = p.y + NODE_H / 2;
  if (side === "left") return { x: p.x, y: cy };
  if (side === "right") return { x: p.x + NODE_W, y: cy };
  if (side === "top") return { x: cx, y: p.y };
  return { x: cx, y: p.y + NODE_H };
}

function edgePath(e: LoopEdge): string {
  // Prefer orthogonal-ish curves so return-to-board arcs clear the mid row.
  if (e.from === "yaml" && e.to === "entry") {
    const s = port("yaml", "right");
    const t = port("entry", "left");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "entry" && e.to === "board") {
    const s = port("entry", "right");
    const t = port("board", "left");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "board" && e.to === "agent") {
    const s = port("board", "bottom");
    const t = port("agent", "top");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "agent" && e.to === "code") {
    const s = port("agent", "left");
    const t = port("code", "right");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "agent" && e.to === "artifacts") {
    const s = port("agent", "right");
    const t = port("artifacts", "left");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "code" && e.to === "pr") {
    const s = port("code", "bottom");
    const t = port("pr", "top");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "artifacts" && e.to === "exit") {
    const s = port("artifacts", "bottom");
    const t = port("exit", "top");
    return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
  }
  if (e.from === "exit" && e.to === "board") {
    const s = port("exit", "top");
    const t = port("board", "right");
    return `M ${s.x} ${s.y} Q 720 80 ${t.x} ${t.y}`;
  }
  if (e.from === "pr" && e.to === "board") {
    const s = port("pr", "left");
    const t = port("board", "left");
    // Left rail return — clears mid-row nodes
    return `M ${s.x} ${s.y} L 48 ${s.y} L 48 ${t.y} L ${t.x} ${t.y}`;
  }
  const s = port(e.from, "right");
  const t = port(e.to, "left");
  return `M ${s.x} ${s.y} L ${t.x} ${t.y}`;
}

function LoopDag({
  tokens,
}: {
  tokens: ReturnType<typeof useHostTheme>["tokens"];
}) {
  const order: LoopId[] = [
    "yaml",
    "entry",
    "board",
    "agent",
    "code",
    "artifacts",
    "pr",
    "exit",
  ];

  return (
    <Stack gap={12}>
      <svg
        width="100%"
        viewBox={`0 0 ${LOOP_W} ${LOOP_H}`}
        style={{ maxWidth: 760 }}
      >
        {/* Lane bands */}
        <rect
          x={12}
          y={16}
          width={LOOP_W - 24}
          height={64}
          rx={6}
          fill={tokens.fill.tertiary}
          opacity={0.4}
        />
        <text x={20} y={14} fill={tokens.text.tertiary} fontSize={9}>
          Config → Entry → Board hub
        </text>
        <rect
          x={12}
          y={128}
          width={LOOP_W - 24}
          height={64}
          rx={6}
          fill={tokens.fill.tertiary}
          opacity={0.25}
        />
        <text x={20} y={126} fill={tokens.text.tertiary} fontSize={9}>
          Work: code · agent · .local evidence
        </text>
        <rect
          x={12}
          y={248}
          width={LOOP_W - 24}
          height={64}
          rx={6}
          fill={tokens.fill.tertiary}
          opacity={0.25}
        />
        <text x={20} y={246} fill={tokens.text.tertiary} fontSize={9}>
          Close: PR Pattern A · Exit Status+Notes → board
        </text>

        {LOOP_EDGES.map((e) => (
          <path
            key={`${e.from}→${e.to}`}
            d={edgePath(e)}
            fill="none"
            stroke={
              e.kind === "main"
                ? tokens.accent.primary
                : e.kind === "back"
                  ? tokens.stroke.secondary
                  : tokens.stroke.tertiary
            }
            strokeWidth={e.kind === "main" ? 2 : 1.35}
            strokeDasharray={e.kind === "back" ? "5 3" : undefined}
            opacity={e.kind === "evidence" ? 0.9 : 1}
          />
        ))}

        {order.map((id) => {
          const p = LOOP_POS[id];
          const hub = Boolean(p.hub);
          return (
            <g key={id}>
              <rect
                x={p.x}
                y={p.y}
                width={NODE_W}
                height={NODE_H}
                rx={6}
                fill={hub ? tokens.fill.primary : tokens.fill.secondary}
                stroke={
                  hub ? tokens.accent.primary : tokens.stroke.primary
                }
                strokeWidth={hub ? 2 : 1}
              />
              <text
                x={p.x + NODE_W / 2}
                y={p.y + NODE_H / 2 + 4}
                textAnchor="middle"
                fill={tokens.text.primary}
                fontSize={11}
                fontWeight={hub ? 600 : 400}
              >
                {LOOP_LABELS[id]}
              </text>
            </g>
          );
        })}
      </svg>

      <Row gap={10} wrap>
        <Pill size="sm" tone="info" active>
          solid accent = main path
        </Pill>
        <Pill size="sm" tone="neutral">
          muted = evidence (.local)
        </Pill>
        <Pill size="sm" tone="neutral">
          dashed = return to board
        </Pill>
      </Row>

      <Table
        headers={["From", "To", "Kind", "Via"]}
        rows={LOOP_EDGES.map((e) => [LOOP_LABELS[e.from], LOOP_LABELS[e.to], e.kind, e.via])}
        striped
      />
    </Stack>
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
        <Row gap={10} style={{ alignItems: "center", flexWrap: "wrap" }}>
          <H1 style={{ margin: 0 }}>Agents · artifacts · board</H1>
          <Pill size="sm" tone="info">
            hub · not an agent
          </Pill>
        </Row>
        <Text tone="secondary">
          Whole picture for board_only SSOT — who writes Status, who writes
          evidence, and how they meet on Exit. Live agent ids only (board ·
          implementer · test-runner · verifier · integrator · auditor ·
          drift-guard · researcher).
        </Text>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          <Pill size="sm" tone="neutral" active>
            ADR-008
          </Pill>
          <Pill size="sm" tone="neutral" active>
            ADR-010
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
        <Stat value="Entry" label="project entry" />
        <Stat value="Exit" label="Status + Notes" />
      </Grid>

      <Callout tone="info" title="Read order">
        Open this hub first for orientation. Detail hubs: agent-board-collaboration
        (recipes), agent-relations (handoff graph), board-ssot-vs-trackers (writable
        Status: board vs offline trackers), per-agent canvases for deep dive.
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
            PRs feed Notes — they do not replace Status. Edge labels are in the
            table under the diagram (not on the lines).
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
            auditor → CHK-* / .local audit + alignment artifacts → Notes paths →
            implementer Ready cards (deep/periodic; not continuous plan pulse).
            Does not mutate product code during audit.
          </Text>
          <Text size="small">
            implementer makes drift-validate → P0/P1 or goal-pulse gaps →
            drift-guard writes drift artifacts (DRIFT-001…012 kit-dev) →
            remediation via Notes/Ready (never silent tracker Status).
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
