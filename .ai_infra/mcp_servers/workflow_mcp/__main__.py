"""
File: __main__.py
Path: .ai_infra/mcp_servers/workflow_mcp/__main__.py
Role: Entrypoint for stdio MCP server.
Used By:
 - Cursor .cursor/mcp.json
Depends On:
 - workflow_mcp/server.py
Notes:
 - mcp.run() defaults to transport="stdio" (unchanged in SDK v2).
"""

from workflow_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
