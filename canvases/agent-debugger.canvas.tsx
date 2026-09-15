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
type DetailTab = "skills" | "layout" | "cli" | "modes";

const VERIFIED = "2026-09-15";
const SOURCES =
  ".cursor/agents/debugger.md · debug-protocol · debug-vault · debug-handoff · board-ssot · logging-and-errors.md";

const GOALS = [
  "Campaign-scoped forensic investigation: map modules/files, raise logs/errors toward a standard",
  "Bounded experiments: hypothesis → capture|ingest → Signals → verdict (confirmed|ruled_out|probable|unknown)",
  "Vault = redacted personal evidence; publish = curated packs peers consume",
  "Queue DBG / TR / SG findings; child bug|slice cards — no durable product fixes on the DEBUG card",
  "debug close + publish manifest hash in Notes; shippable → verifier before Done",
];

const BOARD_NODES = [
  { id: "status" },
  { id: "create" },
  { id: "claim" },
  { id: "init" },
  { id: "evidence" },
  { id: "experiment" },
  { id: "findings" },
  { id: "validate" },
  { id: "close" },
  { id: "handoff" },
];

const BOARD_EDGES = [
  { from: "status", to: "create" },
  { from: "create", to: "claim" },
  { from: "claim", to: "init" },
  { from: "init", to: "evidence" },
  { from: "evidence", to: "experiment" },
  { from: "experiment", to: "findings" },
  { from: "findings", to: "validate" },
  { from: "validate", to: "close" },
  { from: "close", to: "handoff" },
];

const FALLBACK_NODES = [
  { id: "session" },
  { id: "init" },
  { id: "evidence" },
  { id: "experiment" },
  { id: "close" },
];

const FALLBACK_EDGES = [
  { from: "session", to: "init" },
  { from: "init", to: "evidence" },
  { from: "evidence", to: "experiment" },
  { from: "experiment", to: "close" },
];

const BOARD_LABELS: Record<string, string> = {
  status: "api-ready → entry",
  create: "template debug",
  claim: "claim debugger",
  init: "debug init",
  evidence: "inventory · map",
  experiment: "capture · analyze",
  findings: "DBG · TR · SG",
  validate: "validate · handoff",
  close: "debug close",
  handoff: "verifier | peers",
};

const FALLBACK_LABELS: Record<string, string> = {
  session: "session-pointer",
  init: "debug init",
  evidence: "inventory · map",
  experiment: "capture · analyze",
  close: "validate · close",
};

const SKILLS = [
  ["debug-protocol", "Orchestrator", "Modes, caps, experiment loop, lazy skill order, Board Exit"],
  ["debug-vault", "Evidence", "Vault layout, redaction, budgets, session-log, retention"],
  ["debug-scripts", "CLI", "agent_colony debug …; campaign vault/scripts/; promote via integrator"],
  ["debug-module-map", "Map", "Campaign inventory, importance, entrypoints, waves"],
  ["debug-file-ledger", "Map", "Per-file disposition, logs/errors, probes, next action"],
  ["debug-observability-standard", "Standards", "Enforce logging-and-errors.md; SG rows"],
  ["debug-error-surface", "Standards", "Catch/rethrow/swallow/retry boundaries → DBG if behavior"],
  ["debug-instrumentation", "Probes", "DEBUG-PROBE markers, index, rollback, cleanup before close"],
  ["debug-run-ledger", "Runs", "capture/ingest/analyze, Signals, anti-loop budgets"],
  ["debug-lenses", "Lenses", "repro, error, data, concurrency, resource, perf, integration, …"],
  ["debug-handoff", "Exit", "HANDOFF.json/md, child cards, Notes payload, verifier checks"],
];

const MODES = [
  ["incident", "vault + run ledger + selected lenses + instrumentation as needed + handoff"],
  ["standardize", "module map + file ledger + observability/error + tests + handoff"],
  ["structural", "module map + perf/resource lenses → escalate auditor (not Schema-1 pack)"],
  ["deep", "all required lenses; still bounded by wave + run budgets"],
];

