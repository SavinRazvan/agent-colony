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

const VERIFIED = "2026-09-14";
const SOURCES =
  ".cursor/agents/auditor.md · auditor-protocol/SKILL.md · board-ssot/SKILL.md";

const GOALS = [
  "Deep/periodic evidence architecture audit (CHK-* checklists)",
  "Security/perf/granularity/docs/agent-contracts — not continuous plan pulse",
  "Artifacts only; implementer applies Ready cards from actions/todos",
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
  status: "api-ready → project entry",
  create: "create-from-template --template audit",
  claim: "claim --last",
  audit: "evidence-only audit",
  artifacts: "audit + alignment",
  notes: "artifact paths",
  handoff: "→ verifier (in_review)",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  audit: "evidence-only audit",
  artifacts: "audit + alignment",
  close: "updates-log",
};

const READ_FIRST = [
  [".cursor/skills/auditor-protocol/SKILL.md", "CHK-* checklists + phases"],
  [".cursor/skills/agent-surface-parity/SKILL.md", "Per-agent doc/canvas vs machine"],
  [".cursor/skills/audit-module-map/SKILL.md", "Optional deep map"],
  [".cursor/skills/audit-orchestration/SKILL.md", "Quarterly vs PR cadence"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".ai_infra/docs/roadmap/alignment-audit-schema.md", "Alignment schema"],
  [".cursor/skills/canvas-artifacts/SKILL.md", "ADR-010 canvas/plan tiers"],
];

const PATTERNS = [
  ["create-from-template", "--template audit then claim --last"],
  ["Board lifecycle", "Notes = artifact paths; in_review then verifier for Done"],
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
    "Required (arch-impacting merge)",
    "merge Schema-1 / maintainers",
  ],
  [
    ".local/workflow-artifacts/alignment/alignment-todos.md",
    "Required (arch-impacting merge)",
    "implementer applies",
  ],
  ["change-index.md", "Exit", "Next agents / humans"],
  ["history/updates-log.md", "Exit", "Continuity readers"],
  ["Board Status + Notes", "in_review then verifier for Done", "verifier"],
  [
    ".local/generated-data/project-board-snapshot.json",
    "project export (read-only)",
    "DRIFT-010 evidence for drift-guard",
  ],
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
  ["Outbound", "verifier", "must handoff --next verifier on [AUDIT] (EXIT_VALIDATION)"],
  ["Outbound", "implementer", "Continue from Notes with artifact paths"],
  ["Outbound", "drift-guard", "orch Phase 3 — goal pulse + DRIFT validate"],
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

export default function AgentAuditorCanvas() {
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
          auditor Agent Colony — Deep/periodic evidence architecture audit
          (CHK-* security/perf/granularity/docs); not continuous plan pulse.
          Writes workflow artifacts for other agents.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board-first Anchor" />
        <Stat value="verifier" label="Must next when [AUDIT]" tone="warning" />
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
            ? "Entry: project api-ready then project entry; may create-from-template --template audit then claim."
            : "Fallback: session-pointer. Audits write .local/ artifacts only."}
        </Callout>
        <Callout tone="danger" title="Machine gate — [AUDIT] is shippable">
          Must handoff --next verifier --to in_review before Done. CLI EXIT_VALIDATION
          (5) without verifier hop / allow-skip. Commissioned-By ≠ Audited-By (ADR-013).
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. project api-ready then project entry; create --template audit card if needed; claim.</Text>
          <Text>
            2. Evidence-only audit per auditor-protocol — tick CHK-ARCH /
            GRANULARITY / PERF / SEC-CODE / SEC-AGENT / INFRA-KIT / DOCS (full or
            focused table for touched surfaces).
          </Text>
          <Text>
            3. Write .local/workflow-artifacts/enterprise-architecture-audit/
            enterprise-architecture-audit.md + enterprise-audit-actions.md
            (artifact dir name kept; skill is auditor-protocol); Schema-1
            alignment/ mandatory for arch-impacting merges (even zero findings).
          </Text>
          <Text>4. Propose tracker edits in audit-actions — implementer applies.</Text>
          <Text>
            5. Exit: artifacts + change-index + updates-log; must handoff --next
            verifier --to in_review on [AUDIT] (EXIT_VALIDATION without hop);
            Notes with artifact paths; orch Phase 3 → drift-guard goal pulse as needed.
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
              Remediation is findings-only (no auto-fix in audit pass). Merge gate is not advisory — Schema-1 must PASS; open P0/P1 status fails.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Entry: project api-ready then project entry. May create-from-template
              --template audit then claim --last.
            </Text>
            <Text>
              Exit: prefer handoff --next verifier --to in_review — [AUDIT] cards
              are shippable (PR / [AUDIT] / P0|P1 gate); Notes with artifact paths.
            </Text>
            <Text>
              Rate-limit: api-ready → EXIT_QUEUED (6) → cooldown/outbox status|list → flush; do not hammer
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
        Prefer workflow_check_audit_artifacts for Schema-1 scans; agent_colony
        project for board. External: only servers listed for this agent in
        mcp.registry.yaml. Kit inventory: 29 tools.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
