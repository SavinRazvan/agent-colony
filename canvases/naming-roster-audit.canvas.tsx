/**
 * File: naming-roster-audit.canvas.tsx
 * Path: canvases/naming-roster-audit.canvas.tsx
 * Role: Naming roster audit — plan table, scores, target stack, future-agent admission gate.
 * Used By:
 *  - human rename appetite decisions
 *  - .local/workflow-artifacts/alignment/naming-rename-plan.md
 * Depends On:
 *  - .cursor/agents (agent cards)
 *  - .cursor/skills (canonical SKILL.md folders)
 *  - .agents/skills (maintainer SKILL.md folders)
 * Notes:
 *  - Concept hub (not agent-*). Excluded from DOC-008 roster scan like board-ssot-vs-trackers.
 *  - B-safe rename SHIPPED 2026-08-03 (#140, #146–#149); Plan/Scores/Stack = live roster.
 *  - Renames tab = historical old→live ledger only (not current Task subagent_type).
 *  - Roster scorecard 2026-08-04 (AA-ROSTER-001…008) mirrored on Stack/Future views.
 *  - Intentional non-renames: artifact dir enterprise-architecture-audit/, ops doc
 *    project-board-collaboration.md, snapshot project-board-snapshot.json.
 *  - CLI/MCP stack (renames v0.6.0/v0.6.1; current kit 0.6.4): agent_colony / agent-colony console;
 *    agent_colony_mcp package; Cursor server id agent-colony-mcp unchanged.
 *  - Avoid "star-slash" globs in this block comment — they terminate the comment early.
 */

import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Select,
  Stack,
  Stat,
  Table,
  Text,
  useCanvasState,
} from "cursor/canvas";

const AUDIT_DATE = "2026-08-04";

type View = "plan" | "scores" | "stack" | "renames" | "future";

/** Four-column rename plan — primary skill only; shared board skill is separate. */
const PLAN_ROWS: {
  lane: string;
  agentNow: string;
  skillsNow: string;
  agentNext: string;
  skillsNext: string;
  agentChange: "keep" | "rename";
  skillChange: "keep" | "rename" | "none" | "optional-new";
}[] = [
  {
    lane: "Coordination",
    agentNow: "board",
    skillsNow: "PRIMARY board-ssot · ALSO board-shell",
    agentNext: "board",
    skillsNext: "PRIMARY board-ssot · ALSO board-shell",
    agentChange: "keep",
    skillChange: "keep",
  },
  {
    lane: "Delivery",
    agentNow: "implementer",
    skillsNow: "PRIMARY implementer-loop",
    agentNext: "implementer",
    skillsNext: "PRIMARY implementer-loop",
    agentChange: "keep",
    skillChange: "keep",
  },
  {
    lane: "Delivery",
    agentNow: "test-runner",
    skillsNow: "PRIMARY test-coverage",
    agentNext: "test-runner",
    skillsNext: "PRIMARY test-coverage",
    agentChange: "keep",
    skillChange: "keep",
  },
  {
    lane: "Delivery",
    agentNow: "verifier",
    skillsNow: "(no primary skill folder — agent card only)",
    agentNext: "verifier",
    skillsNext: "(keep inline) · optional later: verify-claims",
    agentChange: "keep",
    skillChange: "none",
  },
  {
    lane: "Infrastructure",
    agentNow: "integrator",
    skillsNow: "PRIMARY integrator-protocol",
    agentNext: "integrator",
    skillsNext: "PRIMARY integrator-protocol",
    agentChange: "keep",
    skillChange: "keep",
  },
  {
    lane: "Quality",
    agentNow: "auditor",
    skillsNow:
      "PRIMARY auditor-protocol · ALSO audit-orchestration, audit-module-map",
    agentNext: "auditor",
    skillsNext:
      "PRIMARY auditor-protocol · ALSO audit-orchestration, audit-module-map (keep)",
    agentChange: "keep",
    skillChange: "keep",
  },
  {
    lane: "Quality",
    agentNow: "drift-guard",
    skillsNow: "PRIMARY drift-audit",
    agentNext: "drift-guard",
    skillsNext: "PRIMARY drift-audit",
    agentChange: "keep",
    skillChange: "keep",
  },
  {
    lane: "Research",
    agentNow: "researcher",
    skillsNow: "PRIMARY research-corpus",
    agentNext: "researcher",
    skillsNext: "PRIMARY research-corpus",
    agentChange: "keep",
    skillChange: "keep",
  },
];

const SHARED_SKILLS = [
  [
    "board-ssot",
    "Shared by ALL agents for board Entry/Exit — not one agent's exclusive skill",
  ],
  [
    "workflow-activate",
    "Skill-only — consumer install; no agent twin",
  ],
  [
    "mcp-connect",
    "Skill-only — MCP wiring",
  ],
  [
    "review-pr / prepare-pr / merge-pr / pr-workflow",
    "Maintainer slash namespace (.agents/skills) — not Task agents",
  ],
  [
    "audit-alignment (stub)",
    "DEPRECATED stub → points at auditor + auditor-protocol",
  ],
];
type PillTone = "neutral" | "added" | "deleted" | "renamed" | "success" | "warning" | "info";
type Layer = "all" | "agents" | "skills" | "rules" | "canvases";

