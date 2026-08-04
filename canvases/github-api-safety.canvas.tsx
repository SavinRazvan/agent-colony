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
 * Source: project_outbox.py, project_cli/handlers, agent Board-rights, ADR-008.
 * Verified: 2026-08-03 — post rename + canvas reality; G1 wording aligned to GraphQL remaining via REST cache (agent ids: auditor/board/drift-guard/integrator)
 */

const FIXED = [
  {
    id: "G1",
    what: "Cached GraphQL remaining via REST rate_limit (TTL 45s) before Pattern A writes — EXIT_QUEUED without GraphQL mutation",
  },
  {
    id: "G2",
    what: "Queue Forbidden / 429 / secondary throttle; never queue missing-scopes",
  },
  {
    id: "G3",
    what: "Stronger CODE=6 messaging in skill + rule (do not retry-loop)",
  },
  {
    id: "G4",
    what: "Ops docs + exemplar + schema document precheck / dedupe / throttle",
  },
  {
    id: "G5",
    what: "Pending outbox dedupe by op + item_id + payload fingerprint",
  },
] as const;

const HARD = [
  {
    layer: "Write precheck (G1)",
    what: "guard_write_or_queue: cached GraphQL remaining; enqueue if < min",
    where: "project_cli + project_handlers (claim/handoff/set-*/mention-pr/…)",
    enforces: "Code",
  },
  {
    layer: "Quota cache",
    what: "REST rate_limit cached (TTL); note_successful_write refreshes",
    where: "project_outbox read/write_quota_cache",
    enforces: "Code",
  },
  {
    layer: "Throttle detector (G2)",
    what: "rate-limit / 429 / Forbidden — exclude missing required scopes",
    where: "is_queueable_gh_throttle",
    enforces: "Code",
  },
  {
    layer: "Outbox enqueue",
    what: "On throttle stderr → JSONL; EXIT_QUEUED (6); CODE=6 do-not-retry text",
    where: "maybe_enqueue_on_gh_fail / queued_message",
    enforces: "Code",
  },
  {
    layer: "Pending dedupe (G5)",
    what: "Same op+item+payload → one pending row when dedupe_pending",
    where: "enqueue_op / find_duplicate_pending",
    enforces: "Code",
  },
  {
    layer: "Flush quota gate",
    what: "Refuse flush if remaining < min_graphql_remaining (default 200)",
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
    what: "sleep(retry_backoff_seconds) after soft apply failure (default 30s)",
    where: "flush_outbox",
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
    what: "EXIT_QUEUED / precheck / Forbidden → do not hammer; outbox flush later",
    where: "All 8 agent cards",
  },
  {
    layer: "Skill checklist (G3)",
    what: "Exit: CODE=6 = soft-success; no retry loop; outbox status",
    where: "board-ssot/SKILL.md",
  },
  {
    layer: "Always-apply rule (G3)",
    what: "EXIT_QUEUED covers precheck + Forbidden/429; no dual-write",
    where: "project-ssot-precedence.mdc",
  },
  {
    layer: "Ops + exemplar (G4)",
    what: "Precheck / dedupe / throttle documented for consumers",
    where: "project-board-collaboration · PLUGIN-USER-GUIDE · collab YAML",
  },
  {
    layer: "Researcher anti-loop",
    what: "rounds ≤6; one clone attempt; no re-init without --force",
    where: "researcher + research-corpus",
  },
  {
    layer: "Read-only export",
    what: "project export never mutates Status",
    where: "ADR-008 / project-board-collaboration",
  },
] as const;

const GAPS = [
  {
    gap: "Raw gh / GraphQL outside Pattern A CLI",
    risk: "Bypasses outbox + precheck entirely",
    note: "Policy-only — require cursor_workflow project …; cannot sandbox Cursor shell",
  },
  {
    gap: "EXIT_QUEUED obedience is soft",
    risk: "Agent can ignore code 6 and re-run claim",
    note: "Messaging hardened (G3); LLM compliance still soft",
  },
] as const;

const CONFIG = [
  ["outbox.enabled", "true", "Master switch"],
  ["min_graphql_remaining", "200", "Flush + precheck gate"],
  ["precheck_writes", "true", "Cached GraphQL remaining before Pattern A writes"],
  ["quota_cache_ttl_seconds", "45", "REST→GraphQL quota cache TTL"],
  ["quota_cache_path", ".local/…/graphql-quota-cache.json", "Cache file"],
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
          <Pill tone="neutral">PR #83 · #85</Pill>
          <Pill tone="success">G1–G5 done</Pill>
        </Row>
        <Text tone="secondary">
          How MAS-SSOT-KIT limits API hammering on Project writes — hard (code),
          soft (policy), and accepted residual gaps. Post G1–G5. Soft layer
          binds all 8 live agents (auditor · board · drift-guard · implementer ·
          integrator · researcher · test-runner · verifier).
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="5" label="Gaps fixed (G1–G5)" />
        <Stat value="2" label="Residual soft gaps" />
        <Stat value="CODE=6" label="Do not retry" />
      </Grid>

      <Callout tone="info" title="Verdict">
        Pattern A writes use cached precheck + Forbidden/429 queue + pending
        dedupe. Safe when agents use{" "}
        <Text weight="semibold">python3 -m cursor_workflow project …</Text> and
        treat EXIT_QUEUED (6) as soft-success (no retry loop). Ops doc path
        project-board-collaboration.md is intentional (not the retired
        project-board agent id).
      </Callout>

      <H2>Fixed (G1–G5)</H2>
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
        github.collaboration.yaml → project_ssot.outbox (schema documents all
        keys)
      </Text>
      <Table
        headers={["Key", "Default", "Role"]}
        rows={CONFIG.map(([k, d, role]) => [k, d, role])}
      />

      <H2>Soft protections (agents / rules / docs)</H2>
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
              Soft-success: op is in outbox (or precheck refused the live call).
              Continue local evidence — do not retry gh in a loop.
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Flush refuse</CardHeader>
          <CardBody>
            <Text>
              remaining &lt; min_graphql_remaining → do not flush; wait for
              reset. Mid-batch re-checks quota.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <H2>Flow (Pattern A write)</H2>
      <Card>
        <CardBody>
          <Stack gap={4}>
            <Text size="small">
              1. guard_write_or_queue — if cached remaining &lt; min → enqueue +
              EXIT_QUEUED (no GraphQL)
            </Text>
            <Text size="small">
              2. Else perform write (claim / handoff / set-status / …)
            </Text>
            <Text size="small">
              3. On throttle stderr (rate-limit / 429 / Forbidden) → enqueue +
              EXIT_QUEUED (dedupe pending)
            </Text>
            <Text size="small">
              4. On success → note_successful_write (refresh quota cache)
            </Text>
            <Text size="small">
              5. Agent continues local work — never retry-loop on CODE=6
            </Text>
            <Text size="small">
              6. Later: outbox status → outbox flush (cap 10 · remaining≥200 ·
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
        Raw <Text weight="semibold">gh api graphql</Text> (and any non–Pattern A
        path) still bypasses the outbox. Missing-scopes auth errors are{" "}
        <Text weight="semibold">not</Text> queued (fail loud). Parallel agents
        can still stack distinct pending ops on one card (dedupe only identical
        fingerprints).
      </Callout>

      <Spacer height={8} />
      <Text tone="secondary" size="small">
        Canon: ADR-008 · project_outbox.py · board-ssot skill ·
        project-ssot-precedence.mdc · project-board-collaboration.md § Rate
        limits · github-collaboration.schema.json
      </Text>
    </Stack>
  );
}
