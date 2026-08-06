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
const SOURCES =
  ".cursor/agents/researcher.md · research-corpus/SKILL.md · research_cli.py · .agents/skills/RESEARCH_WORKFLOW.md · live pack flexiai-toolsmith + verifier";

const GOALS = [
  "Adaptive Brief from chat, peer agent Notes/handoffs, or board research card",
  "Multi-round packs under _research_results/sources/<slug>/ + AGENT_BRIEF for MAS",
  "Hard-stop: write only _research_results/ — no product git/PR",
  "Anti-loop efficient: ≤6 rounds, one init/fetch, exit on validate PASS",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "intake" },
  { id: "cli" },
  { id: "rounds" },
  { id: "done" },
  { id: "notes" },
];

const BOARD_EDGES = [
  { from: "status", to: "intake" },
  { from: "intake", to: "cli" },
  { from: "cli", to: "rounds" },
  { from: "rounds", to: "done" },
  { from: "done", to: "notes" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "intake" },
  { id: "rounds" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "intake" },
  { from: "intake", to: "rounds" },
  { from: "rounds", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "project entry",
  intake: "adaptive Brief",
  cli: "research init/fetch",
  rounds: "rounds 1-6 + validate",
  done: "set-status done",
  notes: "AGENT_BRIEF paths",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer.md",
  intake: "adaptive Brief",
  rounds: "rounds 1-6 + validate",
  close: "local close",
};

const HOW_IT_WORKS = [
  ["1 Intake", "Normalize source (HTTPS | github: | path) + question → BRIEF.md"],
  ["2 Init/fetch", "research init → research fetch (shallow clone → cache/<slug>/)"],
  ["3 Map/extract", "MAP.md + findings/<lens>.md with path + ~Lnn evidence"],
  ["4 Deepen", "rounds/round-N.md only for open questions (cap ≤6)"],
  ["5 Curate/pack", "CURATED.md → AGENT_BRIEF.md → INDEX.json status=complete"],
  ["6 Validate", "research validate --slug <slug> must PASS"],
  ["7 Exit", "Research card Done + Notes with pack paths; handoff to consumer"],
];

const LIVE_PROOF = [
  ["Slug", "flexiai-toolsmith"],
  ["Source", "github:SavinRazvan/flexiai-toolsmith @ 3f8b0c7"],
  ["Rounds", "6/6 (justified; anti-loop exit)"],
  ["Curated", "18 verified rows"],
  ["Validate", "PASS"],
  ["Verifier", "Claim A+B VERIFIED (2026-07-19)"],
  ["Board", "Issue #74 Done · pack paths in Notes"],
];

const READ_FIRST = [
  [".cursor/skills/research-corpus/SKILL.md", "Intake + rounds canon"],
  ["_research_results/RESEARCH_BOUNDARIES.md", "Hard-stop boundaries"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".cursor/skills/canvas-artifacts/SKILL.md", "ADR-010 canvas/plan tiers"],
];

const PATTERNS = [
  ["Shipped agent", "Fully functional — live E2E + verifier PASS"],
  ["Opt-in corpus", "Packs appear only after research init (not incomplete)"],
  ["Hard stop", "Write only _research_results/"],
  ["Adaptive intake", "Chat / peer Notes / board card → Brief (+ defaults)"],
  ["Terse chat", "/researcher https://github.com/owner/repo OK"],
  ["Anti-loop", "≤6 deepen rounds; no re-fetch without --force; exit on complete"],
  ["GitHub auth", "Public: network; private: consumer gh/git credentials"],
  ["Board lifecycle", "create-from-template research → done + pack paths"],
  ["Consumers", "implementer / integrator / chat-user read AGENT_BRIEF.md"],
];

const ARTIFACTS = [
  ["_research_results/sources/<slug>/", "Pack + AGENT_BRIEF", "implementer / integrator"],
  ["Board Status + Notes", "Research card done + pack paths", "Next / requesting agent"],
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
  ["Use instead", "implementer", "Product code / commits"],
  ["Use instead", "verifier", "Claims vs evidence"],
  ["Use instead", "auditor", "Architecture audits"],
  ["Use instead", "drift-guard", "Drift / tracker coherence"],
  ["Use instead", "integrator", "Kit surface integration"],
  ["Use instead", "pr-workflow", "Git commit/push/PR (maintainer skills)"],
  ["Consumes from", "any agent", "Notes / handoff / cited pack path"],
  ["Proven with", "verifier", "Post-pack Claim A/B check (optional)"],
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

export default function AgentResearcherCanvas() {
  const { tokens } = useHostTheme();
  const [mode, setMode] = useCanvasState<SsotMode>("ssotMode", "board");

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} style={{ alignItems: "center" }}>
          <H1 style={{ margin: 0 }}>researcher</H1>
          <Pill tone="success" size="sm">
            shipped / proven
          </Pill>
          <Pill tone="info" size="sm">
            kit agent
          </Pill>
          <Pill tone="neutral" size="sm">
            independent-governed
          </Pill>
        </Row>
        <Text tone="secondary">
          researcher Agent Colony — Brief-driven multi-round research
          (GitHub/local) into _research_results packs; hard-stop on product code.
          Adaptive intake from chat or peer agents; corpus packs are opt-in after
          research init.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="proven" label="Live E2E + verifier" tone="success" />
        <Stat value="_research_results/" label="Only write target" />
        <Stat value="≤6 rounds" label="Anti-loop cap" tone="info" />
        <Stat value="EXIT_QUEUED" label="Outbox on rate-limit" tone="warning" />
      </Grid>

      <Callout tone="success" title="Status (2026-07-19)">
        Researcher is shipped and efficient. Live proof: flexiai-toolsmith pack
        (18 curated, validate PASS) + verifier Claim A (efficiency) and Claim B
        (correctness) VERIFIED. “Optional” means opt-in corpus — not an incomplete
        agent.
      </Callout>

      <Stack gap={8}>
        <H2>Goals</H2>
        {GOALS.map((g) => (
          <Text key={g}>• {g}</Text>
        ))}
      </Stack>

      <Divider />

      <Stack gap={10}>
        <H2 style={{ margin: 0 }}>How it works</H2>
        <Table headers={["Step", "Action"]} rows={HOW_IT_WORKS} />
        <Callout tone="info" title="CLI owns scaffold; agent owns evidence">
          python3 -m cursor_workflow research init|fetch|validate. Agent fills
          rounds 1–6 prose under sources/&lt;slug&gt;/ then exits on complete.
        </Callout>
      </Stack>

      <Card>
        <CardHeader>Live proof (flexiai-toolsmith)</CardHeader>
        <CardBody>
          <Table headers={["Field", "Evidence"]} rows={LIVE_PROOF} />
          <Spacer size={8} />
          <Text tone="tertiary" size="small">
            Pack: _research_results/sources/flexiai-toolsmith/AGENT_BRIEF.md ·
            Board Issue #74
          </Text>
        </CardBody>
      </Card>

      <Stack gap={10}>
        <Row gap={12} style={{ alignItems: "center" }}>
          <H2 style={{ margin: 0 }}>Workflow</H2>
          <Toggle
            checked={mode === "board"}
            onChange={(on) => setMode(on ? "board" : "fallback")}
            label={mode === "board" ? "board_only SSOT" : "local_trackers fallback"}
          />
        </Row>
        <Callout tone="info" title="Adaptive intake">
          Derive Brief from user chat (including /researcher https://github.com/…),
          peer agent Notes/handoffs, or board research card. Defaults fill missing
          question/lenses/slug. Refuse only when no source and not mode:self.
        </Callout>
        <Callout tone="warning" title="Hard stop">
          Write only _research_results/. No src/tests/scripts. No git commit/push/PR.
          Redirect to: implementer · integrator · verifier · auditor · drift-guard ·
          pr-workflow (maintainer skills) — see Peers.
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>
            1. Entry: project entry (+ research card); else session-pointer.
          </Text>
          <Text>
            2. Adaptive intake → normalize source (HTTPS | github: | path) → Brief.
          </Text>
          <Text>
            3. research init → fetch → rounds 1–6 → validate under
            _research_results/sources/&lt;slug&gt;/.
          </Text>
          <Text>
            4. If research card: set-status done + Notes with AGENT_BRIEF / INDEX
            paths; handoff to named consumer.
          </Text>
          <Text>5. Do not touch product code, tests, scripts, or git/PR workflows.</Text>
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
              Research packs are read-only input for humans and product agents —
              not shipped product code.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Create: create-from-template --template research --priority p2
              --size m --estimate 3 --agent researcher (or claim Ready card).
            </Text>
            <Text>Entry: project entry + research card when board on.</Text>
            <Text>
              Exit: pack under _research_results/sources/&lt;slug&gt;/; research card
              done + Notes with AGENT_BRIEF paths.
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

      <Callout tone="neutral" title="MCP + CLI">
        Prefer python3 -m cursor_workflow research init|fetch|validate. External
        research MCP only when listed for this agent in mcp.registry.yaml.
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. No invented peers or artifact paths.
      </Text>
    </Stack>
  );
}
