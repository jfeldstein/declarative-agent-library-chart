## Why

Hosted agents need durable, inspectable runs so we can resume work, audit decisions, and correlate human approval with specific tool outcomes. Tying Slack reactions to the right tool calls, persisting that feedback durably, and seeing the same story in Weights & Biases requires a single spine: **the checkpointer is the source of truth for each step**, with **automatic** persistence aligned with [LangGraph’s functional API checkpoint model](https://docs.langchain.com/oss/python/langgraph/use-functional-api#manage-checkpoints), **automatic W&B tracing** as LLM and tool work happens, and **server-side** correlation from Slack message identity to tool call and checkpoint (Slack does not support hidden metadata on posts).

## What Changes

- Adopt **automatic checkpointing** for agent runs (functional API–style entrypoints/tasks or equivalent), so every step is persisted without requiring authors to manually save state; expose **thread state** and **checkpoint history** consistent with LangGraph’s `get_state` / `get_state_history` semantics where applicable.
- **Weights & Biases**: traces are emitted **automatically** during runs (e.g. as LLMs and tools execute). Runs use a **fixed tag schema** where useful for slicing. Each checkpoint step **SHALL** be linkable to the corresponding W&B run/span identifiers so that **late human feedback** (after a reaction webhook) can **update durable storage** and **annotate the correct W&B trace** (resolution chain: Slack message id → tool call → checkpoint → W&B span/trace).
- Introduce a **feedback channel abstraction** (first implementation: **Slack reactions** such as 👍/👎) that binds **scalar or registry-mapped feedback** to **tool calls** and **checkpoints**. **Reaction receipt** is **durably stored** and linked to the correlated tool call (and checkpoint when resolved). Correlation uses a **durable server-side mapping** `(channel_id, message_ts)` → run identifiers, not reliance on hidden Slack payload fields.
- Define a **versioned, global label registry** for human-judgment labels used when persisting explicit feedback from channels like Slack. **v1 scope** is **explicit human feedback only** (no separate operational-signal taxonomy or opt-in mappers in this change).

## Capabilities

### New Capabilities

- `runtime-langgraph-checkpoints`: Automatic persistence and inspection of agent runs (checkpoint after tasks/steps), thread identifiers, optional checkpoint listing/history API aligned with LangGraph functional API patterns; checkpoint records support binding external refs and W&B trace linkage fields per specs.
- `agent-feedback-model`: **Global-only**, versioned taxonomy for **explicit human** judgment labels (e.g. emoji → label id / scalar).
- `tool-feedback-slack`: Ingest Slack reactions; map to registry labels; server-side correlation to `tool_call_id` / `checkpoint_id`; idempotency and orphan handling.
- `wandb-agent-traces`: W&B run/span model for agents; mandatory tags where specified; automatic tracing during execution; **persisted links** from checkpoints/tool steps to W&B identifiers for feedback annotation.

### Deferred to Another Change

- **Shadow rollouts** (variant runs, `rollout_arm`, non-mutating shadow path, comparison telemetry): see **`shadow-rollout-evaluation`**.

### Modified Capabilities

- *(none — no existing `openspec/specs/` capability covers this combination today.)*

## Impact

- **Supersedes** removed change `agent-feedback-wandb-integration`: unique requirements were merged into this tree (2026-04-11); **ATIF export** and **positive-subsequence dataset mining** were **removed** from scope (2026-04-12)—training pipelines can consume W&B and/or checkpoint-backed APIs instead.
- **Shadow rollout** requirements **moved** to **`openspec/changes/shadow-rollout-evaluation`** (2026-04-12).
- **Runtime / agent host**: checkpoint store selection, LangGraph or compatible checkpointer wiring, correlation IDs on tool invocations, W&B trace id persistence on steps.
- **Integrations**: Slack Events API (or Bolt) for reactions; `wandb` SDK for traces and feedback enrichment.
- **Ops**: secrets for Slack and W&B; retention and PII policies for checkpoints and traces.
