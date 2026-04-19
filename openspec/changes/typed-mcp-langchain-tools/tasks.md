## 1. Handler extraction

- [x] 1.1 Audit `hosted_agents.tools_impl.dispatch.invoke_tool` and Slack/Jira modules; list each **`REGISTERED_MCP_TOOL_IDS`** branch and its argument dict shape (keys, optional fields).
- [x] 1.2 Introduce shared **`run_*`** or module-level callables that **`invoke_tool`** delegates to for each migrated id, preserving return **`dict[str, Any]`** shapes used today.
- [x] 1.3 Add or extend unit tests calling **`invoke_tool`** for each migrated id (regression safety).

## 2. Typed LangChain tools

- [x] 2.1 Implement typed **`@tool`** (or structured tool) factories per migrated MCP id, mapping named parameters → the same dict **`invoke_tool`** expects; route execution through **`run_tool_json`** (or equivalent) so allowlist and observability stay centralized.
- [x] 2.2 Update **`supervisor._make_mcp_tool`** / **`_build_mcp_langchain_tools`** to register typed tools for all migrated ids; remove **`generic_mcp_tool`** for those ids; keep **`sample.echo`** behavior.
- [x] 2.3 Add a guard test: every id in **`REGISTERED_MCP_TOOL_IDS`** has either an explicit typed registration or **`sample.echo`**—no silent generic wrapper for migrated set.

## 3. Documentation and traceability

- [x] 3.1 Update **`helm/src/hosted_agents/tools_impl/README.md`** (if needed) to describe structured LangChain parameters vs **`invoke_tool`** dicts.
- [x] 3.2 When promoting **`typed-langchain-tool-bindings`** to **`openspec/specs/`**, add requirement IDs to pytest/Helm evidence per **`dalc-requirement-verification`** and **`docs/spec-test-traceability.md`** (defer here if this change stays pre-promotion only).

## 4. Verification

- [x] 4.1 Run **`uv run pytest`** (or project-standard) for **`helm/src/tests`** covering supervisor, **`test_tool_dispatch`**, Slack/Jira tool tests, and chart contract tests.
- [x] 4.2 Run **`python3 scripts/check_spec_traceability.py`** if any **`openspec/specs/`** files are touched in the implementation PR.
