/**
 * File: mcp-onboarding.canvas.tsx
 * Path: canvases/mcp-onboarding.canvas.tsx
 * Role: Pattern A MCP onboarding — kit server + DeepWiki default + custom servers.
 * Used By:
 *  - humans / agents connecting MCP (mcp-connect skill)
 * Depends On:
 *  - ADR-009 · ADR-004 · connect-external-mcp.md · mcp-connect/SKILL.md
 * Notes:
 *  - DeepWiki is the consumer default zero-auth explore/test server until users add theirs.
 *  - Kit-dev may keep live registry kit-only; seed/example + mcp.user.json still enable DeepWiki.
 */

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
  Stack,
  Stat,
  Table,
  Text,
} from "cursor/canvas";

const VERIFIED = "2026-08-06";
const SOURCES =
  "ADR-009 · ADR-004 · connect-external-mcp.md · mcp-connect/SKILL.md · mcp.registry.yaml.example · mcp.user.example.json";

/** Seven Pattern A agents (board is not on DeepWiki allowlist by default). */
const PATTERN_A_AGENTS = [
  "implementer",
  "test-runner",
  "verifier",
  "auditor",
  "researcher",
  "integrator",
  "drift-guard",
];

const TWO_TIER: string[][] = [
  [
    "Kit",
    "agent-colony-mcp",
    "mcp.json.kit.example → mcp.json",
    "PR / trackers / gates (stdio workflow_mcp)",
  ],
  [
    "User (default)",
    "deepwiki",
    "mcp seed --deepwiki → mcp.user.json + registry",
    "Zero-auth remote GitHub wiki Q&A — explore/test MCP",
  ],
  [
    "User (yours)",
    "my-custom-server / …",
    "mcp link or edit mcp.user.json + registry agents",
    "Auth/private APIs after DeepWiki proves the path",
  ],
];

const SEED_FLOW: Array<[string, string]> = [
  [
    "1) Seed DeepWiki (consumer default)",
    "python3 -m cursor_workflow mcp seed --deepwiki",
  ],
  [
    "2) Merge + validate",
    "python3 -m cursor_workflow mcp validate",
  ],
  [
    "3) Doctor (config vs Cursor host)",
    "python3 -m cursor_workflow mcp doctor",
  ],
  [
    "4) Smoke DeepWiki",
    "python3 -m cursor_workflow mcp smoke --server deepwiki",
  ],
  [
    "5) Smoke kit server",
    "python3 -m cursor_workflow mcp smoke --server agent-colony-mcp",
  ],
];

const KIT_COMMANDS: Array<[string, string]> = [
  [
    "List kit tools",
    "python3 -m cursor_workflow mcp list-tools --server agent-colony-mcp",
  ],
  [
    "Call kit tool",
    "python3 -m cursor_workflow mcp call --server agent-colony-mcp --tool workflow_gate_count",
  ],
];

const DEEPWIKI_DEMO: Array<[string, string]> = [
  [
    "List tools",
    "python3 -m cursor_workflow mcp list-tools --server deepwiki",
  ],
  [
    "Wiki structure",
    "python3 -m cursor_workflow mcp call --server deepwiki --tool read_wiki_structure --args-json '{\"repoName\":\"cloudflare/workers-sdk\"}'",
  ],
  [
    "Ask a question",
    "python3 -m cursor_workflow mcp call --server deepwiki --tool ask_question --args-json '{\"repoName\":\"cloudflare/workers-sdk\",\"question\":\"What are the Workers KV limits?\"}'",
  ],
];

const ADD_YOURS: Array<[string, string]> = [
  [
    "Link fragment",
    "python3 -m cursor_workflow mcp link --name my-api --file .cursor/mcp.d/my-api.json",
  ],
  [
    "Map agents",
    "Edit .cursor/mcp.registry.yaml — servers.<id>.agents + tools_hint",
  ],
  [
    "Auth (if needed)",
    "python3 -m cursor_workflow mcp auth --server my-api --token-env MY_TOKEN",
  ],
  [
    "Validate + smoke",
    "python3 -m cursor_workflow mcp validate && python3 -m cursor_workflow mcp smoke --server my-api",
  ],
];

const CONFIG_LOCATIONS: string[][] = [
  [
    ".cursor/mcp.json",
    "Merged kit + user transports (Cursor host may load these)",
  ],
  [
    ".cursor/mcp.user.json",
    "User servers only (gitignored) — deepwiki URL + your servers",
  ],
  [
    ".cursor/mcp.registry.yaml",
    "Allowlist: which server id → which agent ids (Pattern A call gate)",
  ],
  [
    ".cursor/mcp.registry.yaml.example",
    "Worksheet: kit + deepwiki (7 agents) + my-custom-server stub",
  ],
  [
    ".local/user_settings/mcp.agents.yaml",
    "Human worksheet (optional) before applying to user/registry",
  ],
  [
    ".local/user_settings/mcp.secrets.yaml",
    "Tokens for mcp auth (gitignored)",
  ],
];

const CLI_LEAVES: string[][] = [
  ["validate", "Merge kit+user MCP; check registry"],
  ["seed", "Seed DeepWiki into mcp.user.json + registry"],
  ["link", "Link fragment into mcp.user.json"],
  ["doctor", "Configured vs Cursor host-loaded"],
  ["list-tools", "List tools for allowlisted server"],
  ["call", "Call tool on allowlisted server"],
  ["auth", "Store secrets under .local/user_settings"],
  ["smoke", "Initialize + list tools; write evidence"],
];

