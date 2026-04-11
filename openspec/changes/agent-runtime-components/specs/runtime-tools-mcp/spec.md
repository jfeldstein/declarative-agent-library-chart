## ADDED Requirements

### Requirement: Tools are implemented as modules

Tool behavior SHALL be implemented in **discrete code modules** (packages or equivalent) with clear entrypoints. Each tool module SHALL be versioned and testable independently of a specific agent deployment.

#### Scenario: Module boundary

- **WHEN** a maintainer adds a new tool
- **THEN** it SHALL be added or referenced as a module (not ad hoc strings inside a single monolithic agent image without a defined module boundary), and its interface SHALL be documented for MCP exposure

### Requirement: Tools are exposed via MCP

The platform SHALL expose enabled tools to agents through **MCP** as **MCP tools** (and MAY expose them as **MCP servers** hosting one or more tools). Agents consume tools through the MCP contract (discovery and invocation) rather than only static in-process registration unless MCP is embedded in-process as an implementation detail.

#### Scenario: Discovery

- **WHEN** an agent runtime connects to an enabled MCP server for a deployment
- **THEN** it SHALL receive a tool list that includes every tool enabled in configuration for that deployment

#### Scenario: Invocation

- **WHEN** the agent invokes a listed MCP tool with valid arguments per that tool’s schema
- **THEN** the corresponding module implementation SHALL execute and return a result suitable for the agent loop

### Requirement: Tool enablement is configuration-driven

Which tools (and MCP servers) are active for a given agent deployment SHALL be determined by **configuration** (for example Helm values). Operators SHALL be able to enable a strict subset of available tools.

#### Scenario: Subset enablement

- **WHEN** values enable only tools **A** and **B** for an agent
- **THEN** the agent SHALL NOT be offered tools **C** or **D** via MCP for that deployment

### Requirement: MCP tool calls expose Prometheus metrics

The agent runtime (or embedded MCP bridge) SHALL register:

- Counter **`agent_runtime_mcp_tool_calls_total`** labeled **`tool`** and **`result`**, where **`tool`** MUST be the **configured tool identifier** for that deployment (finite set from configuration), and **`result`** is **`success`** or **`error`**.
- Histogram **`agent_runtime_mcp_tool_duration_seconds`** labeled **`tool`** and **`result`** with the same semantics.

Implementations SHALL NOT use free-form or user-supplied strings as the **`tool`** label value.

#### Scenario: Tool invocation recorded

- **WHEN** an agent successfully completes an MCP tool call for configured tool **T**
- **THEN** **`agent_runtime_mcp_tool_calls_total{tool="T",result="success"}`** SHALL increase and **`agent_runtime_mcp_tool_duration_seconds`** SHALL record duration for **`tool="T"`**

#### Scenario: Tool error path

- **WHEN** an MCP tool call for tool **T** fails in a way visible to the runtime (for example transport or tool execution error)
- **THEN** **`agent_runtime_mcp_tool_calls_total{tool="T",result="error"}`** SHALL increase
