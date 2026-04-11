## ADDED Requirements

### Requirement: Subagents are declared in values

The platform SHALL support **one or more subagent definitions** in deployment configuration (for example Helm values). Each subagent SHALL include at minimum:

- A **system prompt** (or equivalent instruction block) for that subagent.
- **References or flags** for which **scrapers**, **tools**, and **skills** (if applicable) apply to that subagent’s context, consistent with the main agent’s configuration model.

Additional fields (model name, temperature, max tokens, labels) MAY be supported but are not mandated by this spec except where needed to satisfy orchestration behavior below.

#### Scenario: Multiple subagents in one deployment

- **WHEN** values define subagents **S1** and **S2** with distinct system prompts and capability sets
- **THEN** the runtime SHALL materialize two distinct subagent configurations that do not share per-invocation conversation state with each other

### Requirement: Orchestration follows the subagent pattern

The **main agent** (supervisor) SHALL invoke each subagent through a **tool-like interface** (subagent-as-tool). Subagents SHALL be **stateless across invocations** with respect to conversation memory: **the main agent** retains cross-turn memory unless a future spec extends this capability.

#### Scenario: Supervisor delegates

- **WHEN** the main agent selects a subagent for a task and passes an input payload
- **THEN** the subagent SHALL run with a **fresh context** for that invocation, return a result to the main agent, and SHALL NOT require the end user to converse directly with the subagent

#### Scenario: Parallel invocations

- **WHEN** the main agent’s plan requires results from more than one subagent
- **THEN** the runtime MAY execute those subagent invocations in parallel if safe for the configured tools and integrations

### Requirement: Subagent orchestration exposes Prometheus metrics

The agent runtime SHALL register:

- Counter **`agent_runtime_subagent_invocations_total`** labeled **`subagent`** and **`result`**, where **`subagent`** MUST be the **configured subagent identifier** from values (finite set per deployment), and **`result`** is **`success`** or **`error`**.
- Histogram **`agent_runtime_subagent_duration_seconds`** labeled **`subagent`** and **`result`** with the same semantics.

Implementations SHALL NOT use dynamic or user-defined strings as **`subagent`** label values.

#### Scenario: Delegation success

- **WHEN** the supervisor completes a subagent invocation for configured subagent **S** and receives a successful result
- **THEN** **`agent_runtime_subagent_invocations_total{subagent="S",result="success"}`** SHALL increase

#### Scenario: Delegation failure

- **WHEN** a subagent invocation for **S** fails in a way the runtime surfaces to the supervisor
- **THEN** **`agent_runtime_subagent_invocations_total{subagent="S",result="error"}`** SHALL increase