/** Five dimensions × 0–5 → total /25 */
type ScoreDims = {
  clarity: number;
  brevity: number;
  pairing: number;
  convention: number;
  uniqueness: number;
};

type ScoredName = {
  id: string;
  kind: "agent" | "skill-canonical" | "skill-maintainer";
  primaryPair?: string;
  dims: ScoreDims;
  note: string;
};

const RUBRIC: { dim: string; weight: string; how: string }[] = [
  {
    dim: "Clarity",
    weight: "0–5",
    how: "Can a new teammate infer the role from the id alone?",
  },
  {
    dim: "Brevity",
    weight: "0–5",
    how: "Fit for Notes @user/<id>, Task type, slash discoverability (≤3 tokens ideal)",
  },
  {
    dim: "Pairing",
    weight: "0–5",
    how: "Agent↔primary skill share a stem; shared skills scored vs CLI/doctrine fit",
  },
  {
    dim: "Convention",
    weight: "0–5",
    how: "kebab role noun; no -agent/-bot; skills <role>-<protocol> or clear domain",
  },
  {
    dim: "Uniqueness",
    weight: "0–5",
    how: "Collision risk vs roster, slash skills, and future lanes",
  },
];

const BANDS: { range: string; label: string; tone: PillTone; action: string }[] = [
  {
    range: "22–25",
    label: "Excellent",
    tone: "success",
    action: "Keep; document only",
  },
  {
    range: "18–21",
    label: "Good",
    tone: "info",
    action: "Keep or minor skill polish",
  },
  {
    range: "14–17",
    label: "Weak",
    tone: "warning",
    action: "Rename candidate (P1/P2)",
  },
  {
    range: "0–13",
    label: "Poor",
    tone: "deleted",
    action: "Rename priority (P0/P1)",
  },
];

function total(d: ScoreDims): number {
  return d.clarity + d.brevity + d.pairing + d.convention + d.uniqueness;
}

function band(score: number): (typeof BANDS)[number] {
  if (score >= 22) return BANDS[0];
  if (score >= 18) return BANDS[1];
  if (score >= 14) return BANDS[2];
  return BANDS[3];
}

function bandTone(score: number): "success" | "warning" | "danger" | "info" | "neutral" {
  if (score >= 22) return "success";
  if (score >= 18) return "info";
  if (score >= 14) return "warning";
  return "danger";
}

const AGENT_SCORES: ScoredName[] = [
  {
    id: "implementer",
    kind: "agent",
    primaryPair: "implementer-loop",
    dims: { clarity: 5, brevity: 4, pairing: 3, convention: 5, uniqueness: 5 },
    note: "Role crystal clear; skill name too long / not stemmed",
  },
  {
    id: "verifier",
    kind: "agent",
    primaryPair: "(none — card only)",
    dims: { clarity: 5, brevity: 5, pairing: 2, convention: 5, uniqueness: 5 },
    note: "Excellent id; missing dedicated skill folder",
  },
  {
    id: "researcher",
    kind: "agent",
    primaryPair: "research-corpus",
    dims: { clarity: 5, brevity: 4, pairing: 3, convention: 5, uniqueness: 5 },
    note: "Strong; skill has execution noise",
  },
  {
    id: "test-runner",
    kind: "agent",
    primaryPair: "test-coverage",
    dims: { clarity: 4, brevity: 4, pairing: 3, convention: 5, uniqueness: 5 },
    note: "Good agent; skill wording diverges (runner vs coverage)",
  },
  {
    id: "board",
    kind: "agent",
    primaryPair: "board-ssot",
    dims: { clarity: 4, brevity: 3, pairing: 4, convention: 5, uniqueness: 4 },
    note: "Clear; longer Notes stamp; -ssot only on skill",
  },
  {
    id: "auditor",
    kind: "agent",
    primaryPair: "auditor-protocol",
    dims: { clarity: 4, brevity: 2, pairing: 3, convention: 4, uniqueness: 4 },
    note: "Live id auditor; residual: auditor vs architecture-audit artifact path",
  },
  {
    id: "drift-guard",
    kind: "agent",
    primaryPair: "drift-audit",
    dims: { clarity: 3, brevity: 2, pairing: 3, convention: 4, uniqueness: 4 },
    note: "Live id drift-guard; residual: guard vs audit metaphor (score <18)",
  },
  {
    id: "integrator",
    kind: "agent",
    primaryPair: "integrator-protocol",
    dims: { clarity: 5, brevity: 4, pairing: 3, convention: 4, uniqueness: 4 },
    note: "Live id integrator; residual pairing debt with integrator-protocol",
  },
];

