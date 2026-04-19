## ADDED Requirements

### Requirement: [DALC-REQ-OBS-PLUGIN-WANDB-001] Agent lifecycle integration

The agent runtime SHALL publish **`run.started`** and **`run.ended`** around each LangGraph trigger invocation when executing `run_trigger_graph`, carrying enough context to open or close a Weights & Biases run for that execution (including mandatory tag inputs and `ObservabilitySettings`).

#### Scenario: Run wrapper publishes paired events

- **WHEN** `run_trigger_graph` executes for a `TriggerContext`
- **THEN** it SHALL publish **`run.started`** before graph invoke and **`run.ended`** after invoke completes (including on failure), before resetting trigger id tokens

### Requirement: [DALC-REQ-OBS-PLUGIN-WANDB-002] Tool spans via lifecycle bus

The runtime SHALL include a stable **`tool_call_id`** and measured **`duration_s`** on **`tool.call.completed`** events emitted from MCP tool execution so W&B (and other plugins) can record per-tool latency without duplicating timing logic in multiple modules.

#### Scenario: Tool span keys present for sample tool

- **WHEN** `run_tool_json` completes a tool invocation
- **THEN** the **`tool.call.completed`** payload SHALL include **`tool_call_id`** and **`duration_s`**

### Requirement: [DALC-REQ-OBS-PLUGIN-WANDB-003] Feedback events for late W&B logging

When human feedback is durably recorded from Slack reactions (or similar ingress), the runtime SHALL publish **`feedback.recorded`** with `tool_call_id`, optional `checkpoint_id`, label, source, and settings needed to open a short-lived W&B run for late feedback when W&B is enabled.

#### Scenario: Slack reaction path emits feedback event

- **WHEN** `handle_slack_reaction_event` records correlated human feedback successfully
- **THEN** it SHALL publish **`feedback.recorded`** instead of calling the W&B SDK directly from that module

---

## Notes (relationship to `wandb-agent-traces`)

Requirements related to **checkpoint ↔ W&B linkage**, **mandatory run tags**, and **operator documentation** remain owned by `openspec/changes/agent-checkpointing-wandb-feedback/specs/wandb-agent-traces` and promoted persistence specs. This plugin change covers **where** W&B hooks attach (lifecycle bus) and **Helm value placement** under `observability.plugins.wandb`, without altering checkpoint storage behavior.
