# User MCP drop-in pattern

Copy `user.example.json` to a named fragment (e.g. `slack.json`) and link with:

```bash
agent-colony mcp link --name slack --file .cursor/mcp.d/slack.json
```

Fragments must contain a top-level `mcpServers` object with one or more server entries.
