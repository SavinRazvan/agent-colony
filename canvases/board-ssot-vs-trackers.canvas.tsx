/**
 * File: board-ssot-vs-trackers.canvas.tsx
 * Path: canvases/board-ssot-vs-trackers.canvas.tsx
 * Role: Clarify writable Status SSOT — GitHub Project (board_only) vs offline local trackers.
 * Used By:
 *  - humans / agents orienting ADR-008
 *  - agents-artifacts-board (peer hub for day-to-day board + .local artifacts)
 * Depends On:
 *  - ADR-008 · AGENTS.md · project-ssot-precedence.mdc · token-efficiency.md
 * Notes:
 *  - Concept hub (not agent-*). Excluded from DOC-008 roster scan.
 *  - Not "board vs kit" and not "board vs local artifacts" — artifacts coexist.
 *  - Former slug: board-ssot-vs-kit (historical filename).
 */

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

type Mode = "board" | "offline" | "compare";

const VERIFIED = "2026-08-06";
const SOURCES =
  "ADR-008 · AGENTS.md · project-ssot-precedence.mdc · token-efficiency.md · project-board-collaboration.md";

const OFFLINE_NODES = [
  { id: "agent" },
  { id: "session" },
  { id: "plan" },
  { id: "tracker" },
  { id: "code" },
  { id: "pr" },
];

const OFFLINE_EDGES = [
  { from: "agent", to: "session" },
  { from: "session", to: "plan" },
  { from: "plan", to: "tracker" },
  { from: "tracker", to: "code" },
  { from: "code", to: "pr" },
];

const BOARD_NODES = [
  { id: "yaml" },
  { id: "agent" },
  { id: "entry" },
  { id: "board" },
  { id: "code" },
  { id: "pr" },
  { id: "merge" },
  { id: "export" },
  { id: "snapshot" },
];

const BOARD_EDGES = [
  { from: "yaml", to: "agent" },
  { from: "agent", to: "entry" },
  { from: "entry", to: "board" },
  { from: "board", to: "code" },
  { from: "code", to: "pr" },
  { from: "pr", to: "merge" },
  { from: "merge", to: "board" },
  { from: "entry", to: "export" },
  { from: "export", to: "snapshot" },
];

const LABELS: Record<string, string> = {
  agent: "Cursor agents",
  session: "session-pointer.md",
  plan: "plan.md",
  tracker: "work-tracker.md",
  code: "Code + tests",
  pr: "PR Pattern A",
  yaml: "project_ssot YAML",
  entry: "project entry",
  board: "GitHub Project",
  merge: "merge.py → Done",
  export: "export [--reuse]",
  snapshot: "board snapshot.json",
};

const THREE_LAYERS: string[][] = [
  [
    "Live board",
    "Quota healthy · board_only",
    "Yes — only writable Status",
    "project entry → claim / handoff / Notes",
  ],
  [
    "Outbox JSONL",
    "Writes throttled (EXIT_QUEUED=6)",
    "No — buffer only",
    "project queue / outbox flush when GraphQL recovers",
  ],
  [
    "Offline trackers + snapshots",
    "Board off / unreachable / offline_artifacts",
    "Fallback only — resume board when up",
    ".local/index-and-planning/current · project-board-snapshot.json",
  ],
];

const COMPARE_ROWS: string[][] = [
  ["Writable Status SSOT", "work-tracker / session-pointer", "GitHub Project Status"],
  ["Agent Entry", "session-pointer → plan → tracker", "project entry → get / claim"],
  ["Agent Exit", "Update tracker in_progress", "set-status + append-notes on board"],
  ["Live plan / Acceptance", "plan.md", "Board card body (board_only)"],
  [".local PR / audit / drift artifacts", "Evidence (always)", "Evidence (always) — not Status"],
  ["Outbox", "N/A", "board-outbox.jsonl on CODE=6"],
  ["Dual-write Status", "Single writer (markdown)", "Forbidden — DRIFT-009"],
  ["Stale PR / roster / plan guards", "N/A / limited", "DRIFT-010 · 011 · 012"],
  ["PR merge gates", "prepare.py resolve_gates()", "Unchanged (local_only)"],
  ["When to use", "project_ssot off or no gh", "project_ssot.enabled + board_only"],
];

const LOCAL_ALWAYS: string[][] = [
  ["PR Pattern A (review / prep / merge.md)", "Merge readiness evidence — not Status"],
  ["Audit / drift / alignment under .local/workflow-artifacts/", "Evidence bundles"],
  ["board-outbox.jsonl + graphql quota cache", "Rate-limit buffer — flush restores board"],
  ["project-board-snapshot.json", "Read-only export cache (DRIFT-010)"],
  [".local/canvases/ · .local/plans/", "ADR-010 evidence / plan history only"],
  [".venv, secrets, .coverage", "Machine-local protected paths"],
  [
    "Offline trackers (session-pointer / plan / work-tracker)",
    "Only when board disabled or unavailable — never compete under board_only",
  ],
];

