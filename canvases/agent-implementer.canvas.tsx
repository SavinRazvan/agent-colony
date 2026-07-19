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

const VERIFIED = "2026-07-19";
const SOURCES =
  ".cursor/agents/implementer.md · implementation-execution-loop/SKILL.md · project-board-ssot/SKILL.md § Continuation";

const GOALS = [
  "Disciplined implementation slices with trackers and Pattern A gates",
  "Small, reversible slices with production quality",
  "Clear module boundaries, tests, and board Status (or fallback trackers)",
];

const BOARD_NODES = [
  { id: "yaml" },
  { id: "status" },
  { id: "claim" },
  { id: "code" },
  { id: "gates" },
  { id: "evidence" },
  { id: "promote" },
  { id: "handoff" },
  { id: "next" },
];

const BOARD_EDGES = [
  { from: "yaml", to: "status" },
  { from: "status", to: "claim" },
  { from: "claim", to: "code" },
  { from: "code", to: "gates" },
  { from: "gates", to: "evidence" },
  { from: "evidence", to: "promote" },
  { from: "promote", to: "handoff" },
  { from: "handoff", to: "next" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "plan" },
  { id: "tracker" },
  { id: "code" },
  { id: "gates" },
  { id: "evidence" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "plan" },
  { from: "plan", to: "tracker" },
  { from: "tracker", to: "code" },
  { from: "code", to: "gates" },
  { from: "gates", to: "evidence" },
  { from: "evidence", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  yaml: "project_ssot YAML",
  status: "project status",
  claim: "claim (+ Start date if empty)",
  code: "contracts → code → tests",
  gates: "prepare.py GATES",
  evidence: "change-index + updates-log",
  promote: "promote / mention-pr",
  handoff: "handoff --next verifier",
  next: "verifier (typical)",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  plan: "plan.md",
  tracker: "work-tracker.md",
  code: "contracts → code → tests",
  gates: "prepare.py GATES",
  evidence: "change-index + updates-log",
  close: "close tracker (offline)",
};

const READ_FIRST = [
  [".cursor/skills/implementation-execution-loop/SKILL.md", "Slice lifecycle"],
  [".cursor/skills/project-board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".ai_infra/templates/project-board/README.md", "When creating cards"],
  [".local/user_settings/github.collaboration.yaml", "project_ssot block"],
  [".local/index-and-planning/current/architecture.md", "Architecture stub"],
  ["session-pointer / plan / work-tracker", "Fallback only"],
  ["test-plan.md / test-index.md", "When tests or ownership change"],
];

const ARTIFACTS = [
  [
    "change-index.md",
    "Exit / close",
    "Next agents, humans",
  ],
  [
    "history/updates-log.md",
    "One line per close",
    "Drift / continuity readers",
  ],
  [
    "test-plan.md / test-index.md",
    "When tests change",
    "test-runner",
  ],
  [
    "coverage-index (make coverage-index)",
    "When coverage mattered",
    "ICC / maintainers",
  ],
  [
    "Board Status + Notes",
    "Exit (board_only)",
    "verifier / next agent",
  ],
  [
    ".local/generated-data/board-outbox.jsonl",
    "EXIT_QUEUED (6)",
    "Later flush (any agent/human)",
  ],
];

const PATTERNS = [
  ["Pattern A recipes", "claim --last / handoff --last / create-from-template"],
  ["Tier-1", "claim/set-status→In progress Start date; Size/Estimate per skill table"],
  ["Promote before PR", "promote-to-issue OR mention-pr (auto when promote_to_issue_on_pr)"],
  ["Templates", "slice (feature/chore) · bug (defect/fix)"],
  ["Module headers", "file-docstring-header-relations.mdc on new sources"],
  ["Commit trailers", "Author + GitHub-User via contributors commit-trailers"],
  ["Gates", "prepare.py GATES; check_governance_consistency when policy docs change"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/implementer via --agent implementer"],
];

const PEERS = [
  ["Outbound", "verifier", "handoff --next verifier (Exit recipe)"],
  ["Outbound", "workflow-drift-guard", "When make drift-validate finds P0/P1 needing artifacts"],
  ["Inbound", "project-board", "Triage hands Ready cards for implementation"],
  ["Inbound", "enterprise-auditor", "Audit Notes / artifact paths for implementer to apply"],
  ["Escalation (integrator)", "integrator may hand product src/ to implementer", "integrator card"],
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

export default function AgentImplementerCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>implementer</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            STANDALONE product
          </Pill>
        </Row>
        <Text tone="secondary">
          Disciplined implementation slices with trackers and Pattern A gates.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board-first Anchor" />
        <Stat value="verifier" label="Typical next (Exit recipe)" />
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
            ? "GitHub Project is the only writable Status SSOT. Do not dual-write work-tracker in_progress."
            : "Read session-pointer then plan/work-tracker. Resume board sync when available."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>
            1. One primary claimed card (in_progress) when SSOT on; else one
            in_progress in work-tracker.md. Scope on card body or plan.md.
          </Text>
          <Text>
            2. Contracts → implementation → tests. New sources: module header
            (file-docstring-header-relations.mdc).
          </Text>
          <Text>
            3. Gates: python .ai_infra/scripts/pr/prepare.py (or its GATES). Add
            check_governance_consistency.py if governance/policy docs changed.
          </Text>
          <Text>
            4. Commits: contributors commit-trailers. Optional Assisted-by. No
            tool-generated human sign-off.
          </Text>
          <Text>
            5. Close: board Status via CLI; change-index + updates-log; make
            drift-validate; hand off to workflow-drift-guard on P0/P1 findings.
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
              rowTone={READ_FIRST.map(() => "neutral" as const)}
            />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Artifacts</CardHeader>
          <CardBody>
            <Table
              headers={["Path", "When", "Consumed by"]}
              rows={ARTIFACTS}
            />
            <Spacer size={8} />
            <Text tone="tertiary" size="small">
              Tier 2 .local/workflow-artifacts/ (PR/audit) stay local — implementer
              is not primary writer of review/prep/merge artifacts.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Rights: Status + Notes on the card you touch. Prefer claim --last /
              handoff --last --agent implementer → @owner.github_user/implementer.
            </Text>
            <Text>
              Exit recipe: project handoff --last --agent implementer --next
              verifier --to in_review (or --to done).
            </Text>
            <Text>
              Templates: create-from-template --template slice|bug then claim
              --last. Project README is human-only.
            </Text>
            <Text>
              Rate-limit: EXIT_QUEUED (6) → outbox status / flush; continue local
              evidence; do not hammer GraphQL.
            </Text>
            <Text>
              CLI helper: project guide. Canon: project-board-ssot/SKILL.md §
              Continuation.
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Peers</H2>
        <Table
          headers={["Direction", "Agent", "Evidence"]}
          rows={PEERS}
        />
      </Stack>

      <Callout tone="neutral" title="MCP">
        Kit server workflow-kit for PR scripts/gates — prefer cursor_workflow
        project for board. External: only servers listed for this agent in
        mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact
        paths.
      </Text>
    </Stack>
  );
}
