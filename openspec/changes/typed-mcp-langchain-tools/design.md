## Context

Today the supervisor builds LangChain tools for enabled MCP ids by sorting ids and calling `_make_mcp_tool`. **`sample.echo`** uses a typed function; **all other** MCP tools use **`generic_mcp_tool(arguments_json: str)`**, which parses JSON and forwards to **`run_tool_json`** → **`invoke_tool`**. Implementations live in **`tools_impl`** with **`invoke_tool`** as the string-dispatch entry. Scrapers and future callers may want **direct Python calls** without LangChain; those should reuse the **same** core logic without duplicating Slack/Jira clients.

Constraints: preserve **`mcp.enabledTools`** / **`HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON`** identifiers; preserve **`REGISTERED_MCP_TOOL_IDS`** as the chart contract set; preserve **`run_tool_json`** semantics for allowlisting (**`enabled_mcp_tools ∪ unlocked_tools`**), Prometheus counters/histograms, trajectory, and span summaries.

## Goals / Non-Goals

**Goals:**

- Factor **shared entrypoints** (per tool id or small grouped modules) such that **`invoke_tool`** and typed LangChain **`@tool`** wrappers both exercise the **same** code path after arguments are validated/normalized.
- Replace the **generic `arguments_json` wrapper** for **Slack** and **Jira** tools (the ids in **`REGISTERED_MCP_TOOL_IDS`** excluding **`sample.echo`**, which stays typed as today) with **explicit parameters** on LangChain tools so model-facing schemas match the dict contracts **`invoke_tool`** already expects.
- Keep **`dispatch.invoke_tool`** as the **single string-id dispatch** for HTTP-less programmatic use (tests, optional scraper reuse via **`invoke_tool`** or thinner **`run_*`** helpers).

**Non-Goals:**

- Changing REST/Jira/Slack **external** semantics required by **`dalc-slack-tools`** / **`dalc-jira-tools`** (those specs remain the source of truth for API behavior).
- Removing **`invoke_tool`** or the **Helm allowlist** model.
- Introducing a network MCP server or changing **metrics** names/labels.
- Refactoring **subagent** `@tool` construction (only **MCP-style** ids under **`_make_mcp_tool`**).

## Decisions

1. **Shared logic location**  
   **Decision:** Move or expose **thin** functions **`run_<tool_id>`** or domain **`handlers.run_*`** that take **`(arguments: dict[str, Any])`** or typed kwargs and return **`dict[str, Any]`**, called from **`invoke_tool`** branches and from LangChain wrappers that map typed parameters → the same dict **`invoke_tool`** would accept.  
   **Rationale:** Minimizes drift; **`invoke_tool`** stays the registry; LangChain only changes how arguments are collected.  
   **Alternative considered:** LangChain tools call **`invoke_tool(tool_id, built_dict)`** only—simpler but keeps less clarity on per-tool typing at the Python layer; still acceptable if wrappers build dicts explicitly.

2. **Typed LangChain signature shape**  
   **Decision:** One **`@tool`** per MCP id with parameters mirroring the **documented** argument keys (required vs optional with defaults consistent with **`tools_impl`**). Return value remains **`str`** by JSON-serializing the existing result envelope if that is what **`run_tool_json`** returns today—or match current **`run_tool_json`** contract exactly.  
   **Rationale:** Maximizes model usability; avoids “JSON in a string” anti-pattern.  
   **Alternative:** Keep generic wrapper for tools with unstable schemas—**rejected** for Slack/Jira set in scope.

3. **Where registration happens**  
   **Decision:** **`_make_mcp_tool`** becomes a **dispatcher**: for ids with typed bindings, return the dedicated function; **`sample.echo`** unchanged; no fallback **`generic_mcp_tool`** for ids in **`REGISTERED_MCP_TOOL_IDS`** once migrated.  
   **Rationale:** Explicit failure if a **new** id is added to Helm but not wired in supervisor.  
   **Mitigation:** Contract test or unit test that **`REGISTERED_MCP_TOOL_IDS`** ⊆ union of **`sample.echo`** + explicitly registered typed ids.

4. **Scrapers**  
   **Decision:** Document that scrapers **SHOULD** call **`invoke_tool`** or extracted **`run_*`** helpers instead of duplicating SDK calls; optional follow-up PR to replace inline calls—**not** required to complete this change if scrapers already isolate calls.

## Risks / Trade-offs

- **[Risk]** Parameter names in LangChain tools drift from **`invoke_tool`** dict keys → **Mitigation:** single mapping table or shared TypedDict/dataclass per tool id; tests that invoke both paths with equivalent payloads.
- **[Risk]** Larger **`supervisor.py`** if every tool is inlined → **Mitigation:** generate or place typed wrappers in **`tools_impl/langchain/`** (or adjacent module) importing **`run_tool_json`** / **`invoke_tool`**.
- **[Trade-off]** Maintenance: adding a tool now requires **dispatch**, **REGISTERED_MCP_TOOL_IDS**, **typed wrapper**, and possibly **schema** docs—acceptable for bounded tool count.

## Migration Plan

1. Implement shared handlers + typed wrappers behind the same **`run_tool_json`** gate.  
2. Deploy; no Helm value migration. Rollback: revert supervisor to generic wrapper (keep handler extraction on branch if needed).

## Open Questions

- Whether to return **raw dict** vs **JSON string** from LangChain tools to match **`sample.echo`** pattern—follow **`run_tool_json`** output string contract for consistency with today’s agent messages.
- Exact module split (**`hosted_agents.tools_impl.langchain_tools`** vs colocated)—resolve during implementation for import cycles.
