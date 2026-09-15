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

const VERIFIED = "2026-09-15";
const SOURCES =
  ".cursor/agents/debugger.md · debug-protocol/SKILL.md · debug-handoff/SKILL.md · board-ssot/SKILL.md";

const GOALS = [
  "Campaign-scoped forensic investigation with redacted vault evidence",
  "Hypothesis experiments via debug capture / ingest / analyze — no durable product fixes on debug card",
  "Curate DBG / TR / SG findings; child bug|slice cards for implementer",
  "debug close + publish manifest hash in Notes; verifier hop when shippable",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "create" },
  { id: "claim" },
  { id: "init" },
  { id: "experiment" },
  { id: "findings" },
  { id: "close" },
  { id: "handoff" },
];

const BOARD_EDGES = [
  { from: "status", to: "create" },
  { from: "create", to: "claim" },
  { from: "claim", to: "init" },
  { from: "init", to: "experiment" },
  { from: "experiment", to: "findings" },
  { from: "findings", to: "close" },
  { from: "close", to: "handoff" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "init" },
  { id: "experiment" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "init" },
  { from: "init", to: "experiment" },
  { from: "experiment", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "api-ready → project entry",
  create: "create-from-template debug",
  claim: "claim --agent debugger",
  init: "debug init --slug",
  experiment: "capture · ingest · analyze",
  findings: "handoff child cards",
  close: "validate --final · close",
  handoff: "→ verifier | implementer",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  init: "debug init --slug",
  experiment: "capture · analyze",
  close: "validate --final · close",
};

const READ_FIRST = [
  [".cursor/skills/debug-protocol/SKILL.md", "Orchestration hub (lazy-load debug-*)"],
  [".cursor/skills/debug-handoff/SKILL.md", "Exit · publish manifest · verifier hop"],
  [".cursor/skills/evidence-first/SKILL.md", "Disproof doctrine"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".local/workflow-artifacts/debug/DEBUG_BOUNDARIES.md", "After debug init"],
  [".cursor/skills/canvas-artifacts/SKILL.md", "ADR-010 canvas/plan tiers"],
];

const PATTERNS = [
  ["create-from-template", "--template debug then claim --last --agent debugger"],
  ["Campaign slug", ".local/workflow-artifacts/debug/<slug>/ only"],
  ["Vault vs publish", "vault/ redacted; publish/ curated handoffs"],
  ["Child cards", "debug handoff → bug|slice for implementer (not product fixes here)"],
  ["Human hard stops", "debug block on prod probes · auth · PII · budget"],
  ["Not installed on lite", "consumer_lite excludes debugger + debug-* skills"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/debugger via --agent debugger"],
];

const ARTIFACTS = [
  [
    ".local/workflow-artifacts/debug/<slug>/INDEX.json",
    "After debug init",
    "Campaign SSOT under slug",
  ],
  [
    ".local/workflow-artifacts/debug/<slug>/vault/",
    "Experiments",
    "Redacted evidence (protected)",
  ],
  [
    ".local/workflow-artifacts/debug/<slug>/publish/",
    "Exit",
    "Curated manifest for handoffs",
  ],
  [
    ".local/workflow-artifacts/debug/<slug>/DEBUG-BRIEF.md",
    "Init",
    "Campaign scope + boundaries",
  ],
  ["Board Status + Notes", "Exit (manifest hash + validate PASS)", "verifier / implementer"],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "api-ready → list/drop → flush"],
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
  ["Inbound", "board", "create-from-template --template debug + triage"],
  ["Outbound", "implementer", "Child bug|slice cards via debug handoff + publish citations"],
  ["Outbound", "verifier", "Shippable debug campaigns — handoff --next verifier before Done"],
  ["Escalation", "human", "debug block on hard stops (prod probes · PII · budget)"],
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

export default function AgentDebuggerCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>debugger</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            full profile only
          </Pill>
        </Row>
        <Text tone="secondary">
          debugger Agent Colony — Master forensic investigation with redacted vault
          evidence, experiments, and curated publish handoffs.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Campaign under slug" />
        <Stat value="verifier" label="Shippable Done gate" tone="warning" />
        <Stat value="EXIT_QUEUED" label="Outbox on rate-limit" tone="warning" />
      </Grid>

      <Callout tone="danger" title="Boundary — not implementer or auditor">
        No durable product fixes, merge gates, or Schema-1 audit packs on the debug
        card. Route behavioral fixes to implementer via child cards. Shippable
        (PR / [AUDIT] / P0|P1) → handoff --next verifier --to in_review before
        Done.
      </Callout>

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
            ? "Entry: project api-ready then project entry; create-from-template --template debug + claim. Campaign evidence under .local/workflow-artifacts/debug/<slug>/."
            : "Entry: session-pointer.md; resume board sync when available."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>
            1. Entry: claim debug card; `debug init --slug … --item-id …` after
            claim.
          </Text>
          <Text>
            2. `debug inventory` → module/file ledgers; lazy-load debug-* skills
            by phase.
          </Text>
          <Text>
            3. Experiment: `debug capture` or `debug ingest` → `debug analyze`.
          </Text>
          <Text>
            4. Curate DBG/TR/SG findings → `debug handoff` → child bug|slice
            cards for implementer.
          </Text>
          <Text>
            5. Probe cleanup → `debug validate --final` → `debug close` → board
            Notes cite publish/ manifest hash.
          </Text>
          <Text>
            6. Shippable: `project handoff --last --agent debugger --next
            verifier --to in_review` before Done.
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
              Vault paths are protected (local-artifact-protection). Campaign
              closes immutable — supersede with new slug for follow-up.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Entry: create-from-template --template debug + claim --last --agent
              debugger. Own debug card; create child bug|slice with publish
              citations.
            </Text>
            <Text>
              Exit: Notes cite publish/ manifest hash and `debug validate --final`
              PASS; shippable → handoff --next verifier --to in_review.
            </Text>
            <Text>
              Rate-limit: api-ready → EXIT_QUEUED (6) → cooldown/outbox
              status|list → flush; do not hammer GraphQL.
            </Text>
            <Text>
              CLI: `python3 -m agent_colony debug …`. Canon: debug-protocol +
              debug-handoff skills.
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Peers</H2>
        <Table headers={["Direction", "Agent", "Evidence"]} rows={PEERS} />
      </Stack>

      <Callout tone="neutral" title="MCP">
        Kit server agent-colony-mcp for board/session — campaign actions use
        `agent_colony debug`, not new MCP tools. External: only servers listed
        for debugger in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact
        paths.
      </Text>
    </Stack>
  );
}
