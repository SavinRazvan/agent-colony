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
  ".cursor/agents/integrator-mas-agent.md · mas-infrastructure-integration/SKILL.md · project-board-ssot/SKILL.md";

const GOALS = [
  "Integrates new agents, skills, MCP, and infrastructure expansions",
  "Procedural, evidence-only, Pattern A",
  "Escalate to enterprise-auditor, test-runner, implementer, PR maintainer skills",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "skill" },
  { id: "claim" },
  { id: "intake" },
  { id: "wire" },
  { id: "verify" },
  { id: "handoff" },
];

const BOARD_EDGES = [
  { from: "status", to: "skill" },
  { from: "skill", to: "claim" },
  { from: "claim", to: "intake" },
  { from: "intake", to: "wire" },
  { from: "wire", to: "verify" },
  { from: "verify", to: "handoff" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "intake" },
  { id: "wire" },
  { id: "verify" },
  { id: "handoff" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "intake" },
  { from: "intake", to: "wire" },
  { from: "wire", to: "verify" },
  { from: "verify", to: "handoff" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project status",
  skill: "mas-infrastructure",
  claim: "claim / create card",
  intake: "Intake → Plan",
  wire: "templates → wire",
  verify: "validate + gates",
  handoff: "escalate / close",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  intake: "Intake → Plan",
  wire: "templates → wire",
  verify: "validate + gates",
  handoff: "escalate / close",
};

const READ_FIRST = [
  [".cursor/skills/mas-infrastructure-integration/SKILL.md", "Integration canon"],
  [".cursor/skills/project-board-ssot/SKILL.md", "When project_ssot.enabled"],
  ["python3 -m cursor_workflow integrate validate", "Wire verification"],
  ["check_governance_consistency.py", "When policy docs change"],
];

const PATTERNS = [
  ["Pattern A", "claim --last / handoff --last / create-from-template"],
  ["Promote before PR", "promote-to-issue OR mention-pr when shipping integration"],
  ["Tier-1", "claim → Start date; set-field estimate on own card"],
  ["STANDALONE", "Product lives only in mas-workflow-kit-project-ssot"],
  ["Notes timestamp", "@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · … via --agent"],
  ["Attribution", "@owner.github_user/integrator-mas-agent via --agent"],
];

const ARTIFACTS = [
  ["change-index.md", "Exit", "Next agents / humans"],
  ["history/updates-log.md", "Exit", "Continuity readers"],
  ["Board Status + Notes", "Exit (validate outcomes)", "implementer / escalations"],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "Later flush"],
];

const PEERS = [
  ["Escalation", "enterprise-auditor", "Architecture-impacting integration"],
  ["Escalation", "test-runner", "Coverage work"],
  ["Escalation", "implementer", "Product src/ handoff"],
  ["Escalation", "PR maintainer skills", "pr-workflow pipeline"],
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

export default function AgentIntegratorMasAgentCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>integrator-mas-agent</H1>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            STANDALONE product
          </Pill>
        </Row>
        <Text tone="secondary">
          Integrates new agents, skills, MCP, and infrastructure expansions —
          procedural, evidence-only, Pattern A.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="Entry→Exit" label="Board-first Anchor" />
        <Stat value="integrate validate" label="Wire verification" />
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
            ? "Entry: project status + mas-infrastructure-integration skill; claim/create card."
            : "Fallback: session-pointer. Resume board sync when available."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>1. Intake: read integration request; project status + skill.</Text>
          <Text>2. Plan: board card with scope and acceptance criteria.</Text>
          <Text>3. Templates → wire agents/skills/MCP into kit structure.</Text>
          <Text>
            4. Verify: contributors validate, gates, governance consistency,
            integrate validate.
          </Text>
          <Text>
            5. Handoff: Status done or in_review if verify failed; Notes with
            validate outcomes; change-index; updates-log.
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
              Escalates product src/, coverage, audits, and PR work to peer agents.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Entry: project status + mas-infrastructure-integration skill;
              claim/create card.
            </Text>
            <Text>
              Exit: Status done or in_review if verify failed; Notes with validate
              outcomes.
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
        Kit server workflow-kit for integrate validate — prefer cursor_workflow
        project for board. External: only servers listed for this agent in
        mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
