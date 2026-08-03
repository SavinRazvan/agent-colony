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
  ".cursor/agents/auditor.md · auditor-protocol/SKILL.md · board-ssot/SKILL.md";

const GOALS = [
  "Evidence-only enterprise architecture audit",
  "Writes workflow artifacts and tracker hooks for other agents",
  "Propose edits in audit-actions; implementer applies",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "create" },
  { id: "claim" },
  { id: "audit" },
  { id: "artifacts" },
  { id: "notes" },
  { id: "handoff" },
];

const BOARD_EDGES = [
  { from: "status", to: "create" },
  { from: "create", to: "claim" },
  { from: "claim", to: "audit" },
  { from: "audit", to: "artifacts" },
  { from: "artifacts", to: "notes" },
  { from: "notes", to: "handoff" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "audit" },
  { id: "artifacts" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "audit" },
  { from: "audit", to: "artifacts" },
  { from: "artifacts", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project status",
  create: "create [AUDIT] slice",
  claim: "claim --last",
  audit: "evidence-only audit",
  artifacts: "audit + alignment",
  notes: "artifact paths",
  handoff: "→ implementer",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  audit: "evidence-only audit",
  artifacts: "audit + alignment",
  close: "updates-log",
};

const READ_FIRST = [
  [".cursor/skills/auditor-protocol/SKILL.md", "Audit canon"],
  [".cursor/skills/audit-module-map/SKILL.md", "Optional deep map"],
  [".cursor/skills/audit-orchestration/SKILL.md", "Optional orchestration"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".ai_infra/docs/roadmap/alignment-audit-schema.md", "Alignment schema"],
];

const PATTERNS = [
  ["create-from-template", "slice [AUDIT] then claim --last"],
  ["Board lifecycle", "Notes = artifact paths; Status in_review/done"],
  ["Tier-1", "Shared Board rights; Start date on claim / first In progress"],
  ["Tracker etiquette", "Propose edits in audit-actions; implementer applies"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/auditor via --agent"],
];

const ARTIFACTS = [
  [
    ".local/workflow-artifacts/enterprise-architecture-audit/enterprise-architecture-audit.md",
    "Exit",
    "implementer / maintainers",
  ],
  [
    ".local/workflow-artifacts/enterprise-architecture-audit/enterprise-audit-actions.md",
    "Exit",
    "implementer applies",
  ],
  [
    ".local/workflow-artifacts/alignment/alignment-audit.md",
    "Optional (merge workflow)",
    "implementer / maintainers",
  ],
  [
    ".local/workflow-artifacts/alignment/alignment-todos.md",
    "Optional (merge workflow)",
    "implementer applies",
  ],
  ["change-index.md", "Exit", "Next agents / humans"],
  ["history/updates-log.md", "Exit", "Continuity readers"],
  ["Board Status + Notes", "in_review / done", "implementer"],
  [
    ".local/generated-data/project-board-snapshot.json",
    "project export (read-only)",
    "Deprecated HTML ICC (EA-010) — offline only; prefer board + Open Canvas",
  ],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "Later flush"],
];

const PEERS = [
  ["Outbound", "implementer", "Continue from Notes with artifact paths"],
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

export default function AgentEnterpriseAuditorCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>auditor</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            evidence only
          </Pill>
        </Row>
        <Text tone="secondary">
          Evidence-only enterprise architecture audit; writes workflow artifacts and
          tracker hooks for other agents.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board-first Anchor" />
        <Stat value="implementer" label="Typical next (Notes)" />
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
            ? "Entry: project status; may create-from-template slice [AUDIT] then claim."
            : "Fallback: session-pointer. Audits write .local/ artifacts only."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. project status; create [AUDIT] slice card if needed; claim.</Text>
          <Text>2. Evidence-only audit per auditor-protocol/SKILL.md.</Text>
          <Text>
            3. Write enterprise-architecture-audit.md + enterprise-audit-actions.md;
            optional alignment artifacts for merge workflow.
          </Text>
          <Text>4. Propose tracker edits in audit-actions — implementer applies.</Text>
          <Text>
            5. Exit: artifacts + change-index + updates-log; Status in_review/done;
            Notes with artifact paths for implementer.
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
              Audits are advisory — findings only; implementer applies tracker edits.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              May create-from-template --template slice [AUDIT] then claim --last.
            </Text>
            <Text>
              Exit: Status in_review or done; Notes with artifact paths for
              implementer.
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
        Kit server workflow-kit for audit scripts — prefer cursor_workflow project for
        board. External: only servers listed for this agent in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
