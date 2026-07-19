import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  Pill,
  Row,
  Select,
  Spacer,
  Stack,
  Stat,
  Table,
  Text,
  computeDAGLayout,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

const VERIFIED = "2026-07-19";
const SOURCES =
  ".cursor/agents/*.md PEERS · audit-orchestration Phase 3 · project-board-ssot § Continuation · agent-roster edges";

const NODE_W = 128;
const NODE_H = 40;

type AgentId =
  | "project-board"
  | "implementer"
  | "verifier"
  | "test-runner"
  | "integrator-mas-agent"
  | "enterprise-auditor"
  | "workflow-drift-guard"
  | "researcher"
  | "all";

const AGENTS: { id: Exclude<AgentId, "all">; role: string; lane: string }[] = [
  {
    id: "project-board",
    role: "Triage Ready; create cards; hand off work",
    lane: "Coordination",
  },
  {
    id: "implementer",
    role: "Ship slices: code, tests, promote, PR path",
    lane: "Delivery",
  },
  {
    id: "test-runner",
    role: "Module tests / coverage on existing card",
    lane: "Delivery",
  },
  {
    id: "verifier",
    role: "Claims vs evidence; no implement",
    lane: "Delivery",
  },
  {
    id: "integrator-mas-agent",
    role: "Wire agents/skills/MCP into the kit",
    lane: "Infrastructure",
  },
  {
    id: "enterprise-auditor",
    role: "Evidence-only architecture audit artifacts",
    lane: "Quality",
  },
  {
    id: "workflow-drift-guard",
    role: "Drift validate; dual-write remediation",
    lane: "Quality",
  },
  {
    id: "researcher",
    role: "Adaptive Brief research packs (no product PRs)",
    lane: "Optional",
  },
];

/** Handoff edges from agent cards; test-runner→verifier also in skill chain when tests gate PR. */
const RELATIONS: {
  from: Exclude<AgentId, "all">;
  to: Exclude<AgentId, "all">;
  via: string;
  when: string;
}[] = [
  {
    from: "project-board",
    to: "implementer",
    via: "handoff next=implementer",
    when: "After triage / create-from-template + claim",
  },
  {
    from: "implementer",
    to: "verifier",
    via: "handoff --next verifier --to in_review",
    when: "PR-ready or slice ready for evidence check",
  },
  {
    from: "implementer",
    to: "test-runner",
    via: "handoff / Notes",
    when: "Tests or coverage needed before merge",
  },
  {
    from: "implementer",
    to: "workflow-drift-guard",
    via: "invoke after drift-validate",
    when: "P0/P1 findings need drift artifacts",
  },
  {
    from: "workflow-drift-guard",
    to: "project-board",
    via: "Ready / Notes remediation",
    when: "Confirmed dual-write — triage card",
  },
  {
    from: "workflow-drift-guard",
    to: "implementer",
    via: "Ready / Notes remediation",
    when: "Confirmed dual-write — fix in slice",
  },
  {
    from: "enterprise-auditor",
    to: "implementer",
    via: "Notes + artifact paths",
    when: "Audit card closed; implementer applies actions",
  },
  {
    from: "enterprise-auditor",
    to: "workflow-drift-guard",
    via: "audit-orchestration Phase 3",
    when: "After tracker/doc edits; P0/P1 drift findings",
  },
  {
    from: "enterprise-auditor",
    to: "verifier",
    via: "audit-orchestration Phase 3",
    when: "Spot-check top audit claims vs preflight + repo paths",
  },
  {
    from: "integrator-mas-agent",
    to: "implementer",
    via: "escalate product src/",
    when: "Integration needs product code",
  },
  {
    from: "integrator-mas-agent",
    to: "test-runner",
    via: "escalate coverage",
    when: "Integration needs test module work",
  },
  {
    from: "integrator-mas-agent",
    to: "enterprise-auditor",
    via: "escalate architecture",
    when: "Integration is architecture-impacting",
  },
  {
    from: "test-runner",
    to: "verifier",
    via: "handoff --to in_review",
    when: "Tests gate the PR",
  },
  {
    from: "verifier",
    to: "implementer",
    via: "stay in_review + failure Notes",
    when: "Not verified — implementer fixes",
  },
];

