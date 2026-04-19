## Why

Supervisor MCP tools are mostly wrapped as a single LangChain tool per id that accepts **`arguments_json`**, which forces models to pack arguments into a string and duplicates no real business logic—the real behavior already lives in **`invoke_tool`** and **`tools_impl`**. Refactoring to **shared handler entrypoints** plus **typed `@tool` wrappers** improves agent ergonomics, keeps **one implementation path** for Slack/Jira (and scrapers that import the same functions), and removes unnecessary indirection without changing wire-level tool ids or Helm allowlisting.

## What Changes

- Introduce **pure or thin handler entrypoints** (per tool id or per domain module) that **`invoke_tool`** and LangChain **`@tool`** wrappers both call, so dispatch stays centralized and tests can target handlers directly.
- Replace the **generic `arguments_json` MCP LangChain wrapper** with **typed** LangChain tools (explicit parameters matching the existing argument dict contracts) for **Slack** and **Jira** tools currently covered by `REGISTERED_MCP_TOOL_IDS`, plus keep **`sample.echo`** as the existing typed pattern.
- Leave **`run_tool_json`** as the shared choke point for **allowlisting**, **metrics**, **trajectory**, and related observability (wrappers call into it or share its inner invoke path—design detail).
- **No** change to HTTP trigger behavior required for this refactor (user scope: non-goal); **no** change to configured tool identifiers or Helm **`mcp.enabledTools`** semantics.

## Capabilities

### New Capabilities

- `typed-langchain-tool-bindings`: Normative expectations for how enabled in-process MCP tool ids are exposed to the supervisor/agent loop (structured LangChain tools tied to existing `invoke_tool` contracts and shared handlers).

### Modified Capabilities

- _(none)_ — Existing **`dalc-slack-tools`** and **`dalc-jira-tools`** requirements already describe external API behavior and credentials; this change refines **agent-facing binding shape** without altering those REST semantics. If promotion workflow later merges **`runtime-tools-mcp`** from **`agent-runtime-components`**, this change’s new capability aligns with its “schema sufficient for invocation” intent without editing unpublished deltas here.

## Impact

- **Code**: `helm/src/hosted_agents/supervisor.py` (`_make_mcp_tool`, `_build_mcp_langchain_tools`), `helm/src/hosted_agents/tools_impl/dispatch.py`, `helm/src/hosted_agents/tools_impl/jira/*`, Slack tool modules; tests under `helm/src/tests/` (supervisor/tool dispatch, contract tests if tool surfaces change).
- **Dependencies**: Existing LangChain `@tool` / structured tool usage; no new runtime dependency expected unless typing utilities are added.
- **Operators**: No breaking change to **`mcp.enabledTools`** or env **`HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON`**; optional doc touch in `tools_impl/README.md` describing typed LangChain parameters.