function FlowDiagram({ mode }: { mode: "board" | "offline" }) {
  const theme = useHostTheme();
  const nodes = mode === "offline" ? OFFLINE_NODES : BOARD_NODES;
  const edges = mode === "offline" ? OFFLINE_EDGES : BOARD_EDGES;
  const layout = computeDAGLayout({
    nodes,
    edges,
    direction: "horizontal",
    nodeWidth: mode === "offline" ? 132 : 112,
    nodeHeight: 40,
    rankGap: 44,
    nodeGap: 18,
    padding: 12,
  });

  const accentIds =
    mode === "offline"
      ? new Set(["session", "plan", "tracker"])
      : new Set(["yaml", "entry", "board", "merge"]);

  const readOnlyIds =
    mode === "board" ? new Set(["export", "snapshot"]) : new Set();

  const nodeW = mode === "offline" ? 132 : 112;

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ display: "block", maxWidth: 900 }}
    >
      {layout.edges.map((e, i) => (
        <line
          key={i}
          x1={e.sourceX}
          y1={e.sourceY}
          x2={e.targetX}
          y2={e.targetY}
          stroke={theme.stroke.secondary}
          strokeWidth={1.5}
          strokeDasharray={
            readOnlyIds.has(e.from) || readOnlyIds.has(e.to) ? "4 3" : undefined
          }
        />
      ))}
      {layout.nodes.map((n) => {
        const hot = accentIds.has(n.id);
        const readOnly = readOnlyIds.has(n.id);
        return (
          <g key={n.id}>
            <rect
              x={n.x}
              y={n.y}
              width={nodeW}
              height={40}
              rx={4}
              fill={hot ? theme.fill.secondary : theme.fill.tertiary}
              stroke={
                readOnly
                  ? theme.stroke.secondary
                  : hot
                    ? theme.accent.primary
                    : theme.stroke.primary
              }
              strokeWidth={hot ? 1.5 : 1}
              strokeDasharray={readOnly ? "3 2" : undefined}
            />
            <text
              x={n.x + nodeW / 2}
              y={n.y + 24}
              textAnchor="middle"
              fill={theme.text.primary}
              fontSize={10}
            >
              {LABELS[n.id] ?? n.id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function Legend() {
  const theme = useHostTheme();
  return (
    <Row gap={16} wrap>
      <Row gap={8} align="center">
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: 3,
            background: theme.fill.secondary,
            border: `1.5px solid ${theme.accent.primary}`,
          }}
        />
        <Text size="small" tone="secondary">
          Writable Status SSOT
        </Text>
      </Row>
      <Row gap={8} align="center">
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: 3,
            background: theme.fill.tertiary,
            border: `1px dashed ${theme.stroke.secondary}`,
          }}
        />
        <Text size="small" tone="secondary">
          Read-only export (never Status)
        </Text>
      </Row>
      <Row gap={8} align="center">
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: 3,
            background: theme.fill.tertiary,
            border: `1px solid ${theme.stroke.primary}`,
          }}
        />
        <Text size="small" tone="secondary">
          Execution (code / PR gates)
        </Text>
      </Row>
    </Row>
  );
}