const CLI_CMDS = [
  ["debug init", "Create campaign tree; reject existing slug"],
  ["debug inventory", "Enumerate files; seed module/file ledgers"],
  ["debug capture -- <argv>", "Secure argv capture (subprocess shell=False)"],
  ["debug ingest", "Import existing log without executing"],
  ["debug analyze", "Draft Signals + run summary; agent sets verdict"],
  ["debug finding add|update|render", "DBG / TR / SG machine records + Markdown views"],
  ["debug probe register|resolve|scan", "Probe index + DEBUG-PROBE reconcile"],
  ["debug handoff", "ready_for_consumer + HANDOFF + child-card payloads"],
  ["debug status --digest", "Budgets, latest run, findings, next_action"],
  ["debug validate | block | repair | close", "State-aware gates; close = immutable"],
];

const LAYOUT = [
  ["INDEX.json", "Campaign SSOT: status, mode, budgets, counters, next_agent"],
  ["DEBUG-BRIEF.md", "Scope, lenses, caps, human approval state"],
  ["vault/", "Redacted evidence (protected); session-log; logs/by-run; probes"],
  ["vault/logs/by-run/run-NNNNNN/", "meta + stdout/stderr + extracted/"],
  ["publish/", "Peers read here: HANDOFF, findings, runs, project-map"],
  ["publish/findings/", "bugs-for-implementer · cases-for-test-runner · standards-gaps"],
  ["publish/manifest.json", "Hashes + paths; Notes cite manifest hash"],
];

const FINDINGS = [
  ["DBG-*", "implementer", "Behavior/fix boundary; child --template bug"],
  ["TR-*", "test-runner", "Regression/edge cases; captures are leads not suite proof"],
  ["SG-*", "standards / integrator", "logging-and-errors gaps; mechanical vs doctrine"],
];

const STATES = [
  ["init", "Schemas, brief, empty counters"],
  ["in_progress", "Runs + events; placeholders OK"],
  ["blocked", "Human decision; evidence + next action required"],
  ["ready_for_consumer", "HANDOFF + findings rendered; child payloads"],
  ["closed", "Immutable; no open probes; secret scan PASS"],
];

const HARD_STOPS = [
  "Production/staging probes or mutable external systems",
  "Destructive commands or unknown side effects",
  "Load/stress/soak outside an isolated environment",
  "Auth, payment, secrets, PII, regulated data",
  "Probes that alter business behavior",
  "Budget/scope expansion beyond Brief",
  "Evidence redaction cannot make safe",
  "Overwrite/repair/unlock/archive/purge protected vault without explicit approval",
];

const READ_FIRST = [
  [".cursor/skills/debug-protocol/SKILL.md", "Orchestration hub — load first"],
  [".cursor/skills/debug-vault/SKILL.md", "Vault discipline + redaction"],
  [".cursor/skills/debug-handoff/SKILL.md", "Exit · child cards · verifier"],
  [".cursor/skills/board-ssot/SKILL.md", "When project_ssot.enabled"],
  [".cursor/skills/evidence-first/SKILL.md", "Facts → evidence → action"],
  [".ai_infra/docs/operations/logging-and-errors.md", "Observability SSOT"],
  [".local/workflow-artifacts/debug/DEBUG_BOUNDARIES.md", "After scaffold / init"],
];

const PATTERNS = [
  ["Board template", "create-from-template --template debug (not bug)"],
  ["Capture shell=False", "Python argv only — does NOT disable Cursor Shell tool"],
  ["Vault vs publish", "Notes cite publish/ + manifest hash; never dump vault"],
  ["Child cards", "Consumers claim bug|slice — never take over DEBUG card"],
  ["Lazy skills", "debug-protocol dispatches sections; do not preload all 11"],
  ["Not on lite", "consumer_lite forbids debugger + debug-* skills"],
  ["Attribution", "@owner.github_user/debugger via --agent debugger"],
];

const ARTIFACTS = [
  [
    ".local/workflow-artifacts/debug/<slug>/INDEX.json",
    "After init",
    "Campaign machine SSOT",
  ],
  [
    ".local/workflow-artifacts/debug/<slug>/vault/",
    "Experiments",
    "Protected redacted evidence",
  ],
  [
    ".local/workflow-artifacts/debug/<slug>/publish/",
    "Handoff / Exit",
    "implementer · test-runner · verifier",
  ],
  [
    ".local/workflow-artifacts/debug/<slug>/publish/HANDOFF.json",
    "debug handoff",
    "Peers + Board Notes payload",
  ],
  ["Board Status + Notes", "Exit (manifest hash + validate PASS)", "verifier / board"],
  [".local/generated-data/board-outbox.jsonl", "EXIT_QUEUED (6)", "api-ready → flush"],
];

