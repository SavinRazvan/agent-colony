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
  H3,
  Pill,
  Row,
  Spacer,
  Stack,
  Stat,
  Swatch,
  Table,
  Text,
  TodoListCard,
  Toggle,
  computeDAGLayout,
  useCanvasState,
  useHostTheme,
} from "cursor/canvas";

type Mode = "classic" | "shipped" | "compare";

const VERIFIED = "2026-07-19";

const CLASSIC_NODES = [
  { id: "agent" },
  { id: "session" },
  { id: "plan" },
  { id: "tracker" },
  { id: "code" },
  { id: "pr" },
];

const CLASSIC_EDGES = [
  { from: "agent", to: "session" },
  { from: "session", to: "plan" },
  { from: "plan", to: "tracker" },
  { from: "tracker", to: "code" },
  { from: "code", to: "pr" },
];

const SHIPPED_NODES = [
  { id: "yaml" },
  { id: "agent" },
  { id: "cli" },
  { id: "board" },
  { id: "code" },
  { id: "pr" },
  { id: "merge" },
  { id: "export" },
  { id: "snapshot" },
];

const SHIPPED_EDGES = [
  { from: "yaml", to: "agent" },
  { from: "agent", to: "cli" },
  { from: "cli", to: "board" },
  { from: "board", to: "code" },
  { from: "code", to: "pr" },
  { from: "pr", to: "merge" },
  { from: "merge", to: "board" },
  { from: "cli", to: "export" },
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
  cli: "cursor_workflow project",
  board: "GitHub Project",
  merge: "merge.py",
  export: "project export",
  snapshot: "board-snapshot.json",
};

const ABC_SLICES = [
  {
    id: "a",
    card: "BOARD-DOC-004",
    title: "A — Writable SSOT docs",
    color: "blue" as const,
    items: [
      "HANDOFF / ADR-008 / overlay / skills: only writable SSOT",
      "Continuation contract: Entry read board, Exit Status + Notes",
      "Local trackers = offline fallback; no dual-mirror",
      "DRIFT-009 dual-write guard",
    ],
  },
  {
    id: "b",
    card: "BOARD-MERGE-005",
    title: "B — Post-merge board sync",
    color: "green" as const,
    items: [
      "merge.py sets card Done + Notes (PR URL + SHA)",
      "Pattern A close — no new agent after merge",
      "CLI: get, append-notes, find-by-pr",
      "set-status on PVTI_; append-notes resolves DraftIssue DI_",
    ],
  },
  {
    id: "c",
    card: "BOARD-EXPORT-006",
    title: "C — Export + DRIFT-010",
    color: "purple" as const,
    items: [
      "project export → read-only snapshot",
      ".local/generated-data/project-board-snapshot.json",
      "Never writes Status — DRIFT-010 stale PR / board drift",
      "Deprecated HTML ICC Project Board tab (EA-010) — offline export only; prefer live board + Open Canvas",
    ],
  },
];

const FOLLOWUP_SLICES = [
  {
    id: "fix-notes",
    card: "FIX-NOTES-DI",
    title: "append-notes on DraftIssue",
    color: "green" as const,
    items: [
      "Resolves PVTI_ → DI_ + title for DraftIssue content",
      "Status stays on PVTI_; Issue-backed via gh issue edit",
      "Shipped on main (PR #3)",
    ],
  },
  {
    id: "tests",
    card: "Edge-case tests",
    title: "CLI + merge coverage",
    color: "blue" as const,
    items: [
      "Issue body, GraphQL errors, merge Notes warn",
      "set_item_status PVTI-only paths; outbox queue/flush",
      "1147 tests collected; COV-100 6503 stmts / 100%; drift validate green",
    ],
  },
  {
    id: "doc-drift",
    card: "Doc-drift residuals",
    title: "Skill board_only caveats",
    color: "blue" as const,
    items: [
      "audit-orchestration, workflow-activate",
      "mas-infrastructure-integration, test-module-coverage",
      "review-pr board_only caveats",
      "DRIFT validate P0=0 P1=0 P2=0 — shipped on main",
    ],
  },
];

const CLI_RECIPE_ROWS = [
  ["claim", "Pattern A — In progress + Start date (if empty) + Notes @user/agent · UTC"],
  ["handoff", "Pattern A — Status + Notes + next=@user/agent"],
  ["create-from-template", "Pattern A — slice/bug card + body sections"],
  ["mention-pr", "Pattern A — PR Notes; auto-promote when promote_to_issue_on_pr"],
  ["promote-to-issue", "Pattern A — Draft→Issue (same PVTI_; claim does not auto-promote)"],
  ["guide", "Copy-safe recipes for --agent <name>"],
  ["last", "Resolve --last item_id after create"],
  ["validate-item", "Card body / field sanity check"],
];