const SKILL_SCORES: ScoredName[] = [
  {
    id: "workflow-activate",
    kind: "skill-canonical",
    dims: { clarity: 5, brevity: 4, pairing: 5, convention: 5, uniqueness: 5 },
    note: "Matches CLI activate; consumer-facing",
  },
  {
    id: "review-pr",
    kind: "skill-maintainer",
    dims: { clarity: 5, brevity: 5, pairing: 5, convention: 5, uniqueness: 5 },
    note: "Maintainer verb-object namespace (intentional)",
  },
  {
    id: "prepare-pr",
    kind: "skill-maintainer",
    dims: { clarity: 5, brevity: 5, pairing: 5, convention: 5, uniqueness: 5 },
    note: "Same family as review-pr / merge-pr",
  },
  {
    id: "merge-pr",
    kind: "skill-maintainer",
    dims: { clarity: 5, brevity: 5, pairing: 5, convention: 5, uniqueness: 5 },
    note: "Same family",
  },
  {
    id: "pr-workflow",
    kind: "skill-maintainer",
    dims: { clarity: 5, brevity: 4, pairing: 5, convention: 5, uniqueness: 5 },
    note: "Orchestrates PR slash path",
  },
  {
    id: "audit-orchestration",
    kind: "skill-canonical",
    dims: { clarity: 4, brevity: 3, pairing: 5, convention: 4, uniqueness: 4 },
    note: "Shared parent skill — no agent twin required",
  },
  {
    id: "audit-module-map",
    kind: "skill-canonical",
    dims: { clarity: 4, brevity: 3, pairing: 5, convention: 4, uniqueness: 4 },
    note: "audit-* family coherent",
  },
  {
    id: "board-ssot",
    kind: "skill-canonical",
    primaryPair: "board",
    dims: { clarity: 4, brevity: 3, pairing: 4, convention: 4, uniqueness: 4 },
    note: "-ssot doctrine keyword is valuable",
  },
  {
    id: "board-shell",
    kind: "skill-canonical",
    primaryPair: "board",
    dims: { clarity: 4, brevity: 3, pairing: 4, convention: 4, uniqueness: 4 },
    note: "Shipped board-shell; residual -shell vs onboard mnemonic",
  },
  {
    id: "test-coverage",
    kind: "skill-canonical",
    primaryPair: "test-runner",
    dims: { clarity: 4, brevity: 3, pairing: 3, convention: 4, uniqueness: 4 },
    note: "Shipped test-coverage; runner↔coverage stem gap remains",
  },
  {
    id: "mcp-connect",
    kind: "skill-canonical",
    dims: { clarity: 4, brevity: 2, pairing: 4, convention: 3, uniqueness: 4 },
    note: "Shipped mcp-connect; brevity still weak",
  },
  {
    id: "research-corpus",
    kind: "skill-canonical",
    primaryPair: "researcher",
    dims: { clarity: 4, brevity: 2, pairing: 3, convention: 3, uniqueness: 4 },
    note: "Shipped research-corpus; former -execution suffix retired",
  },
  {
    id: "auditor-protocol",
    kind: "skill-canonical",
    primaryPair: "auditor",
    dims: { clarity: 4, brevity: 2, pairing: 3, convention: 3, uniqueness: 3 },
    note: "Shipped auditor-protocol; long stem vs short agent id",
  },
  {
    id: "drift-audit",
    kind: "skill-canonical",
    primaryPair: "drift-guard",
    dims: { clarity: 3, brevity: 2, pairing: 3, convention: 3, uniqueness: 3 },
    note: "Shipped drift-audit; guard vs audit metaphor remains",
  },
  {
    id: "implementer-loop",
    kind: "skill-canonical",
    primaryPair: "implementer",
    dims: { clarity: 3, brevity: 2, pairing: 2, convention: 3, uniqueness: 3 },
    note: "Shipped implementer-loop; loop suffix still long",
  },
  {
    id: "integrator-protocol",
    kind: "skill-canonical",
    primaryPair: "integrator",
    dims: { clarity: 3, brevity: 1, pairing: 2, convention: 2, uniqueness: 3 },
    note: "Worst pairing on roster (short agent / long skill)",
  },
  {
    id: "audit-alignment",
    kind: "skill-maintainer",
    primaryPair: "auditor",
    dims: { clarity: 2, brevity: 4, pairing: 1, convention: 2, uniqueness: 2 },
    note: "DEPRECATED stub — retire",
  },
];

type PairScore = {
  agent: string;
  skill: string;
  agentTotal: number;
  skillTotal: number;
  pairAvg: number;
  grade: string;
};

const PAIR_SCORES: PairScore[] = AGENT_SCORES.map((a) => {
  const skillId = a.primaryPair?.startsWith("(") ? undefined : a.primaryPair;
  const skill = skillId
    ? SKILL_SCORES.find((s) => s.id === skillId)
    : undefined;
  const agentTotal = total(a.dims);
  const skillTotal = skill ? total(skill.dims) : 10;
  const pairAvg = Math.round(((agentTotal + skillTotal) / 2) * 10) / 10;
  return {
    agent: a.id,
    skill: skillId ?? "(no skill folder)",
    agentTotal,
    skillTotal,
    pairAvg,
    grade: band(Math.round(pairAvg)).label,
  };
}).sort((x, y) => y.pairAvg - x.pairAvg);