const PEERS = [
  ["Inbound", "board", "create-from-template --template debug + claim"],
  ["Outbound", "implementer", "Child bug|slice from DBG rows + publish citations"],
  ["Outbound", "test-runner", "TR rows — fresh pytest for durable proof"],
  ["Outbound", "verifier", "Shippable: handoff --next verifier before Done"],
  ["Outbound", "auditor", "Structural findings only — not Schema-1 packs"],
  ["Outbound", "drift-guard", "SG → DRIFT only if doctrine/docs actually drift"],
  ["Outbound", "integrator", "Promote reusable vault/scripts into kit"],
  ["Outbound", "researcher", "May cite research brief — corpus stays separate"],
  ["Escalation", "human", "debug block on hard stops"],
];

const SIGNALS = [
  ["exit_code", "Child process exit (wrapper may differ with --propagate-exit)"],
  ["errors", "Tracebacks / extracted errors"],
  ["logs", "Relevant lines or none — gap Confirmed"],
  ["probe_hits", "DEBUG-PROBE markers observed"],
  ["verdict", "confirmed | ruled_out | probable | unknown"],
  ["vault_ref", "vault/logs/by-run/run-NNNNNN/"],
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
  const nodeW = 108;
  const nodeH = 36;
  const layout = computeDAGLayout({
    nodes,
    edges,
    direction: "horizontal",
    nodeWidth: nodeW,
    nodeHeight: nodeH,
    rankGap: 28,
    nodeGap: 14,
  });

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      style={{ maxWidth: 980 }}
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
            fontSize={9}
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
  const [tab, setTab] = useCanvasState<DetailTab>("detailTab", "skills");

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
          <Pill tone="success" size="sm">
            v3 shipped
          </Pill>
        </Row>
        <Text tone="secondary">
          Master forensic investigation — redacted vault evidence, hypothesis
          experiments, curated publish handoffs for implementer / test-runner /
          verifier.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED} · facts only
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="11" label="debug-* skills" />
        <Stat value="5" label="Campaign states" />
        <Stat value="verifier" label="Shippable Done gate" tone="warning" />
        <Stat value="EXIT_QUEUED" label="Outbox on rate-limit" tone="warning" />
      </Grid>

      <Callout tone="danger" title="Boundary — not implementer, auditor, or test-runner">
        No durable product fixes, merge gates, Schema-1 audit packs, or owning the
        durable pytest suite on the DEBUG card. Route DBG → implementer child
        cards; TR → test-runner; structural → auditor input only. Shippable (PR /
        [AUDIT] / P0|P1) → handoff --next verifier --to in_review before Done.
      </Callout>

      <Callout tone="info" title="shell=False ≠ Cursor Shell off">
        Secure capture uses Python subprocess argv (shell=False). That is campaign
        capture only. Cursor Agent Shell/Task are separate and unchanged.
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
            ? "Entry: project api-ready → entry → create-from-template --template debug → claim --agent debugger. Evidence under .local/workflow-artifacts/debug/<slug>/."
            : "Entry: session-pointer.md; resume board sync when available."}
        </Callout>
        <DagPanel mode={mode} tokens={tokens} />
      </Stack>

      <CollapsibleSection title="Loop steps (canon)" defaultOpen>
        <Stack gap={6}>
          <Text>
            1. Claim DEBUG card; `debug init --slug … --item-id … --mode …`.
          </Text>
          <Text>
            2. `debug inventory` → module map + file ledger; lazy-load skills by
            phase.
          </Text>
          <Text>
            3. Experiment: hypothesis → optional probe → `debug capture` or
            `ingest` → `analyze` → Signals + verdict.
          </Text>
          <Text>
            4. Curate DBG/TR/SG → `debug handoff` → child bug|slice cards
            (publish citations).
          </Text>
          <Text>
            5. Probe cleanup → `debug validate` → `debug close` → Notes cite
            publish/ manifest hash + PASS.
          </Text>
          <Text>
            6. Shippable: `project handoff --last --agent debugger --next verifier
            --to in_review`.
          </Text>
        </Stack>
      </CollapsibleSection>

      <Stack gap={10}>
        <H2 style={{ margin: 0 }}>Detail</H2>
        <Row gap={8} style={{ flexWrap: "wrap" }}>
          {(
            [
              ["skills", "11 skills"],
              ["layout", "Vault / publish"],
              ["cli", "CLI commands"],
              ["modes", "Modes · findings · stops"],
            ] as const
          ).map(([id, label]) => (
            <Pill
              key={id}
              tone={tab === id ? "info" : "neutral"}
              size="sm"
              active={tab === id}
              onClick={() => setTab(id)}
            >
              {label}
            </Pill>
          ))}
        </Row>

        {tab === "skills" ? (
          <Card>
            <CardHeader trailing={<Text size="small">Load debug-protocol first</Text>}>
              Specialized skills
            </CardHeader>
            <CardBody>
              <Table headers={["Skill", "Layer", "Owns"]} rows={SKILLS} />
            </CardBody>
          </Card>
        ) : null}

        {tab === "layout" ? (
          <Card>
            <CardHeader>Campaign tree</CardHeader>
            <CardBody>
              <Table headers={["Path", "Role"]} rows={LAYOUT} />
              <Spacer size={8} />
              <Text tone="tertiary" size="small">
                Root: .local/workflow-artifacts/debug/&lt;slug&gt;/ — vault/**
                protected (local-artifact-protection). Closed campaigns are
                immutable; follow-ups use a new slug + supersedes.
              </Text>
            </CardBody>
          </Card>
        ) : null}

        {tab === "cli" ? (
          <Stack gap={12}>
            <Card>
              <CardHeader>python3 -m agent_colony debug …</CardHeader>
              <CardBody>
                <Table headers={["Command", "Purpose"]} rows={CLI_CMDS} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>Publish run — Signals block</CardHeader>
              <CardBody>
                <Table headers={["Field", "Meaning"]} rows={SIGNALS} />
              </CardBody>
            </Card>
          </Stack>
        ) : null}

        {tab === "modes" ? (
          <Stack gap={12}>
            <Card>
              <CardHeader>Modes (debug-protocol call order)</CardHeader>
              <CardBody>
                <Table headers={["Mode", "Skill emphasis"]} rows={MODES} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>Finding kinds</CardHeader>
              <CardBody>
                <Table headers={["Id", "Owner", "Route"]} rows={FINDINGS} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>Campaign states</CardHeader>
              <CardBody>
                <Table headers={["Status", "Rule"]} rows={STATES} />
              </CardBody>
            </Card>
            <Card>
              <CardHeader>Human hard stops → debug block</CardHeader>
              <CardBody>
                <Stack gap={4}>
                  {HARD_STOPS.map((s) => (
                    <Text key={s}>• {s}</Text>
                  ))}
                </Stack>
              </CardBody>
            </Card>
          </Stack>
        ) : null}
      </Stack>

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
              No new MCP tools — board/session via agent-colony-mcp; campaign
              actions via debug CLI only.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Board interaction</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Create: create-from-template --template debug --priority p2 (unless
              shippable severity) --agent debugger.
            </Text>
            <Text>
              Exit: Notes cite campaign id, outcome, publish path, manifest hash,
              validate PASS; child cards for every actionable DBG/TR/SG.
            </Text>
            <Text>
              Rate-limit: api-ready → EXIT_QUEUED (6) → cooldown/outbox → flush;
              do not hammer GraphQL.
            </Text>
            <Text>
              validate-item: debug packs use validate_for_board — not Audit
              Schema-1.
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Stack gap={8}>
        <H2>Peers</H2>
        <Table headers={["Direction", "Agent", "Evidence"]} rows={PEERS} />
      </Stack>

      <Callout tone="neutral" title="MCP">
        Kit server agent-colony-mcp for Pattern A board/session. Campaign actions
        use `agent_colony debug`. External servers only if listed for debugger in
        mcp.registry.yaml (DeepWiki is not granted by default).
      </Callout>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. Product canvas SSOT under
        canvases/agent-debugger.canvas.tsx · sync via canvas-artifacts.
      </Text>
    </Stack>
  );
}