const RESEARCHER_REDIRECTS: [string, string][] = [
  ["implementer", "Product code / commits / PRs"],
  ["verifier", "Claims vs evidence checks"],
  ["enterprise-auditor", "Architecture audits"],
  ["workflow-drift-guard", "Drift / tracker coherence"],
];

const HAPPY_PATH = [
  ["1", "project-board", "Ready card; Priority/Size/Estimate triage"],
  ["2", "implementer", "claim → code/tests → promote or mention-pr"],
  ["3", "test-runner", "Optional: coverage on same card"],
  ["4", "verifier", "Evidence check → done or back to implementer"],
  ["5", "merge.py", "Post-merge Status → Done (Pattern A)"],
];

const LANES: [string, string][] = [
  ["Coordination", "project-board"],
  ["Delivery", "implementer · test-runner · verifier"],
  ["Infrastructure", "integrator-mas-agent"],
  ["Quality", "enterprise-auditor · workflow-drift-guard"],
  ["Optional", "researcher"],
];

const DAG_NODES = AGENTS.filter((a) => a.id !== "researcher").map((a) => ({
  id: a.id,
}));

const DAG_EDGES = RELATIONS.filter(
  (r) => r.from !== "researcher" && r.to !== "researcher",
).map((r) => ({ from: r.from, to: r.to }));