const FUTURE_GATES: {
  id: string;
  check: string;
  failIf: string;
  maxDeduct: number;
}[] = [
  {
    id: "FG-1",
    check: "Role noun kebab-case (no -agent/-bot/-assistant)",
    failIf: "Type suffix or title-case folder",
    maxDeduct: 5,
  },
  {
    id: "FG-2",
    check: "≤3 kebab tokens; Notes-friendly (@user/<id>)",
    failIf: "4+ tokens or product acronym clutter (mas-, enterprise-)",
    maxDeduct: 5,
  },
  {
    id: "FG-3",
    check: "Primary skill folder shares stem (<id>-loop|protocol|…)",
    failIf: "Unrelated compound skill name",
    maxDeduct: 5,
  },
  {
    id: "FG-4",
    check: "Lane declared (Coordination|Delivery|Infra|Quality|Research)",
    failIf: "Overlaps existing agent responsibility ≥50%",
    maxDeduct: 5,
  },
  {
    id: "FG-5",
    check: "Canvas agent-<id> + DOC-008 + Task subagent_type same day",
    failIf: "Agent ships without roster/canvas/Task wiring",
    maxDeduct: 5,
  },
  {
    id: "FG-6",
    check: "Admission score ≥18/25 before merge",
    failIf: "Score <18 without accepted_divergence + rationale",
    maxDeduct: 5,
  },
];

const FUTURE_EXAMPLES: {
  proposed: string;
  skill: string;
  dims: ScoreDims;
  verdict: string;
}[] = [
  {
    proposed: "releaser",
    skill: "releaser-protocol",
    dims: { clarity: 5, brevity: 5, pairing: 5, convention: 5, uniqueness: 4 },
    verdict:
      "AA-ROSTER-002 deferred P2 — admit when release pain repeats (not this slice)",
  },
  {
    proposed: "ci-fixer",
    skill: "ci-fixer-protocol",
    dims: { clarity: 4, brevity: 4, pairing: 4, convention: 5, uniqueness: 4 },
    verdict:
      "AA-ROSTER-003 deferred P3 — prefer absorb into implementer (no new agent)",
  },
  {
    proposed: "enterprise-security-auditor",
    skill: "enterprise-security-architecture-audit",
    dims: { clarity: 3, brevity: 1, pairing: 3, convention: 2, uniqueness: 2 },
    verdict:
      "AA-ROSTER-004 reject — collide with auditor; extend auditor-protocol",
  },
];

/** Roster scorecard 2026-08-04 — mirror of alignment-audit AA-ROSTER-* */
const SCORECARD_KEEP_AGENTS: string[][] = [
  ["implementer", "22", "implementer-loop", "KEEP"],
  ["verifier", "22", "(none — optional verify-claims later)", "KEEP"],
  ["researcher", "22", "research-corpus", "KEEP"],
  ["test-runner", "21", "test-coverage", "KEEP"],
  ["board", "20", "board-ssot (+ board-shell)", "KEEP"],
  ["integrator", "20", "integrator-protocol", "KEEP"],
  ["auditor", "17", "auditor-protocol", "KEEP"],
  ["drift-guard", "16", "drift-audit", "KEEP"],
];

const SCORECARD_ADD: string[][] = [
  [
    "releaser",
    "releaser-protocol",
    "P2 deferred",
    "AA-ROSTER-002 — release lane gap; admit when pain repeats",
  ],
  [
    "ci-fixer",
    "ci-fixer-protocol",
    "P3 absorb",
    "AA-ROSTER-003 — prefer implementer; do not ship agent now",
  ],
];

const SCORECARD_REMOVE: string[][] = [
  ["(none)", "—", "AA-ROSTER-001 — all 8 agents kept; low scores = naming debt"],
];

const SCORECARD_RETIRE_SKILLS: string[][] = [
  [
    "audit-alignment",
    "Retire when safe",
    "AA-ROSTER-005 open — DEPRECATED stub → auditor (11/25)",
  ],
  [
    "verify-claims (new)",
    "Optional later",
    "AA-ROSTER-006 deferred — skill for verifier, not a new agent",
  ],
];

const SCORECARD_REJECT: string[][] = [
  [
    "enterprise-security-auditor",
    "AA-ROSTER-004",
    "Collides with auditor lane",
  ],
  ["onboarder", "AA-ROSTER-004", "Overlap board + board-shell + workflow-activate"],
  ["mcp-agent", "AA-ROSTER-004", "mcp-connect is skill-only by design"],
  ["documenter", "AA-ROSTER-004", "Doc-sync belongs to implementer"],
];

type RenameRow = {
  layer: Exclude<Layer, "all">;
  current: string;
  proposed: string;
  action: "keep" | "rename" | "alias" | "retire";
  priority: "P0" | "P1" | "P2";
  rationale: string;
};

