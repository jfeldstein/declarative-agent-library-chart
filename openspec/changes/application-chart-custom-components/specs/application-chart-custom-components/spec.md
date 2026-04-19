## ADDED Requirements

### Requirement: [DALC-REQ-APP-CUSTOM-001] Application charts document custom runtime packaging

An application chart that depends on **`declarative-agent-library-chart`** and ships **custom Python** for tools, triggers-side integrations, or scrapers SHALL document in its **`README.md`** how that code is **built into the container image** (or, for non-production demos only, mounted read-only), how it relates to the **library runtime image**, and which **values** keys (`agent.image`, `agent.extraEnv`, etc.) operators must set.

#### Scenario: Operator understands image responsibility

- **WHEN** a reader opens **`examples/with_custom_components/README.md`**
- **THEN** the document SHALL state that **custom code is part of the application image** (or explicitly describe the dev-only mount pattern) and SHALL reference the **`agent:`** dependency alias for library tunables

### Requirement: [DALC-REQ-APP-CUSTOM-002] Custom MCP-style tools register through the shared dispatch contract

The runtime SHALL provide a **documented initialization mechanism** (for example an environment variable naming an importable module executed at startup) that allows an application image to **register additional MCP tool ids** such that **`invoke_tool`** and the LangChain MCP binding layer treat them like built-in ids **without** modifying library source in the forked repository.

Custom tool ids SHALL remain subject to existing **allowlist** semantics (`mcp.enabledTools` / **`HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON`**) and skill-unlock behavior unchanged elsewhere.

#### Scenario: Allowlisted custom tool invokes successfully

- **WHEN** a deployment supplies a valid custom registration module, sets **`mcp.enabledTools`** (or equivalent env) to include a **registered** custom tool id, and invokes **`POST /api/v1/trigger`** with **`tool`** / **`tool_arguments`**
- **THEN** the runtime SHALL dispatch to the **custom implementation** and SHALL NOT treat the id as unknown solely because it is not shipped in the default library tree

### Requirement: [DALC-REQ-APP-CUSTOM-003] Custom inbound automation uses application-owned Kubernetes resources

Application charts that require **inbound paths not covered** by the library’s first-class Slack/Jira triggers SHALL document **application-owned** workloads (for example an extra **Deployment** or **CronJob** in the parent chart) that forward to **`/api/v1/trigger`** or otherwise compose with the agent Service using **stable HTTP contracts**, rather than requiring undocumented patches inside **`declarative-agent-library-chart`** templates.

#### Scenario: Example describes trigger composition

- **WHEN** **`examples/with_custom_components/README.md`** explains trigger extension
- **THEN** it SHALL describe **parent-chart-owned** resources or **`extraEnv`** composition and SHALL reference the **`POST /api/v1/trigger`** contract as the integration boundary

### Requirement: [DALC-REQ-APP-CUSTOM-004] Custom scrapers reuse RAG embed conventions

A custom scraper batch job packaged by an application chart SHALL use the **same RAG base URL wiring** as library scrapers (**`RAG_SERVICE_URL`** resolved consistently with the dependency’s internal RAG URL) when posting to **`/v1/embed`**, and SHOULD reuse **`hosted_agents.scrapers.base`** helpers where embeddings are produced so metrics and HTTP behavior stay consistent.

#### Scenario: Example scraper documents RAG env

- **WHEN** **`examples/with_custom_components`** includes a scraper **CronJob** manifest or Helm template for a custom module
- **THEN** the example README SHALL call out **`RAG_SERVICE_URL`** (or the chart helper that sets it) as **required** for embed ingestion

### Requirement: [DALC-REQ-APP-CUSTOM-005] Reference example `with_custom_components` exists

The repository SHALL include **`examples/with_custom_components/`** as an **application chart** that depends on **`declarative-agent-library-chart`** with **`alias: agent`**, includes **`templates/agent.yaml`** using **`declarative-agent.system`**, and demonstrates **at least one** custom tool registration path consistent with **[DALC-REQ-APP-CUSTOM-002]**, plus documented stubs or manifests for **trigger composition** **[DALC-REQ-APP-CUSTOM-003]** and **custom scraper** **[DALC-REQ-APP-CUSTOM-004]**.

#### Scenario: Example chart is structurally consistent with other examples

- **WHEN** a maintainer inspects **`examples/with_custom_components/Chart.yaml`**
- **THEN** it SHALL declare **`type: application`**, declare the **file://** dependency on **`../../helm/chart`**, and SHALL use **`alias: agent`** matching **[DALC-REQ-DALC-PKG-002]** in **`openspec/specs/dalc-library-chart-packaging/spec.md`**
