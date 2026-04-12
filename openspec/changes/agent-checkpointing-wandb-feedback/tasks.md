## Implementation order

**Rationale:** Ship **checkpoints** and **W&B tracing + id linkage** first (no Slack dependency). Add **Slack reactions** and **durable feedback + W&B annotation** once correlation keys exist on checkpoints. **Shadow rollouts** are **not** in this change—see `shadow-rollout-evaluation`.

## 1. Checkpointing foundation

- [x] 1.1 Select and configure production checkpointer backend (e.g. Postgres/Redis) and document `thread_id` / `checkpoint_id` usage
- [x] 1.2 Wire LangGraph functional API (or equivalent) so `@entrypoint` receives an injected checkpointer and tasks persist automatically per step
- [x] 1.3 Implement host policy: default-on checkpointing with explicit ephemeral opt-out flag
- [x] 1.4 Expose `get_state` / `get_state_history`-compatible read APIs for operators and internal services
- [ ] 1.5 Persist checkpoints around user-visible external side effects (e.g. Slack post) with `checkpoint_id`, `tool_call_id`, `external_ref` (e.g. Slack channel + `ts`), and timestamp per spec

## 2. W&B automatic tracing and checkpoint linkage

- [ ] 2.1 Enable **automatic** W&B tracing for LLM and tool execution during a run (no separate “export step”) — *run-level `wandb.init`/`finish` per trigger exists; per-LLM/per-tool spans still to wire into LangChain/LangGraph*
- [x] 2.2 Initialize W&B per top-level invocation with the **tag schema** from `wandb-agent-traces` (omit unknown values; do not emit high-cardinality text as tags)
- [x] 2.3 On each checkpoint (or equivalent step boundary), **persist** W&B identifiers needed to annotate that step later (e.g. `wandb_run_id`, span/trace id per SDK)—so resolution **Slack message → tool call → checkpoint → W&B** is possible
- [x] 2.4 Add contract or integration tests (W&B SDK mocked) for tag shape and persisted **checkpoint ↔ W&B** link fields
- [x] 2.5 Keep **`docs/observability.md`** aligned with the **Operator documentation and runtime stubs** requirement in `wandb-agent-traces`; maintain **`hosted_agents.agent_tracing`** and **runtime summary** fields until full W&B/checkpointer wiring lands

## 3. Correlation IDs and Slack feedback

- [x] 3.1 Define stable `tool_call_id`, `run_id`, and `thread_id` propagation through tool execution context
- [ ] 3.2 Add durable store mapping `(slack_channel_id, message_ts)` → `tool_call_id`, `checkpoint_id`, `run_id`, `thread_id`, and W&B ids from §2
- [ ] 3.3 Implement Slack Events subscription for reactions; map configured emoji to **global registry** labels
- [ ] 3.4 On resolved feedback: **durably persist** reaction outcome linked to `tool_call_id` and `checkpoint_id`; **annotate** the corresponding W&B span/run per §2 linkage
- [ ] 3.5 Implement idempotency and conflict policy for duplicate, changed, or removed reactions; reconcile with latest Slack state where feasible
- [ ] 3.6 Orphan reactions: log/queue only—no training-facing label without resolved correlation

## 4. Global label registry (human feedback only)

- [x] 4.1 Implement **single global** versioned label registry and change process; document how new labels ship
- [ ] 4.2 Persist human feedback records with `registry_id`, `schema_version`, global `label_id`, and optional `agent_id` for attribution only

## 5. Rollout and verification

- [x] 5.1 Feature-flag checkpoints, W&B tracing, and Slack ingestion independently for staged enablement
- [ ] 5.2 End-to-end test: tool posts Slack message → mapping written → reaction → feedback in store → W&B annotation on correct span
- [ ] 5.3 End-to-end test: checkpoint resume after injected failure matches LangGraph semantics for completed tasks — *covered partially by thread checkpoint accumulation tests; interrupt/resume not yet implemented*
- [x] 5.4 Runbook: secrets, retention, rollback, and PII review for checkpoints and traces
