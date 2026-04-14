# In-process tools (`tools_impl`)

This package holds **reference tool implementations** invoked through **`POST /api/v1/trigger`** with JSON `{"tool":"<id>","tool_arguments":{…}}` when the tool id is allowlisted via Helm values (`mcp.enabledTools`) or unlocked by a loaded skill (`skills[].extraTools` via `{"load_skill":"<name>"}` on the same endpoint).

| Tool id | Module | Notes |
|---------|--------|-------|
| `sample.echo` | `sample_echo.py` | Returns `{"echo": "<message>"}` |

To add a tool:

1. Implement `run(arguments: dict) -> dict` in a new module.
2. Register the id in `hosted_agents/tools_impl/dispatch.py`.
3. Document the id in this table and allowlist it in chart values for deployments that need it.

For a **stdio MCP server** that mirrors these tools for external agent hosts, generate a thin wrapper (future work) that delegates to the same functions.