const RENAME_ROWS: RenameRow[] = [
  {
    layer: "agents",
    current: "integrator-mas-agent",
    proposed: "integrator",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #147 — live id integrator",
  },
  {
    layer: "agents",
    current: "enterprise-auditor",
    proposed: "auditor",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #148 — live id auditor",
  },
  {
    layer: "agents",
    current: "workflow-drift-guard",
    proposed: "drift-guard",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #148 — live id drift-guard",
  },
  {
    layer: "agents",
    current: "project-board",
    proposed: "board",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #149 — live id board",
  },
  {
    layer: "agents",
    current: "implementer",
    proposed: "implementer",
    action: "keep",
    priority: "P2",
    rationale: "unchanged (never renamed)",
  },
  {
    layer: "agents",
    current: "verifier",
    proposed: "verifier",
    action: "keep",
    priority: "P2",
    rationale: "unchanged (never renamed)",
  },
  {
    layer: "agents",
    current: "researcher",
    proposed: "researcher",
    action: "keep",
    priority: "P2",
    rationale: "unchanged (never renamed)",
  },
  {
    layer: "agents",
    current: "test-runner",
    proposed: "test-runner",
    action: "keep",
    priority: "P2",
    rationale: "unchanged (never renamed)",
  },
  {
    layer: "skills",
    current: "mas-infrastructure-integration",
    proposed: "integrator-protocol",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #146 — live skill integrator-protocol",
  },
  {
    layer: "skills",
    current: "enterprise-architecture-audit",
    proposed: "auditor-protocol",
    action: "rename",
    priority: "P2",
    rationale:
      "SHIPPED #146 — live skill auditor-protocol (artifact dir path kept)",
  },
  {
    layer: "skills",
    current: "workflow-drift-audit",
    proposed: "drift-audit",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #146 — live skill drift-audit",
  },
  {
    layer: "skills",
    current: "implementation-execution-loop",
    proposed: "implementer-loop",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #140 — live skill implementer-loop",
  },
  {
    layer: "skills",
    current: "test-module-coverage",
    proposed: "test-coverage",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #140 — live skill test-coverage",
  },
  {
    layer: "skills",
    current: "project-board-ssot",
    proposed: "board-ssot",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #140 — live skill board-ssot",
  },
  {
    layer: "skills",
    current: "board-shell-onboard",
    proposed: "board-shell",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #140 — live skill board-shell",
  },
  {
    layer: "skills",
    current: "connect-external-mcp",
    proposed: "mcp-connect",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #140 — live skill mcp-connect",
  },
  {
    layer: "skills",
    current: "research-corpus-execution",
    proposed: "research-corpus",
    action: "rename",
    priority: "P2",
    rationale: "SHIPPED #140 — live skill research-corpus",
  },
];

const STACK = [
  ["Coordination", "board", "board-ssot (+ board-shell)"],
  ["Delivery", "implementer", "implementer-loop"],
  ["Delivery", "test-runner", "test-coverage"],
  ["Delivery", "verifier", "(inline / optional verify-claims)"],
  ["Infrastructure", "integrator", "integrator-protocol"],
  ["Quality", "auditor", "auditor-protocol"],
  ["Quality", "drift-guard", "drift-audit"],
  ["Research", "researcher", "research-corpus"],
];

function actionTone(action: RenameRow["action"]): PillTone {
  switch (action) {
    case "keep":
      return "success";
    case "rename":
      return "renamed";
    case "alias":
      return "info";
    case "retire":
      return "deleted";
    default: {
      const _exhaustive: never = action;
      return _exhaustive;
    }
  }
}

function priorityTone(p: RenameRow["priority"]): PillTone {
  switch (p) {
    case "P0":
      return "deleted";
    case "P1":
      return "warning";
    case "P2":
      return "neutral";
    default: {
      const _exhaustive: never = p;
      return _exhaustive;
    }
  }
}

function scoreRows(items: ScoredName[]) {
  return [...items]
    .sort((a, b) => total(b.dims) - total(a.dims))
    .map((s) => {
      const t = total(s.dims);
      const b = band(t);
      return [
        <Text weight="semibold" size="small">
          {s.id}
        </Text>,
        String(s.dims.clarity),
        String(s.dims.brevity),
        String(s.dims.pairing),
        String(s.dims.convention),
        String(s.dims.uniqueness),
        <Text weight="semibold">{String(t)}</Text>,
        <Pill tone={b.tone} size="sm">
          {b.label}
        </Pill>,
        <Text size="small">{s.note}</Text>,
      ];
    });
}

function scoreRowTones(items: ScoredName[]) {
  return [...items]
    .sort((a, b) => total(b.dims) - total(a.dims))
    .map((s) => bandTone(total(s.dims)));
}

function changeTone(
  c: "keep" | "rename" | "none" | "optional-new",
): PillTone {
  switch (c) {
    case "keep":
      return "success";
    case "rename":
      return "renamed";
    case "none":
      return "neutral";
    case "optional-new":
      return "info";
    default: {
      const _exhaustive: never = c;
      return _exhaustive;
    }
  }
}

