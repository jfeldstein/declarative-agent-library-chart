## ADDED Requirements

### Requirement: Skills support progressive disclosure

The platform SHALL support **named skills** that provide **specialized prompts and optional supplementary context** without loading all skill content into the default system prompt. Agents SHALL be able to **discover** available skills (for example via a catalog in configuration or a small fixed list in a loader tool description) and **load** a chosen skill on demand.

This pattern SHALL align with the **skills** architecture described in LangChain documentation ([Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)): progressive disclosure of domain knowledge and prompts.

#### Scenario: On-demand load

- **WHEN** the agent decides a task matches a named skill **K** and triggers the skill load mechanism
- **THEN** the runtime SHALL inject **K**’s specialized prompt (and any skill-local context defined for **K**) into the active context for subsequent reasoning steps in that conversation turn or session according to implementation rules

### Requirement: Skills are configuration-addressable

Skill definitions (name, prompt content or path, optional tool bindings) SHALL be declared in **configuration** so operators can add or remove skills without rebuilding unrelated components, subject to packaging constraints for prompt files or modules.

#### Scenario: Enable a skill catalog entry

- **WHEN** values include a skill **K** with valid references to its prompt source
- **THEN** the agent SHALL be able to load **K** through the documented load mechanism at runtime

### Requirement: Skill load operations expose Prometheus metrics

The agent runtime SHALL register:

- Counter **`agent_runtime_skill_loads_total`** labeled **`skill`** and **`result`**, where **`skill`** MUST be the **configured skill name** from the catalog (finite set per deployment), and **`result`** is **`success`** or **`error`**.
- Histogram **`agent_runtime_skill_load_duration_seconds`** labeled **`skill`** and **`result`** with the same semantics.

Implementations SHALL NOT use unbounded skill identifiers as label values.

#### Scenario: Successful load

- **WHEN** the agent successfully loads skill **K** via the documented mechanism
- **THEN** **`agent_runtime_skill_loads_total{skill="K",result="success"}`** SHALL increase and **`agent_runtime_skill_load_duration_seconds`** SHALL record the load duration for **`skill="K"`**

#### Scenario: Failed load

- **WHEN** loading skill **K** fails (for example missing prompt source or validation error)
- **THEN** **`agent_runtime_skill_loads_total{skill="K",result="error"}`** SHALL increase