const TROUBLESHOOTING: string[][] = [
  [
    "DeepWiki “Repository Not Indexed”",
    "Wait for indexing, or use a known indexed repo (cloudflare/workers-sdk).",
  ],
  [
    "configured but NOT host-loaded",
    "Normal for Pattern A — CLI still works; Cursor host load is optional.",
  ],
  [
    "No module named 'mcp' / workflow_mcp",
    "Use venv: .venv/bin/python -m cursor_workflow … (pip install -e \".[dev,mcp]\").",
  ],
  [
    "Kit-dev live registry has only agent-colony-mcp",
    "Expected — CI stays kit-tier. Consumers seed DeepWiki; or merge from .example / mcp seed.",
  ],
  [
    "Strict validate fails",
    "Use mcp validate (non-strict) until live registry + user fragment are complete.",
  ],
  [
    "ask_question arg name",
    "Use repoName (not repo) in --args-json.",
  ],
];

export default function MCPOnboardingCanvas() {
  return (
    <Stack gap={20} style={{ padding: 20, maxWidth: 980 }}>
      <Stack gap={8}>
        <Row gap={10} align="center" wrap>
          <H1 style={{ margin: 0 }}>MCP onboarding (Pattern A)</H1>
          <Pill tone="info" size="sm">
            ADR-009
          </Pill>
          <Pill tone="success" size="sm">
            DeepWiki default
          </Pill>
        </Row>
        <Text tone="secondary">
          Canonical path for agents + CI:{" "}
          <Text weight="semibold">cursor_workflow mcp</Text> (validate → seed /
          link → doctor → smoke → list-tools → call). Cursor IDE host loading is
          optional convenience.
        </Text>
        <Text tone="tertiary" size="small">
          Source: {SOURCES} · verified {VERIFIED}
        </Text>
      </Stack>

      <Grid columns={3} gap={12}>
        <Stat value="agent-colony-mcp" label="Kit stdio server" />
        <Stat value="deepwiki" label="Default explore/test" tone="success" />
        <Stat value="8" label="CLI leaves (incl. seed)" />
      </Grid>

      <Callout tone="success" title="DeepWiki = default until you add yours">
        <Stack gap={6}>
          <Text>
            Consumer activate (with_mcp) and{" "}
            <Pill>mcp seed --deepwiki</Pill> write a zero-auth remote server so
            users can explore MCP end-to-end before wiring private/auth servers.
          </Text>
          <Text>
            Mapped by default to seven Pattern A agents (not board):
          </Text>
          <Row gap={6} wrap>
            {PATTERN_A_AGENTS.map((a) => (
              <Pill key={a} size="sm">
                {a}
              </Pill>
            ))}
          </Row>
          <Text tone="secondary" size="small">
            Transport: url https://mcp.deepwiki.com/mcp · tools:
            read_wiki_structure · read_wiki_contents · ask_question
          </Text>
        </Stack>
      </Callout>

      <H2>Two-tier model</H2>
      <Table
        headers={["Tier", "Server id", "Config", "Purpose"]}
        rows={TWO_TIER}
        striped
      />

      <Divider />

      <Card>
        <CardHeader>Quick start — seed DeepWiki + prove the path</CardHeader>
        <CardBody>
          <Table headers={["Step", "Command"]} rows={SEED_FLOW} striped />
        </CardBody>
      </Card>

      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader>Kit calls (agent-colony-mcp)</CardHeader>
          <CardBody>
            <Table headers={["Action", "Command"]} rows={KIT_COMMANDS} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader>DeepWiki demo calls</CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Table headers={["Action", "Command"]} rows={DEEPWIKI_DEMO} />
              <Text tone="tertiary" size="small">
                Args use <Pill>repoName</Pill> (not <Pill>repo</Pill>).
              </Text>
            </Stack>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHeader>Then add your own server</CardHeader>
        <CardBody>
          <Stack gap={8}>
            <Text size="small" tone="secondary">
              Keep DeepWiki for docs/Q&A demos; link Slack/DB/GitHub/custom next.
              Worksheet stub: my-custom-server in mcp.user.example.json.
            </Text>
            <Table headers={["Step", "Command / action"]} rows={ADD_YOURS} />
          </Stack>
        </CardBody>
      </Card>

      <Divider />

      <H2>CLI leaves</H2>
      <Table headers={["Command", "Role"]} rows={CLI_LEAVES} striped />

      <H2>Where to configure</H2>
      <Table headers={["Path", "Role"]} rows={CONFIG_LOCATIONS} striped />

      <Callout tone="info" title="What to tell an agent">
        <Stack gap={6}>
          <Text>
            Prefer Pattern A CLI over assuming Cursor host MCP is loaded. Only
            call servers listed for your agent id in mcp.registry.yaml.
          </Text>
          <Text>
            DeepWiki flow: read_wiki_structure → ask_question (or
            read_wiki_contents). Return answer + short wiki pointers + caveat if
            indexing is incomplete.
          </Text>
          <Text>
            Skill: .cursor/skills/mcp-connect/SKILL.md · Ops:
            connect-external-mcp.md
          </Text>
        </Stack>
      </Callout>

      <Card>
        <CardHeader>Troubleshooting</CardHeader>
        <CardBody>
          <Table headers={["Issue", "Fix"]} rows={TROUBLESHOOTING} striped />
        </CardBody>
      </Card>

      <Text tone="tertiary" size="small">
        Caption: {SOURCES} · verified {VERIFIED}. Kit-dev may skip DeepWiki seed
        so CI health stays kit-tier only.
      </Text>
    </Stack>
  );
}
