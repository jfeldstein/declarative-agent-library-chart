## MODIFIED Requirements

### Requirement: Tools are implemented as modules

Tool behavior SHALL be implemented in **discrete code modules** (packages or equivalent) with clear entrypoints. Each tool module SHALL be versioned and testable independently of a specific agent deployment.

#### Scenario: Module boundary

- **WHEN** a maintainer adds a new tool
- **THEN** it SHALL be added or referenced as a module (not ad hoc strings inside a single monolithic agent image without a defined module boundary), and its interface SHALL be documented for **agent consumption** (for example **MCP tool schema** and/or **LangGraph tool** binding)

### Requirement: Tools are exposed for agent use

The platform SHALL make **enabled tools** available to the **agent runtime** (for example **LangGraph**) such that the runtime can **discover** which tools exist for the deployment and **invoke** them with arguments that conform to each tool’s schema. **MCP** defines a **reference contract** for discovery and invocation (tool list, schemas, call/result shapes); implementations **MAY** satisfy this obligation using **MCP over the network**, **in-process MCP-compatible adapters**, or **LangGraph-native tool registration**, provided the **configuration-driven enablement** and **observability** requirements in this capability are met. Implementations **SHALL NOT** require a separate MCP server **process** solely for conformance when an equivalent in-process binding meets the same semantics.

#### Scenario: Discovery

- **WHEN** an agent runtime starts for a deployment with enabled tools per configuration
- **THEN** it SHALL obtain a tool list that includes **every** tool enabled in configuration for that deployment, with schemas or descriptions sufficient for the agent loop to invoke them correctly

#### Scenario: Invocation

- **WHEN** the agent invokes a listed tool with valid arguments per that tool’s schema
- **THEN** the corresponding module implementation SHALL execute and return a result suitable for the agent loop

### Requirement: Tool enablement is configuration-driven

Which tools (and any **MCP server endpoints**, when used) are active for a given agent deployment SHALL be determined by **configuration** (for example Helm values). Operators SHALL be able to enable a strict subset of available tools.

#### Scenario: Subset enablement

- **WHEN** values enable only tools **A** and **B** for an agent
- **THEN** the agent runtime SHALL NOT offer tools **C** or **D** for that deployment

### Requirement: Tool invocations expose Prometheus metrics

The agent runtime (including any **MCP bridge** or **LangGraph tool** wrapper) SHALL register:

- Counter **`agent_runtime_mcp_tool_calls_total`** labeled **`tool`** and **`result`**, where **`tool`** MUST be the **configured tool identifier** for that deployment (finite set from configuration), and **`result`** is **`success`** or **`error`**.
- Histogram **`agent_runtime_mcp_tool_duration_seconds`** labeled **`tool`** and **`result`** with the same semantics.

Implementations SHALL NOT use free-form or user-supplied strings as the **`tool`** label value. **Metric names** remain as specified for **compatibility** with existing dashboards; they denote **tool invocations** whether or not a wire MCP transport is used.

#### Scenario: Tool invocation recorded

- **WHEN** an agent successfully completes a **configured tool invocation** for tool **T**
- **THEN** **`agent_runtime_mcp_tool_calls_total{tool="T",result="success"}`** SHALL increase and **`agent_runtime_mcp_tool_duration_seconds`** SHALL record duration for **`tool="T"`**

#### Scenario: Tool error path

- **WHEN** a **tool invocation** for tool **T** fails in a way visible to the runtime (for example transport, adapter, or tool execution error)
- **THEN** **`agent_runtime_mcp_tool_calls_total{tool="T",result="error"}`** SHALL increase