export default function BoardSsotVsTrackersCanvas() {
  const [mode, setMode] = useCanvasState<Mode>("view-mode", "board");
  const [showLocal, setShowLocal] = useCanvasState<boolean>("show-local", true);

  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 960 }}>
      <Stack gap={8}>
        <Row gap={10} align="center" wrap>
          <H1 style={{ margin: 0 }}>Writable SSOT: board vs offline trackers</H1>
          <Pill size="sm" tone="info">
            hub · not an agent
          </Pill>
        </Row>
        <Text tone="secondary">
          What is the only place agents may write Status? Under board_only it is
          the GitHub Project. Offline local trackers are a fallback when the board
          is off or unreachable — not a second live Status.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED}
        </Text>
      </Stack>

      <Callout tone="warning" title="Do not confuse these">
        <Stack gap={6}>
          <Text>
            Not “board SSOT vs kit” — this repo is the kit/product (Agent Colony).
          </Text>
          <Text>
            Not “board vs local artifacts” — .local evidence (PR, audit, drift,
            outbox, snapshots) always coexists. Day-to-day map: agents-artifacts-board
            canvas.
          </Text>
          <Text>
            This hub only answers: where does writable Status live?
          </Text>
        </Stack>
      </Callout>

      <Grid columns={3} gap={12}>
        <Stat value="GitHub Project" label="board_only Status" tone="success" />
        <Stat value="Trackers" label="offline fallback only" />
        <Stat value=".local/" label="evidence (always)" />
      </Grid>

      <H2>Three coordination layers</H2>
      <Table
        headers={["Layer", "When", "Writable Status?", "How agents use it"]}
        rows={THREE_LAYERS}
        striped
      />

      <Divider />

      <Row gap={8} wrap>
        <Pill active={mode === "board"} onClick={() => setMode("board")}>
          board_only (default)
        </Pill>
        <Pill active={mode === "offline"} onClick={() => setMode("offline")}>
          Offline trackers
        </Pill>
        <Pill active={mode === "compare"} onClick={() => setMode("compare")}>
          Side-by-side
        </Pill>
      </Row>

      {(mode === "board" || mode === "compare") && (
        <Stack gap={10}>
          <H2>board_only — GitHub Project is Status SSOT</H2>
          <Text tone="secondary">
            Entry via project entry (live | conserve | offline_artifacts). Exit
            updates Status + Notes. Dashed path = read-only export for DRIFT-010.
          </Text>
          <Legend />
          <FlowDiagram mode="board" />
          <Card>
            <CardHeader>Agent loop</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small">
                  1. project entry → get/claim one card · read Notes
                </Text>
                <Text size="small">
                  2. Work — Acceptance on card body; code + tests
                </Text>
                <Text size="small">
                  3. Exit — handoff / set-status + append-notes
                </Text>
                <Text size="small">
                  4. CODE=6 → outbox; flush later — do not dual-write trackers
                </Text>
                <Text size="small">
                  5. Post-merge — merge.py → Done + Notes (PR URL + SHA)
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      )}

      {(mode === "offline" || mode === "compare") && (
        <Stack gap={10}>
          <H2>Offline — local trackers are Status fallback</H2>
          <Text tone="secondary">
            Used when project_ssot is disabled or gh/Projects unavailable
            (fallback: local_trackers). Resume board sync when available — never
            silent dual-write under board_only.
          </Text>
          <Legend />
          <FlowDiagram mode="offline" />
          <Card>
            <CardHeader>Agent loop (fallback)</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small">1. session-pointer → plan → work-tracker</Text>
                <Text size="small">2. One in_progress row in work-tracker.md</Text>
                <Text size="small">3. Implement → tests → update trackers</Text>
                <Text size="small">
                  4. PR Pattern A still local — merge is code-side
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      )}

      <Divider />

      <H2>Concern matrix</H2>
      <Table
        headers={["Concern", "Offline trackers", "board_only"]}
        rows={COMPARE_ROWS}
        striped
      />

      <Row gap={10} align="center">
        <Toggle checked={showLocal} onChange={setShowLocal} />
        <Text size="small">Show what always stays local (evidence)</Text>
      </Row>

      {showLocal ? (
        <Stack gap={8}>
          <H2>.local always (not competing Status)</H2>
          <Callout tone="info" title="Artifacts ≠ SSOT">
            These paths are evidence, buffers, and history. They do not replace
            board Status under board_only. See agents-artifacts-board for who
            writes what.
          </Callout>
          <Table headers={["Keep local", "Why"]} rows={LOCAL_ALWAYS} striped />
        </Stack>
      ) : null}

      <CollapsibleSection title="History — how board_only shipped (optional)" defaultOpen={false}>
        <Stack gap={8}>
          <Text size="small" tone="secondary">
            Migration A→B→C (PR #2), FIX-NOTES-DI (PR #3), STANDALONE product
            decision 2026-07-18. Useful archive — not required for day-to-day.
          </Text>
          <Table
            headers={["Slice", "Outcome"]}
            rows={[
              ["A — Writable SSOT docs", "ADR-008 · continuation · DRIFT-009"],
              ["B — Post-merge board sync", "merge.py → Done + Notes"],
              ["C — Export + DRIFT-010/011", "Read-only snapshot; never Status"],
              ["FIX-NOTES-DI", "append-notes DraftIssue DI_ resolve"],
              ["CLI + Metric A", "26 project leaves · 1455 tests · Metric A 100%"],
            ]}
          />
        </Stack>
      </CollapsibleSection>

      <Callout tone="neutral" title="Peer hubs">
        agents-artifacts-board — board + .local who-writes-what ·
        agent-board-collaboration — handoff DAG · github-api-safety — quota /
        outbox / project entry
      </Callout>

      <Spacer height={4} />
      <Text size="small" tone="tertiary">
        Caption: {SOURCES} · verified {VERIFIED}. Former filename
        board-ssot-vs-kit.canvas.tsx.
      </Text>
    </Stack>
  );
}
