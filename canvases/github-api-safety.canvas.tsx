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
  Spacer,
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

/**
 * Inventory of GitHub API hammering / safety protections in MAS Workflow Kit.
 * Source: project_outbox.py, project_atomics, agent Board-rights blocks, ADR-008.
 * Verified: 2026-07-19
 */

const HARD = [
  {
    layer: "Outbox enqueue",
    what: "On rate-limit stderr → JSONL queue; EXIT_QUEUED (6)",
    where: "project_outbox.maybe_enqueue_on_gh_fail",
    enforces: "Code",
  },
  {
    layer: "Flush quota gate",
    what: "Refuse flush if GraphQL remaining < min (default 200)",
    where: "flush_outbox + outbox status",
    enforces: "Code",
  },
  {
    layer: "Flush batch cap",
    what: "max_flush_per_run (default 10) + mid-batch re-check",
    where: "flush_outbox loop",
    enforces: "Code",
  },
  {
    layer: "Flush backoff",
    what: "sleep(retry_backoff_seconds) after non-RL failure (default 30s)",
    where: "flush_outbox",
    enforces: "Code",
  },
  {
    layer: "RL detector",
    what: "Regex: rate limit / secondary rate limit",
    where: "is_rate_limit_error",
    enforces: "Code",
  },
  {
    layer: "Placeholder IDs",
    what: "Reject short/ellipsis PVTI_ stubs (CODE=2)",
    where: "is_placeholder_item_id / resolve_item_id_arg",
    enforces: "Code",
  },
  {
    layer: "Doctor skip-live",
    what: "Skip item-list when remaining < min_graphql_remaining",
    where: "run_doctor",
    enforces: "Code",
  },
  {
    layer: "Pattern A recipes",
    what: "claim/handoff/create wrap atomics; --last preferred",
    where: "project_handlers + project guide",
    enforces: "Code + docs",
  },
] as const;

const SOFT = [
  {
    layer: "Agent Board rights",
    what: "EXIT_QUEUED → do not hammer; outbox status/flush",
    where: "All 8 agent cards",
  },
  {
    layer: "Skill checklist",
    what: "Exit: no retry loop; confirm outbox status",
    where: "project-board-ssot/SKILL.md",
  },
  {
    layer: "Always-apply rule",
    what: "EXIT_QUEUED → outbox; no GraphQL hammer; no dual-write",
    where: "project-ssot-precedence.mdc",
  },
  {
    layer: "Researcher anti-loop",
    what: "rounds ≤6; one clone attempt; no re-init without --force",
    where: "researcher + research-corpus-execution",
  },
  {
    layer: "Read-only export",
    what: "project export never mutates Status",
    where: "ADR-008 / project-board-collaboration",
  },
] as const;

const GAPS = [
  {
    gap: "Raw gh / GraphQL outside CLI",
    risk: "Bypasses outbox entirely",
    note: "Policy-only — Pattern A CLI required; cannot sandbox Cursor shell",
  },
  {
    gap: "EXIT_QUEUED obedience is soft",
    risk: "Agent can ignore code 6 and re-run claim",
    note: "Stronger CODE=6 messaging; LLM compliance still soft",
  },
] as const;

const FIXED = [
  {
    id: "G1",
    what: "Cached REST rate_limit precheck (TTL 45s) before Pattern A writes",
  },
  {
    id: "G2",
    what: "Queue Forbidden/429 throttle; exclude missing-scopes",
  },
  {
    id: "G5",
    what: "Pending outbox dedupe by op+item+payload",
  },
] as const;

const CONFIG = [
  ["outbox.enabled", "true", "Master switch"],
  ["min_graphql_remaining", "200", "Flush / precheck gate"],
  ["precheck_writes", "true", "Cached REST before writes"],
  ["quota_cache_ttl_seconds", "45", "REST cache TTL"],
  ["dedupe_pending", "true", "One pending row per fingerprint"],
  ["max_flush_per_run", "10", "Ops per flush"],
  ["retry_backoff_seconds", "30", "Sleep after failed apply"],
] as const;

export default function GithubApiSafetyCanvas() {
  return (
    <Stack gap={20} style={{ padding: 24, maxWidth: 960 }}>
      <Stack gap={6}>
        <Row gap={8} align="center">
          <H1>GitHub API safety</H1>
          <Pill tone="neutral">2026-07-19</Pill>
        </Row>
        <Text tone="secondary">
          How MAS Workflow Kit limits API hammering and unsafe Project writes —
          hard (code), soft (policy), and real gaps.
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="3" label="Gaps fixed (G1/G2/G5)" />
        <Stat value="2" label="Residual soft gaps" />
        <Stat value="CODE=6" label="Do not retry" />
      </Grid>

      <Callout tone="info">
        Verdict: cached precheck + Forbidden/429 queue + pending dedupe for
        Pattern A writes. Safe if agents use{" "}
        <Text weight="semibold">cursor_workflow project …</Text> and stop on
        EXIT_QUEUED (6).
      </Callout>

      <H2>Fixed in this slice</H2>
      <Table
        headers={["ID", "Fix"]}
        rows={FIXED.map((r) => [r.id, r.what])}
      />

      <H2>Hard protections (enforced in code)</H2>
      <Table
        headers={["Layer", "Behavior", "Where", "Kind"]}
        rows={HARD.map((r) => [r.layer, r.what, r.where, r.enforces])}
      />

      <H2>Config defaults</H2>
      <Text tone="secondary" size="small">
        github.collaboration.yaml → project_ssot.outbox
      </Text>
      <Table
        headers={["Key", "Default", "Role"]}
        rows={CONFIG.map(([k, d, role]) => [k, d, role])}
      />

      <H2>Soft protections (agents / rules)</H2>
      <Table
        headers={["Layer", "Instruction", "Where"]}
        rows={SOFT.map((r) => [r.layer, r.what, r.where])}
      />

      <H2>Exit codes that matter</H2>
      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader>EXIT_QUEUED = 6</CardHeader>
          <CardBody>
            <Text>
              Soft-success: op landed in outbox. Agent must continue local work
              — not retry gh in a loop.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Flush refuse</CardHeader>
          <CardBody>
            <Text>
              remaining &lt; min_graphql_remaining → EXIT_GH, wait for reset.
              Mid-batch re-checks quota.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <H2>Flow</H2>
      <Card>
        <CardBody>
          <Stack gap={4}>
            <Text size="small">1. Write fails with rate-limit stderr</Text>
            <Text size="small">2. maybe_enqueue_on_gh_fail → board-outbox.jsonl</Text>
            <Text size="small">3. EXIT_QUEUED (6) — soft success</Text>
            <Text size="small">4. Agent continues local evidence (no retry loop)</Text>
            <Text size="small">
              5. Later: outbox status → outbox flush (cap 10 · remaining≥200 ·
              backoff 30s)
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Divider />

      <H2>Residual gaps (accepted)</H2>
      <Table
        headers={["Gap", "Risk", "Note"]}
        rows={GAPS.map((g) => [g.gap, g.risk, g.note])}
      />

      <Callout tone="warning">
        Forbidden/403 and raw <Text weight="semibold">gh api graphql</Text>{" "}
        bypass the outbox. Parallel agents can still pile pending ops on one
        card (hygiene, not a hard lock).
      </Callout>

      <Spacer height={8} />
      <Text tone="secondary" size="small">
        Canon: ADR-008 · project_outbox.py · project-board-ssot skill ·
        project-ssot-precedence.mdc · project-board-collaboration.md § Rate
        limits
      </Text>
    </Stack>
  );
}
