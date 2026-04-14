## ADDED Requirements

### Requirement: Trigger invokes only the root agent

Every **`POST /api/v1/trigger`** SHALL invoke **exactly one** top-level **main agent** whose **system instructions** come from deployment **root** configuration (e.g. Helm **`systemPrompt`** → `HOSTED_AGENT_SYSTEM_PROMPT`), not from a selected subagent entry. The HTTP request SHALL **not** accept a **`subagent`** field (or any field with the same meaning) to bypass or replace that main agent.

#### Scenario: Request without subagent field

- **WHEN** a client sends a valid trigger request with a user message field (per implementation) and **does not** include `subagent`
- **THEN** the main agent runs and MAY call zero or more subagent tools before producing the trigger HTTP response

#### Scenario: subagent field rejected or absent

- **WHEN** a client sends `subagent` in the JSON body (legacy)
- **THEN** the server responds with **400** (rejected) or the field is **stripped by schema** such that it has no effect—behavior MUST be documented; preference is **schema omission + validation error** for clarity

### Requirement: Subagents exposed only as tools to the main agent

Configured subagents SHALL **not** be directly invokable as separate HTTP routes. They SHALL be exposed to the **main agent** as **LangChain tools** (one tool per subagent or an equivalent single-dispatch tool documented in design) following the **subagents** supervisor pattern described in LangChain documentation.

#### Scenario: Main agent delegates via tool

- **WHEN** the main agent’s model issues a tool call targeting a configured subagent
- **THEN** the corresponding subagent unit executes and returns a string result to the main agent, which continues orchestration until a final user-visible response is produced

### Requirement: No dedicated router node

The compiled orchestration graph SHALL **not** include a **router** node whose sole responsibility is to classify or dispatch requests to subagents **before** the main agent runs. **Dispatch** to subagents is performed **only** through **main-agent tool calls**.

#### Scenario: Graph entry

- **WHEN** a trigger run starts
- **THEN** the first orchestration step is **main agent** reasoning (or a single wrapper node that invokes that agent), not a separate routing classifier node

### Requirement: Documented operator contract

Documentation SHALL state that **root `systemPrompt`** defines the **supervisor**, **`subagents`** define **tools** (with **name** / **description** for tool schema), and **no HTTP subagent selector** exists on trigger.

#### Scenario: README

- **WHEN** an operator reads the CFHA README for multi-agent behavior
- **THEN** they understand that subagents are **tools** of the root agent and align with LangChain’s subagents pattern (link to official docs)