const CLI_ATOMIC_ROWS = [
  ["status", "Board health + project_ssot config"],
  ["list", "Filter by Status / assignee"],
  ["create", "New slice card (low-level)"],
  ["set-status", "In progress / In review / Done (PVTI_ only)"],
  ["set-field", "Priority, Size, Estimate, etc."],
  ["get", "Card body + fields"],
  ["append-notes", "Handoff lines; DraftIssue DI_ resolve + Issue edit"],
  ["set-assignee", "Human assignee (UI or PAT)"],
  ["find-by-pr", "Resolve card from PR number"],
  ["export", "Read-only snapshot → project-board-snapshot.json"],
  ["doctor", "Config / PAT / field-id diagnostics"],
  ["queue", "Enqueue deferred board write"],
  ["outbox", "status | flush — EXIT_QUEUED (6) buffer"],
];

const CLI_ROWS = [...CLI_RECIPE_ROWS, ...CLI_ATOMIC_ROWS];

function FlowDiagram({ mode }: { mode: "classic" | "shipped" }) {
  const theme = useHostTheme();
  const nodes = mode === "classic" ? CLASSIC_NODES : SHIPPED_NODES;
  const edges = mode === "classic" ? CLASSIC_EDGES : SHIPPED_EDGES;
  const layout = computeDAGLayout({
    nodes,
    edges,
    direction: "horizontal",
    nodeWidth: mode === "classic" ? 132 : 118,
    nodeHeight: 40,
    rankGap: 48,
    nodeGap: 20,
    padding: 12,
  });

  const accentIds =
    mode === "classic"
      ? new Set(["session", "plan", "tracker"])
      : new Set(["yaml", "cli", "board", "merge"]);

  const readOnlyIds = mode === "shipped" ? new Set(["export", "snapshot"]) : new Set();

  const nodeW = mode === "classic" ? 132 : 118;

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
          strokeDasharray={readOnlyIds.has(e.from) || readOnlyIds.has(e.to) ? "4 3" : undefined}
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
              fontFamily="system-ui, sans-serif"
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
    <Row gap={16} style={{ flexWrap: "wrap" }}>
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
          Writable SSOT (Status lives here)
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
          Read-only export path (never writes Status)
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

export default function BoardSsotVsKitCanvas() {
  const [mode, setMode] = useCanvasState<Mode>("view-mode", "compare");
  const [showLocal, setShowLocal] = useCanvasState<boolean>("show-local", true);

  return (
    <Stack gap={24} style={{ padding: 24, maxWidth: 960 }}>
      <Stack gap={8}>
        <H1>MAS Workflow Kit → Board SSOT (shipped)</H1>
        <Text tone="secondary">
          Before/after comparison for mas-workflow-kit-project-ssot as of {VERIFIED}.
          PR #2 merged A→B→C on main; FIX-NOTES-DI, doc-drift residuals, EA-001/004,
          and expanded tests (1147 collected) are shipped on main.
        </Text>
      </Stack>

      <Row gap={8} style={{ flexWrap: "wrap" }}>
        <Pill active={mode === "classic"} onClick={() => setMode("classic")}>
          Classic kit
        </Pill>
        <Pill active={mode === "shipped"} onClick={() => setMode("shipped")}>
          Shipped
        </Pill>
        <Pill active={mode === "compare"} onClick={() => setMode("compare")}>
          Side-by-side
        </Pill>
      </Row>

      <Grid columns={4} gap={12}>
        <Stat value="Markdown" label="Classic SSOT" />
        <Stat value="GitHub Project" label="Shipped SSOT" tone="success" />
        <Stat value="0 / 0 / 0" label="DRIFT P0 P1 P2" tone="success" />
        <Stat value="STANDALONE" label="Decided 2026-07-18" tone="success" />
      </Grid>

      <Callout tone="success" title="North star (shipped)">
        When board_only is on, agents read the GitHub Project on Entry and update
        Status + Notes on Exit. Local markdown trackers are offline fallback only —
        no dual-mirror. merge.py closes cards to Done after Pattern A merge.
        append-notes on DraftIssue items resolves PVTI_ → DI_ + title (FIX-NOTES-DI).
      </Callout>

      <H2>A → B → C rollout (PR #2 — merged)</H2>
      <TodoListCard
        defaultExpanded
        todos={ABC_SLICES.map((s) => ({
          id: s.id,
          content: `${s.title} · ${s.card}`,
          status: "completed" as const,
        }))}
      />
      <Grid columns={3} gap={12}>
        {ABC_SLICES.map((slice) => (
          <Card>
            <CardHeader
              trailing={
                <Row gap={6} align="center">
                  <Swatch color={slice.color} />
                  <Pill size="sm" active>
                    Done
                  </Pill>
                </Row>
              }
            >
              {slice.title}
            </CardHeader>
            <CardBody>
              <Stack gap={4}>
                {slice.items.map((item) => (
                  <Text size="small">{item}</Text>
                ))}
              </Stack>
            </CardBody>
          </Card>
        ))}
      </Grid>

      <H2>Post A→B→C follow-ups (shipped on main)</H2>
      <TodoListCard
        defaultExpanded
        todos={FOLLOWUP_SLICES.map((s) => ({
          id: s.id,
          content: `${s.title} · ${s.card}`,
          status: "completed" as const,
        }))}
      />
      <Grid columns={3} gap={12}>
        {FOLLOWUP_SLICES.map((slice) => (
          <Card>
            <CardHeader
              trailing={
                <Row gap={6} align="center">
                  <Swatch color={slice.color} />
                  <Pill size="sm" active>
                    Done
                  </Pill>
                </Row>
              }
            >
              {slice.title}
            </CardHeader>
            <CardBody>
              <Stack gap={4}>
                {slice.items.map((item) => (
                  <Text size="small">{item}</Text>
                ))}
              </Stack>
            </CardBody>
          </Card>
        ))}
      </Grid>

      {(mode === "classic" || mode === "compare") && (
        <Stack gap={10}>
          <H2>Classic MAS Workflow Kit</H2>
          <Text tone="secondary">
            Per-clone markdown under .local/index-and-planning/current/ was the
            writable SSOT: plan, work-tracker, session-pointer.
          </Text>
          <Legend />
          <FlowDiagram mode="classic" />
          <Card>
            <CardHeader>Agent loop (before)</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small">
                  1. session-pointer → plan → work-tracker
                </Text>
                <Text size="small">
                  2. One in_progress row in work-tracker.md
                </Text>
                <Text size="small">3. Implement → tests → update trackers</Text>
                <Text size="small">
                  4. PR Pattern A (prepare.py GATES) — merge is code-side only
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      )}

      {(mode === "shipped" || mode === "compare") && (
        <Stack gap={10}>
          <H2>Shipped — GitHub Project as only writable SSOT</H2>
          <Text tone="secondary">
            Same agents and Pattern A gates. Coordination bus is board Status /
            Notes. Solid edges = writable; dashed = read-only export for DRIFT-010.
          </Text>
          <Legend />
          <FlowDiagram mode="shipped" />
          <Card>
            <CardHeader>Agent loop + post-merge (after)</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small">
                  Entry: project status → list/claim → read card Notes
                </Text>
                <Text size="small">
                  Work: Acceptance on card body; implement + tests
                </Text>
                <Text size="small">
                  Exit: set-status (PVTI_) + append-notes (DraftIssue DI_ resolve)
                </Text>
                <Text size="small">
                  Post-merge: merge.py → Done + Notes (PR URL + SHA) — no new agent
                </Text>
                <Text size="small">
                  DRIFT-010: project export snapshot vs open PRs (read-only)
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      )}

      <Divider />

      <H2>project CLI — 22 leaf subcommands (shipped)</H2>
      <Callout tone="info" title="Module split (EA-001 shipped)">
        Dispatcher: project_cli.py · atomics: project_atomics.py · GraphQL adapter:
        gh_project_adapter.py · Pattern A recipes: project_recipes.py · rate-limit
        buffer: project_outbox.py → .local/generated-data/board-outbox.jsonl
        (EXIT_QUEUED=6).
      </Callout>
      <Table
        headers={["Command", "Role"]}
        rows={CLI_ROWS}
        striped
      />
      <Text tone="tertiary" size="small">
        Full list: status · list · create · create-from-template · set-status ·
        set-field · get · append-notes · claim · mention-pr · promote-to-issue ·
        handoff · validate-item · last · guide · doctor · set-assignee · find-by-pr ·
        export · queue · outbox
      </Text>

      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader trailing={<Pill size="sm" active>Guard</Pill>}>
            DRIFT-009
          </CardHeader>
          <CardBody>
            <Text size="small">
              Blocks dual-write: agents must not mirror slice status into
              work-tracker.md or session-pointer.md under board_only.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill size="sm" active>Guard</Pill>}>
            DRIFT-010
          </CardHeader>
          <CardBody>
            <Text size="small">
              Compares read-only export to open PRs / stale board state.
              Uses .local/generated-data/project-board-snapshot.json — never
              writes Status. DRIFT-006 fixed via real test-index paths.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <H2>Classic vs shipped</H2>
      <Table
        headers={["Concern", "Classic kit", "STANDALONE product"]}
        rows={[
          ["Backlog / status SSOT", "Local markdown trackers", "GitHub Project"],
          [
            "Agent Entry",
            "session-pointer → plan → tracker",
            "project status / list / claim",
          ],
          [
            "Agent Exit",
            "Update work-tracker in_progress",
            "set-status (PVTI_) + append-notes on board",
          ],
          [
            "DraftIssue Notes",
            "N/A",
            "append-notes resolves DI_; Issue-backed via gh issue edit",
          ],
          ["Human visibility", "Per-machine .local files", "Shared Project UI"],
          ["Post-merge card", "Manual / tracker only", "merge.py → Done + Notes"],
          ["Dual writers", "Single (markdown)", "Forbidden — DRIFT-009"],
          ["Stale PR detection", "N/A", "DRIFT-010 + export snapshot"],
          ["PR merge gates", "prepare.py Pattern A", "Unchanged (local_only)"],
          ["Offline / no gh", "N/A (always local)", "fallback: local_trackers"],
        ]}
        striped
      />

      <CollapsibleSection
        title="Recently fixed"
        leading={<Swatch color="green" />}
        defaultOpen={false}
      >
        <Callout tone="success" title="append-notes on draft issues (FIX-NOTES-DI)">
          Previously a known gap. append-notes now resolves PVTI_ → DI_ + title for
          DraftIssue content; Status stays on PVTI_; Issue-backed cards use gh issue
          edit. Shipped on main (PR #3).
        </Callout>
      </CollapsibleSection>

      <Row gap={10} align="center">
        <Toggle checked={showLocal} onChange={setShowLocal} />
        <Text size="small">Show what stays local</Text>
      </Row>

      {showLocal && (
        <Stack gap={8}>
          <H3>Stays local (by design)</H3>
          <Table
            headers={["Keep local", "Why"]}
            rows={[
              ["PR Pattern A (review / prepare / merge)", "Merge readiness is code-side"],
              ["Commit / PR attribution (owner, trailers)", "collab YAML — not board fields"],
              [".venv, secrets, .coverage", "Machine-local protected artifacts"],
              ["Audit / PR artifacts under .local/", "Evidence bundles stay in-repo"],
              ["Export snapshot under generated-data/", "Read-only cache — not SSOT"],
              ["Offline fallback trackers", "Only when project_ssot disabled or no gh"],
              ["Deprecated HTML ICC board panel", "EA-010 — offline export only; prefer live board + Open Canvas"],
            ]}
          />
        </Stack>
      )}

      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader trailing={<Pill size="sm" active>Done</Pill>}>
            Shipped on product (STANDALONE)
          </CardHeader>
          <CardBody>
            <Stack gap={4}>
              <Text size="small">project_ssot + board_only in collab YAML</Text>
              <Text size="small">
                cursor_workflow project CLI (22 leaf subcommands; outbox status +
                flush counted separately)
              </Text>
              <Text size="small">8 agent Anchors + continuation contract</Text>
              <Text size="small">ADR-008 + project-ssot-precedence overlay</Text>
              <Text size="small">A→B→C merged (PR #2); FIX-NOTES-DI on main (PR #3)</Text>
              <Text size="small">
                1147 tests collected; COV-100 6503 stmts / 100%; DRIFT validate
                P0=0 P1=0 P2=0
              </Text>
              <Text size="small">STANDALONE decided — this repo is the product</Text>
              <Text size="small">
                BOARD-PROMOTE: Draft→Issue via promote-to-issue / mention-pr auto
                (promote_to_issue_on_pr default true); claim does not auto-promote
              </Text>
              <Text size="small">BOARD-TIER1: Start date on In progress; Size/Estimate table; mention-pr</Text>
              <Text size="small">EA-001: project_cli split (atomics/adapter/recipes/outbox)</Text>
              <Text size="small">EA-004: pyright blocking in kit-quality CI</Text>
              <Text size="small">EA-010: deprecated HTML ICC tab (offline export; prefer board + Open Canvas)</Text>
            </Stack>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill size="sm">Open</Pill>}>
            Still human-gated / future
          </CardHeader>
          <CardBody>
            <Stack gap={4}>
              <Text size="small">Install screenshot asset TBD if UI text differs</Text>
              <Text size="small">Consumer marketplace publish channel TBD</Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Spacer />
      <Callout tone="neutral" title="How to read this (STANDALONE product)">
        Classic kit solved disciplined agents + PR gates on local markdown.
        This repository is the permanent product: coordination on one GitHub Project,
        evidence in local artifacts. Upstream mas-workflow-kit is lineage only —
        no port back. Board Entry/Exit continues every agent slice.
      </Callout>

      <Text size="small" tone="tertiary">
        Source: HANDOFF §1 · ADR-008 · STANDALONE 2026-07-18 · PR #2/#3 merged ·
        drift validate green · verified {VERIFIED} · 1147 tests · COV-100 6503 stmts
      </Text>
    </Stack>
  );
}