export default function NamingRosterAuditCanvas() {
  const [view, setView] = useCanvasState<View>("view", "stack");
  const [layer, setLayer] = useCanvasState<Layer>("layer", "all");

  const agentAvg =
    Math.round(
      (AGENT_SCORES.reduce((acc, a) => acc + total(a.dims), 0) /
        AGENT_SCORES.length) *
        10,
    ) / 10;
  const skillAvg =
    Math.round(
      (SKILL_SCORES.reduce((acc, s) => acc + total(s.dims), 0) /
        SKILL_SCORES.length) *
        10,
    ) / 10;
  const below18 = AGENT_SCORES.filter((a) => total(a.dims) < 18).length;
  const lowestAgent = [...AGENT_SCORES].sort(
    (a, b) => total(a.dims) - total(b.dims),
  )[0]!;
  const sortedAgents = [...AGENT_SCORES].sort(
    (a, b) => total(b.dims) - total(a.dims),
  );

  const filteredRenames = RENAME_ROWS.filter(
    (r) => layer === "all" || r.layer === layer,
  );

  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 1140 }}>
      <Stack gap={6}>
        <Row gap={10} style={{ alignItems: "center", flexWrap: "wrap" }}>
          <H1 style={{ margin: 0 }}>Naming roster — live stack</H1>
          <Pill tone="info" size="sm">
            hub · not an agent
          </Pill>
          <Pill tone="success" size="sm">
            B-safe SHIPPED
          </Pill>
          <Pill tone="neutral" size="sm">
            8 agents · 14 skills
          </Pill>
        </Row>
        <Text tone="secondary" size="small">
          Verified {AUDIT_DATE} · Clarity+Brevity+Pairing+Convention+Uniqueness
          (/25) · Advisory. Default view = live Target stack. Plan/Scores use live
          ids. Renames tab = historical old→live ledger only (not Task types).
        </Text>
      </Stack>

      <Row gap={12} align="center" justify="space-between">
        <Grid columns={4} gap={12} style={{ flex: 1 }}>
          <Stat value={String(agentAvg)} label="Agent avg /25" />
          <Stat value={String(skillAvg)} label="Skill avg /25" />
          <Stat
            value={String(below18)}
            label="Agents below 18"
            tone={below18 > 0 ? "warning" : "success"}
          />
          <Stat
            value={String(total(lowestAgent.dims))}
            label={`Lowest agent (${lowestAgent.id})`}
            tone={total(lowestAgent.dims) < 18 ? "danger" : "warning"}
          />
        </Grid>
        <Select
          value={view}
          onChange={(v) => setView(v as View)}
          options={[
            { value: "stack", label: "Target stack (live)" },
            { value: "plan", label: "Plan table (live)" },
            { value: "scores", label: "Scores" },
            { value: "renames", label: "Old→live ledger" },
            { value: "future", label: "Future agents" },
          ]}
        />
      </Row>

      {view === "plan" ? (
        <Stack gap={16}>
          <Callout tone="success" title="B-safe rename SHIPPED — 2026-08-03">
            Live filesystem roster: 8 agents / 14 canonical skills / 7 rules.
            Agent descriptions prefixed Agent Colony (#153). Shared board-ssot is
            Entry/Exit for all agents. Plan rows below are keep/keep against the
            shipped names — not a pending rename plan.
          </Callout>

          <Stack gap={8}>
            <H2>Agent ↔ skill roster (live)</H2>
            <Text tone="secondary" size="small">
              Columns are live ids (post-rename). Δ keep = no further rename planned.
            </Text>
            <Table
              headers={[
                "Lane",
                "Agent (live)",
                "Skills (live)",
                "Agent (same)",
                "Skills (same)",
                "Δ agent",
                "Δ skill",
              ]}
              rows={PLAN_ROWS.map((r) => [
                r.lane,
                <Text weight="semibold" size="small">
                  {r.agentNow}
                </Text>,
                <Text size="small">{r.skillsNow}</Text>,
                <Text weight="semibold" size="small">
                  {r.agentNext}
                </Text>,
                <Text size="small">{r.skillsNext}</Text>,
                <Pill tone={changeTone(r.agentChange)} size="sm">
                  {r.agentChange}
                </Pill>,
                <Pill tone={changeTone(r.skillChange)} size="sm">
                  {r.skillChange}
                </Pill>,
              ])}
              rowTone={PLAN_ROWS.map((r) =>
                r.agentChange === "rename" || r.skillChange === "rename"
                  ? "warning"
                  : "success",
              )}
              striped
              stickyHeader
            />
          </Stack>

          <Stack gap={8}>
            <H2>Shared / skill-only (not owned by one agent)</H2>
            <Table
              headers={["Skill (live)", "Role"]}
              rows={SHARED_SKILLS.map(([a, b]) => [a, b])}
              striped
            />
          </Stack>

          <Callout tone="neutral" title="Intentional non-renames">
            Artifact dir .local/workflow-artifacts/enterprise-architecture-audit/
            · ops doc project-board-collaboration.md · snapshot
            project-board-snapshot.json — paths kept on purpose (not agent/skill
            ids).
          </Callout>

          <Card>
            <CardHeader>Confidence</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small">
                  Sure about current primary pairings — taken from agent cards.
                </Text>
                <Text size="small">
                  Residual score debt (pairing/brevity) remains advisory — rename
                  appetite for B-safe is closed.
                </Text>
                <Text size="small">
                  Historical: skills #140 then agents #146–#149 — B-safe SHIPPED.
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      ) : null}

      {view === "scores" ? (
        <Stack gap={16}>
          <Callout tone="info" title="How to read scores">
            Each name is scored 0–5 on five axes (total /25). Pair avg =
            mean(agent, primary skill). Admission bar for new agents: ≥18/25 unless
            accepted_divergence is documented.
          </Callout>

          <Stack gap={8}>
            <H2>Scoring rubric</H2>
            <Table
              headers={["Dimension", "Scale", "How to score"]}
              rows={RUBRIC.map((r) => [r.dim, r.weight, r.how])}
              striped
            />
            <Table
              headers={["Band", "Label", "Action"]}
              rows={BANDS.map((b) => [
                b.range,
                <Pill tone={b.tone} size="sm">
                  {b.label}
                </Pill>,
                b.action,
              ])}
            />
          </Stack>

          <Stack gap={8}>
            <H2>Agent name scores (current)</H2>
            <Text tone="secondary" size="small">
              Source: .cursor/agents/*.md · sorted by total descending
            </Text>
            <BarChart
              categories={sortedAgents.map((a) => a.id)}
              series={[
                {
                  name: "Total /25",
                  data: sortedAgents.map((a) => total(a.dims)),
                  tone: "info",
                },
              ]}
              horizontal
              height={280}
              yMax={25}
              referenceLines={[
                { value: 18, label: "Admit ≥18", tone: "warning" },
                { value: 22, label: "Excellent", tone: "success" },
              ]}
            />
            <Text tone="tertiary" size="small">
              Chart: agent total score · ref lines admit≥18 and excellent≥22 · {AUDIT_DATE}
            </Text>
            <Table
              headers={[
                "Agent",
                "Clar",
                "Brev",
                "Pair",
                "Conv",
                "Uniq",
                "Total",
                "Band",
                "Note",
              ]}
              rows={scoreRows(AGENT_SCORES)}
              rowTone={scoreRowTones(AGENT_SCORES)}
              striped
              stickyHeader
            />
          </Stack>

          <Stack gap={8}>
            <H2>Skill name scores (current)</H2>
            <Text tone="secondary" size="small">
              Canonical (.cursor/skills) + maintainer (.agents/skills) · /25
            </Text>
            <Table
              headers={[
                "Skill",
                "Clar",
                "Brev",
                "Pair",
                "Conv",
                "Uniq",
                "Total",
                "Band",
                "Note",
              ]}
              rows={scoreRows(SKILL_SCORES)}
              rowTone={scoreRowTones(SKILL_SCORES)}
              striped
              stickyHeader
            />
          </Stack>

          <Stack gap={8}>
            <H2>Agent ↔ primary skill pair score</H2>
            <Table
              headers={[
                "Agent",
                "Primary skill",
                "Agent /25",
                "Skill /25",
                "Pair avg",
                "Grade",
              ]}
              rows={PAIR_SCORES.map((p) => [
                p.agent,
                p.skill,
                String(p.agentTotal),
                String(p.skillTotal),
                <Text weight="semibold">{String(p.pairAvg)}</Text>,
                <Pill tone={band(Math.round(p.pairAvg)).tone} size="sm">
                  {p.grade}
                </Pill>,
              ])}
              rowTone={PAIR_SCORES.map((p) => bandTone(Math.round(p.pairAvg)))}
              striped
            />
          </Stack>
        </Stack>
      ) : null}

      {view === "stack" ? (
        <Stack gap={12}>
          <H2>Live stack (shipped roster)</H2>
          <Table
            headers={["Lane", "Agent", "Primary skill"]}
            rows={STACK.map(([lane, agent, skill]) => [
              lane,
              <Text weight="semibold">{agent}</Text>,
              skill,
            ])}
            striped
          />
          <Callout tone="success" title="B-safe rename debt closed · AA-ROSTER-001">
            Live ids: board · implementer · test-runner · verifier · integrator ·
            auditor · drift-guard · researcher. KEEP all 8 — residual score debt
            (drift-guard 16 / auditor 17) is naming debt, not redundancy.
          </Callout>
          <Callout tone="neutral" title="CLI / MCP stack (kit 0.6.4)">
            Renames landed in v0.6.0 (CLI) / v0.6.1 (MCP). Current kit 0.6.4:
            Python module agent_colony · console agent-colony · MCP package
            agent_colony_mcp · Cursor server id agent-colony-mcp (unchanged).
          </Callout>
          <H2>Scorecard keep (agent /25)</H2>
          <Table
            headers={["Agent", "/25", "Primary skill", "Verdict"]}
            rows={SCORECARD_KEEP_AGENTS}
            striped
          />
          <Callout tone="neutral" title="Intentional path keeps">
            enterprise-architecture-audit/ (artifact dir) ·
            project-board-collaboration.md (ops) · project-board-snapshot.json —
            not agent or skill folder names. Evidence: alignment-audit.md § Roster
            scorecard 2026-08-04.
          </Callout>
        </Stack>
      ) : null}

      {view === "renames" ? (
        <Stack gap={12}>
          <Callout tone="warning" title="Historical ledger — not live Task ids">
            Old = pre-rename id (retired). Live = today’s id after B-safe (#140,
            #146–#149). Action rename = completed rename; keep = never renamed.
            Do not treat Old as today’s subagent_type.
          </Callout>
          <Row gap={12} align="center" justify="space-between">
            <H2>Old → live (SHIPPED)</H2>
            <Select
              value={layer}
              onChange={(v) => setLayer(v as Layer)}
              options={[
                { value: "all", label: "All" },
                { value: "agents", label: "Agents" },
                { value: "skills", label: "Skills" },
              ]}
            />
          </Row>
          <Table
            headers={["Pri", "Layer", "Old (retired)", "Live (shipped)", "Action", "Why"]}
            rows={filteredRenames.map((r) => [
              <Pill tone={priorityTone(r.priority)} size="sm">
                {r.priority}
              </Pill>,
              r.layer,
              r.current,
              <Text weight="semibold" size="small">
                {r.proposed}
              </Text>,
              <Pill tone={actionTone(r.action)} size="sm">
                {r.action}
              </Pill>,
              r.rationale,
            ])}
            striped
          />
          <Card>
            <CardHeader>Rename appetite (closed)</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <Text size="small">
                  B-safe SHIPPED 2026-08-03 — this tab is the audit trail only.
                </Text>
                <Text size="small">
                  Was B) A+B — auditor / drift-guard / board + skill pairs (done)
                </Text>
                <Text size="small">
                  Was C) Full — rules *-policy (deferred / not in B-safe)
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      ) : null}

      {view === "future" ? (
        <Stack gap={16}>
          <Callout tone="info" title="Roster scorecard 2026-08-04 (AA-ROSTER)">
            Advisory only — no new agents for security/perf/infra/docs/
            granularity (AA-ROSTER-004). Retire = audit-alignment stub kept
            RETIRE-PENDING until DOC/count integrator slice (AA-ROSTER-005).
            Full tables: .local/workflow-artifacts/alignment/alignment-audit.md
          </Callout>

          <Stack gap={8}>
            <H2>Agents to add (advisory)</H2>
            <Table
              headers={["Candidate", "Skill", "Priority", "Finding"]}
              rows={SCORECARD_ADD}
              striped
            />
          </Stack>

          <Stack gap={8}>
            <H2>Agents to remove</H2>
            <Table
              headers={["Agent", "Action", "Rationale"]}
              rows={SCORECARD_REMOVE}
              striped
            />
          </Stack>

          <Stack gap={8}>
            <H2>Skills to retire / optional add</H2>
            <Table
              headers={["Skill", "Action", "Finding"]}
              rows={SCORECARD_RETIRE_SKILLS}
              striped
            />
          </Stack>

          <Stack gap={8}>
            <H2>Do not add (rejected)</H2>
            <Table
              headers={["Candidate", "Finding", "Why"]}
              rows={SCORECARD_REJECT}
              striped
            />
          </Stack>

          <Callout tone="info" title="Admission gate for new agents">
            Before merge, score the proposed agent id + primary skill with the same
            rubric. Require total ≥18/25 and FG-1…FG-6 green. Prefer extending an
            existing lane over adding a near-duplicate.
          </Callout>

          <Stack gap={8}>
            <H2>Future-agent checklist</H2>
            <Table
              headers={["Id", "Check", "Fail if", "Max deduct"]}
              rows={FUTURE_GATES.map((g) => [
                g.id,
                g.check,
                g.failIf,
                String(g.maxDeduct),
              ])}
              striped
            />
          </Stack>

          <Stack gap={8}>
            <H2>Scorecard template (copy for new proposals)</H2>
            <Table
              headers={[
                "Field",
                "Value",
                "Clar",
                "Brev",
                "Pair",
                "Conv",
                "Uniq",
                "Total",
              ]}
              rows={[
                [
                  "Proposed agent",
                  "<role-noun>",
                  "?",
                  "?",
                  "?",
                  "?",
                  "?",
                  "?/25",
                ],
                [
                  "Primary skill",
                  "<role>-protocol|loop",
                  "?",
                  "?",
                  "?",
                  "?",
                  "?",
                  "?/25",
                ],
                [
                  "Pair avg",
                  "mean(agent, skill)",
                  "—",
                  "—",
                  "—",
                  "—",
                  "—",
                  "≥18",
                ],
                [
                  "Lane",
                  "Coordination|Delivery|Infra|Quality|Research",
                  "—",
                  "—",
                  "—",
                  "—",
                  "—",
                  "unique",
                ],
              ]}
            />
          </Stack>

          <Stack gap={8}>
            <H2>Worked examples (hypothetical adds)</H2>
            <Table
              headers={[
                "Proposed agent",
                "Skill",
                "Total",
                "Band",
                "Verdict",
              ]}
              rows={FUTURE_EXAMPLES.map((e) => {
                const t = total(e.dims);
                const b = band(t);
                return [
                  e.proposed,
                  e.skill,
                  String(t),
                  <Pill tone={b.tone} size="sm">
                    {b.label}
                  </Pill>,
                  <Text size="small">{e.verdict}</Text>,
                ];
              })}
              rowTone={FUTURE_EXAMPLES.map((e) => bandTone(total(e.dims)))}
              striped
            />
          </Stack>

          <Card>
            <CardHeader>Integrator (kit) obligation</CardHeader>
            <CardBody>
              <Stack gap={6}>
                <H3>When adding any agent</H3>
                <Text size="small">
                  Run this scorecard in the integration card Notes, then wire
                  agent card + primary skill + canvas agent-&lt;id&gt; + DOC-008 +
                  Task subagent_type in one slice.
                </Text>
                <Text size="small">
                  Reject names scoring &lt;18 unless the human records
                  accepted_divergence with rationale on the board card.
                </Text>
              </Stack>
            </CardBody>
          </Card>
        </Stack>
      ) : null}

      <Divider />
      <Text tone="tertiary" size="small">
        Live truth: .cursor/agents/*.md · .cursor/skills/*/SKILL.md · Roster
        scorecard: .local/workflow-artifacts/alignment/alignment-audit.md §
        2026-08-04 · AA-ROSTER-001…008 · verified {AUDIT_DATE}
      </Text>
    </Stack>
  );
}