function RelationDag({
  focus,
  tokens,
}: {
  focus: AgentId;
  tokens: ReturnType<typeof useHostTheme>["tokens"];
}) {
  const layout = computeDAGLayout({
    nodes: DAG_NODES,
    edges: DAG_EDGES,
    direction: "horizontal",
    nodeWidth: NODE_W,
    nodeHeight: NODE_H,
    rankGap: 44,
    nodeGap: 18,
  });
  const byId = Object.fromEntries(layout.nodes.map((n) => [n.id, n]));

  const related = new Set<string>();
  if (focus !== "all") {
    related.add(focus);
    for (const r of RELATIONS) {
      if (r.from === focus) related.add(r.to);
      if (r.to === focus) related.add(r.from);
    }
  }

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ maxWidth: 980 }}
    >
      {layout.edges.map((e, i) => {
        const active =
          focus === "all" ||
          (related.has(e.from) &&
            related.has(e.to) &&
            (e.from === focus || e.to === focus));
        const dimmed = focus !== "all" && !active;
        return (
          <line
            key={`${e.from}-${e.to}-${i}`}
            x1={e.sourceX}
            y1={e.sourceY}
            x2={e.targetX}
            y2={e.targetY}
            stroke={
              dimmed
                ? tokens.stroke.tertiary
                : active
                  ? tokens.accent.primary
                  : tokens.stroke.secondary
            }
            strokeWidth={active && focus !== "all" ? 2.5 : 1.5}
            strokeDasharray={e.isBackEdge ? "4 3" : undefined}
            opacity={dimmed ? 0.25 : 1}
          />
        );
      })}
      {layout.nodes.map((n) => {
        const dimmed = focus !== "all" && !related.has(n.id);
        const isFocus = n.id === focus;
        const label =
          n.id.length > 16 ? `${n.id.slice(0, 14)}…` : n.id;
        return (
          <g key={n.id} opacity={dimmed ? 0.3 : 1}>
            <rect
              x={n.x}
              y={n.y}
              width={NODE_W}
              height={NODE_H}
              rx={6}
              fill={isFocus ? tokens.fill.secondary : tokens.fill.tertiary}
              stroke={
                isFocus ? tokens.accent.primary : tokens.stroke.secondary
              }
              strokeWidth={isFocus ? 2 : 1}
            />
            <text
              x={n.x + NODE_W / 2}
              y={n.y + NODE_H / 2 + 4}
              textAnchor="middle"
              fill={tokens.text.primary}
              fontSize={11}
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              {label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function AgentRelationsCanvas() {
  const { tokens } = useHostTheme();
  const [focus, setFocus] = useCanvasState<AgentId>("focus", "all");

  const focusedRows =
    focus === "all"
      ? RELATIONS.map((r) => [r.from, "→", r.to, r.via, r.when])
      : RELATIONS.filter((r) => r.from === focus || r.to === focus).map((r) => [
          r.from,
          r.from === focus ? "→ out" : "← in",
          r.to,
          r.via,
          r.when,
        ]);

  const focusMeta = AGENTS.find((a) => a.id === focus);

  const outbound =
    focus === "all"
      ? RELATIONS.length
      : RELATIONS.filter((r) => r.from === focus).length;
  const inbound =
    focus === "all"
      ? RELATIONS.length
      : RELATIONS.filter((r) => r.to === focus).length;

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 1000 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>Agent relations</H1>
          <Pill tone="info" size="sm">
            8 agents
          </Pill>
        </Row>
        <Text tone="secondary">
          How kit agents hand off work — edges from agent cards plus skill chain
          (e.g. test-runner→verifier when tests gate the PR). Select an agent to
          highlight its neighbors.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED}
        </Text>
      </Stack>

      <Row gap={12} style={{ alignItems: "center", flexWrap: "wrap" }}>
        <Text weight="semibold" size="small">
          Focus
        </Text>
        <Select
          value={focus}
          onChange={(v) => setFocus(v as AgentId)}
          options={[
            { value: "all", label: "All relations" },
            ...AGENTS.map((a) => ({ value: a.id, label: a.id })),
          ]}
        />
        {focusMeta ? (
          <Text tone="secondary" size="small">
            {focusMeta.lane} · {focusMeta.role}
          </Text>
        ) : null}
      </Row>

      <Grid columns={3} gap={12}>
        <Stat value={String(AGENTS.length)} label="Agents" />
        <Stat
          value={String(focus === "all" ? RELATIONS.length : outbound)}
          label={focus === "all" ? "Handoff edges" : "Outbound"}
        />
        <Stat
          value={String(focus === "all" ? "5" : inbound)}
          label={focus === "all" ? "Lanes" : "Inbound"}
        />
      </Grid>

      <Card>
        <CardHeader
          trailing={
            <Pill size="sm" tone="neutral">
              DAG
            </Pill>
          }
        >
          Collaboration graph (researcher omitted — redirects only)
        </CardHeader>
        <CardBody>
          <RelationDag focus={focus} tokens={tokens} />
          <Text tone="tertiary" size="small">
            Accent edges = selected agent’s handoffs. Dashed = back-edge (cycle).
            researcher has no product edges — see redirects below.
          </Text>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Happy path (typical slice)</H2>
        <Table
          headers={["Step", "Actor", "What happens"]}
          rows={HAPPY_PATH}
        />
      </Stack>

      <Divider />

      <Stack gap={8}>
        <H2>
          {focus === "all"
            ? "All handoff relations"
            : `Relations for ${focus}`}
        </H2>
        {focusedRows.length === 0 ? (
          <Callout tone="neutral" title="No direct handoff edges">
            This agent redirects to product agents or is consume-only with
            generic next. See role cards and researcher redirects.
          </Callout>
        ) : (
          <Table
            headers={["From", "Dir", "To", "Via", "When"]}
            rows={focusedRows}
          />
        )}
      </Stack>

      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader>Lanes</CardHeader>
          <CardBody>
            <Table headers={["Lane", "Agents"]} rows={LANES} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>researcher redirects</CardHeader>
          <CardBody>
            <Table
              headers={["Hand to", "Why"]}
              rows={RESEARCHER_REDIRECTS}
            />
            <Spacer />
            <Text size="small" tone="tertiary">
              Hard stop: write only under _research_results/; no product
              commit/push/PR.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Callout tone="info" title="Shared board contract">
        Every agent: Entry = project status / claim; Exit = Status + Notes.
        Tier-1: Start date on first In progress; Size/Estimate per skill table. Promote
        Draft→Issue via promote-to-issue or mention-pr (auto when
        promote_to_issue_on_pr) before shippable PR — claim does not auto-promote.
        Notes: @owner.github_user/&lt;agent&gt; · YYYY-MM-DDTHH:MM:SSZ · … via
        append-notes --agent. Board is the only writable Status SSOT when board_only.
      </Callout>

      <Text size="small" tone="tertiary">
        Peer canvases: agent-roster (card edges) · agent-board-collaboration
        (board SSOT hub) · per-agent canvases under canvases/agent-*.canvas.tsx
      </Text>
    </Stack>
  );
}
