import {
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  H1,
  Pill,
  Stack,
  Table,
  Text,
} from "cursor/canvas";

const VERIFIED = "2026-08-05";

const REGISTRY_SNAPSHOT = {
  workflowKit: {
    serverId: "agent-colony-mcp",
    tier: "kit",
    agents: [
      "implementer",
      "test-runner",
      "verifier",
      "auditor",
      "researcher",
      "integrator",
      "drift-guard",
    ],
  },
  deepwiki: {
    serverId: "deepwiki",
    tier: "external",
    agents: ["researcher", "implementer", "auditor"],
    tools: ["read_wiki_structure", "read_wiki_contents", "ask_question"],
  },
};

const FLOW_COMMANDS: Array<[string, string]> = [
  [
    "1) Merge + sanity check",
    "python3 -m cursor_workflow mcp validate",
  ],
  [
    "2) Doctor (config vs Cursor host)",
    "python3 -m cursor_workflow mcp doctor",
  ],
  [
    "3) Discover tools",
    "python3 -m cursor_workflow mcp list-tools --server agent-colony-mcp",
  ],
  [
    "4) Call a tool (kit stdio example)",
    "python3 -m cursor_workflow mcp call --server agent-colony-mcp --tool workflow_gate_count",
  ],
];

const DEEPWIKI_DEMO_COMMANDS: Array<[string, string]> = [
  [
    "A) Smoke DeepWiki server",
    "python3 -m cursor_workflow mcp smoke --server deepwiki",
  ],
  [
    "B) List wiki topics for a repo",
    "python3 -m cursor_workflow mcp call --server deepwiki --tool read_wiki_structure --args-json '{\"repoName\":\"cloudflare/workers-sdk\"}'",
  ],
  [
    "C) Ask a factual question",
    "python3 -m cursor_workflow mcp call --server deepwiki --tool ask_question --args-json '{\"repoName\":\"cloudflare/workers-sdk\",\"question\":\"What are the Workers KV limits (key size, value size, TTL/cache TTL)?\"}'",
  ],
];

const CONFIG_LOCATIONS = [
  {
    path: ".cursor/mcp.registry.yaml",
    role: "Allowlist mapping: which server id is allowed for which agent ids.",
  },
  {
    path: ".cursor/mcp.user.json",
    role: "Transport config (command/args or url) for user servers; gitignored.",
  },
  {
    path: ".local/user_settings/mcp.secrets.yaml",
    role: "Secrets/tokens for MCP auth; gitignored.",
  },
];

const TROUBLESHOOTING = [
  {
    issue: "DeepWiki says “Repository Not Indexed”",
    fix: "Wait for DeepWiki indexing to complete, or pick an indexed repo (example: cloudflare/workers-sdk).",
  },
  {
    issue: "No module named 'mcp'",
    fix: "Run via the venv (activate `.venv` or use `.venv/bin/python -m cursor_workflow ...`).",
  },
  {
    issue: "Strict validate fails without live registry",
    fix: "Use `mcp validate` (non-strict) for kit-only installs, or copy `.cursor/mcp.registry.yaml.example` into a live `.cursor/mcp.registry.yaml`.",
  },
];

export default function MCPOnboardingCanvas() {
  return (
    <Stack gap={10}>
      <H1>MCP onboarding (Pattern A)</H1>
      <Text tone="tertiary">
        Canonical portable path for agents + CI: use <Pill>cursor_workflow mcp</Pill> commands.
        Cursor IDE MCP loading is optional. Verified {VERIFIED}.
      </Text>

      <Callout tone="neutral" title="Key idea: CLI is canonical">
        Agents should follow the same “universal” sequence regardless of whether Cursor host MCP
        is loaded: validate → list → call → smoke.
      </Callout>

      <Card>
        <CardHeader>Quick start (kit: agent-colony-mcp)</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Table
              headers={["Step", "Command"]}
              rows={FLOW_COMMANDS.map(([step, cmd]) => [step, cmd])}
            />
            <Text tone="tertiary" size="small">
              Tip: if you see “configured but NOT host-loaded” in <Pill>mcp doctor</Pill>, that’s normal—
              the CLI still works.
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>DeepWiki demo (external: deepwiki)</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              In your current registry snapshot, <Pill>deepwiki</Pill> is mapped to agents:
              {" "}
              <Pill>{REGISTRY_SNAPSHOT.deepwiki.agents.join(", ")}</Pill>.
            </Text>
            <Table
              headers={["Demo step", "Command"]}
              rows={DEEPWIKI_DEMO_COMMANDS.map(([step, cmd]) => [step, cmd])}
            />
            <Text tone="tertiary" size="small">
              Note: DeepWiki tool args use <Pill>repoName</Pill> (not <Pill>repo</Pill>).
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Divider />

      <Card>
        <CardHeader>Where to configure servers</CardHeader>
        <CardBody>
          <Table
            headers={["Path", "Role"]}
            rows={CONFIG_LOCATIONS.map((r) => [r.path, r.role])}
          />
        </CardBody>
      </Card>

      <Divider />

      <Card>
        <CardHeader>Agent usage template (what to tell an agent)</CardHeader>
        <CardBody>
          <Stack gap={6}>
            <Text>
              Use DeepWiki only when the server is mapped to your agent id in{" "}
              <Pill>.cursor/mcp.registry.yaml</Pill>.
            </Text>
            <Text>
              For a typical doc help flow:
            </Text>
            <Text>
              1) call <Pill>read_wiki_structure</Pill> → find relevant section/pages
            </Text>
            <Text>
              2) call <Pill>ask_question</Pill> (or <Pill>read_wiki_contents</Pill>) → extract facts
            </Text>
            <Text tone="tertiary" size="small">
              Output should be: answer + short pointers (wiki topic/page) + caveat if DeepWiki indexing is incomplete.
            </Text>
          </Stack>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>Troubleshooting</CardHeader>
        <CardBody>
          <Table
            headers={["Issue", "Fix"]}
            rows={TROUBLESHOOTING.map((r) => [r.issue, r.fix])}
          />
        </CardBody>
      </Card>
    </Stack>
  );
}

