## ADDED Requirements

### Requirement: [DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-001] Enabled MCP tools use structured LangChain parameters for covered tool ids

For each in-process MCP tool identifier listed in **`REGISTERED_MCP_TOOL_IDS`** and enabled for the deployment (together with skill-unlocked tools), except **`sample.echo`** which already uses explicit parameters, the supervisor **SHALL** expose a LangChain **`@tool`** (or equivalent structured tool) whose **parameters are explicit typed fields** matching the argument contract consumed by **`invoke_tool`** for that identifier. Implementations **SHALL NOT** rely on a single opaque **`arguments_json`** string as the **only** way for the model to supply arguments for those identifiers.

#### Scenario: Slack post tool has structured parameters

- **WHEN** **`slack.post_message`** is enabled for the deployment and exposed to the agent loop
- **THEN** the LangChain tool definition **SHALL** accept documented fields (for example channel id, text, and optional thread identifiers) as **named parameters**, not solely as a serialized JSON blob string

#### Scenario: Jira search tool has structured parameters

- **WHEN** **`jira.search_issues`** is enabled for the deployment and exposed to the agent loop
- **THEN** the LangChain tool definition **SHALL** accept documented search parameters (for example JQL and caps) as **named parameters**, not solely as a serialized JSON blob string

### Requirement: [DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-002] Tool behavior shares one implementation path with invoke_tool

For each MCP tool identifier migrated under **[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-001]**, the Python implementation that performs Slack Web API or Jira REST work **SHALL** be reachable through **`invoke_tool`** (directly or via a thin wrapper that **`invoke_tool`** calls) so that programmatic callers and LangChain wrappers do not duplicate business logic.

#### Scenario: Dispatch and LangChain agree on semantics

- **WHEN** a test or caller invokes **`invoke_tool`** with a valid argument dict for an migrated identifier
- **AND** the agent loop invokes the corresponding structured LangChain tool with equivalent arguments
- **THEN** both paths **SHALL** exercise the same underlying implementation behavior (same validation and external API effects modulo serialization of return values for the agent UI)

### Requirement: [DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-003] Generic JSON-string MCP wrapper is not used for migrated ids

For MCP tool identifiers covered by **[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-001]**, the supervisor **SHALL NOT** register the legacy generic **`arguments_json`** LangChain tool implementation for those identifiers.

#### Scenario: No generic wrapper for migrated Slack tools

- **WHEN** the runtime builds supervisor tools for a deployment that enables **`slack.reactions_add`**
- **THEN** the registered LangChain tool for that identifier **SHALL NOT** be the generic **“pass all args as one JSON string”** helper used for unmigrated placeholders
