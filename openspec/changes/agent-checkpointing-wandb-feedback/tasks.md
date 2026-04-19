## 1. Checkpointing foundation

- [x] 1.1 Select and configure **production** checkpointer backends (**Postgres** / **Redis** savers) and document **`thread_id` / `checkpoint_id`**. *(**Done:** Postgres LangGraph saver via **`HOSTED_AGENT_CHECKPOINT_BACKEND=postgres`** + **`HOSTED_AGENT_POSTGRES_URL`** (`build_checkpointer`); identifiers documented in **`docs/runbook-checkpointing-wandb.md`**. **Deferred:** Redis saver not pinned—**`build_checkpointer`** still rejects **`redis`** until a supported Redis implementation exists.)*
- [x] 1.2 Wire persistence via **`StateGraph` + `compile(checkpointer=…)`** + **`graph.invoke`** (**`trigger_graph.py`**). *(**Done:** compiled graph uses checkpointer when enabled; LangGraph **`@entrypoint` / `@task`** API intentionally not used.)*
- [x] 1.3 Implement host policy: default-on checkpointing with explicit ephemeral opt-out flag
- [x] 1.4 Expose `get_state` / `get_state_history`-compatible read APIs for operators and internal services
- [x] 1.5 Persist checkpoints around user-visible external side effects (e.g. Slack post) with `checkpoint_id`, `tool_call_id`, `external_ref`, timestamp per spec

## 2. Correlation and Slack feedback

- [x] 2.1 Define stable `tool_call_id`, `run_id`, and `thread_id` propagation through tool execution context
- [x] 2.2 Add **durable** (survives restarts / multi-replica) store mapping **`(slack_channel_id, message_ts)`** → tool/run/**`checkpoint_id`**. *(**Done:** **`PostgresCorrelationStore`** when **`HOSTED_AGENT_OBSERVABILITY_STORE=postgres`** + **`HOSTED_AGENT_POSTGRES_URL`**; in-memory **`CorrelationStore`** remains the default for single-process dev.)*
- [x] 2.3 Implement Slack Events subscription for reactions; map configured emoji to **global registry** labels (positive / negative / neutral per policy)
- [ ] 2.4 Implement idempotency and conflict policy for duplicate, changed, or removed reactions; reconcile with latest Slack state where feasible. *(**Deferred:** ingest uses **`dedupe_key`** upsert (“latest wins”) only; no reaction removal reconciliation or Slack API poll loop in this codebase.)*
- [x] 2.5 Orphan reactions: log/queue only—no training-eligible label without resolved correlation

## 3. Weights & Biases integration

- [x] 3.1 Initialize W&B per top-level run with **fully populated** mandatory tag schema (`agent_id`, `environment`, `skill_id`, `skill_version`, `model_id`, `prompt_hash`, `rollout_arm`, `thread_id`). *(**Done:** `wandb_mandatory_tags_for_run` resolves tags from env + trigger body (`load_skill` / `tool`) + `HOSTED_AGENT_ROLLOUT_ARM`; late Slack feedback uses the same resolver for **thread_id** + env.)*
- [x] 3.2 Emit hierarchical telemetry: tool calls as child spans (or equivalent) including `tool_call_id` and timing
- [x] 3.3 On feedback ingestion, update W&B trace/span or keyed metrics so feedback is queryable by `tool_call_id` and `checkpoint_id` (`feedback_label`, `feedback_source`)
- [x] 3.4 Add integration tests or **contract** tests against the real **W&B SDK** shape (or high-fidelity stub), not only ad-hoc mock objects. *(**Done:** `tests/test_wandb_sdk_contract.py` + reaction E2E with mocked **`wandb`** module.)*
- [x] 3.5 Support **late** feedback after span close; enforce tag cardinality limits and hash/omit sensitive tag values

## 4. Canonical trajectory and ATIF

- [x] 4.1 Implement in-memory/streaming CanonicalTrajectory builder fed by checkpoints and tool results
- [x] 4.2 Pin ATIF schema version and implement exporter from CanonicalTrajectory to ATIF JSON
- [x] 4.3 [REMOVED]
- [x] 4.4 Implement configurable **redaction** before export; document rules for messages, tool args, and Slack identifiers

## 5. Shadow rollouts

- [x] 5.1 Add configuration for shadow variants (skill version, model, prompt hash) and `request_correlation_id` linking to primary
- [x] 5.2 [REMOVED]
- [x] 5.3 [REMOVED]
- [x] 5.4 [REMOVED]

## 6. Rollout and verification

- [x] 6.1 Feature-flag each layer (checkpoints, W&B, Slack, ATIF export, shadow) for staged enablement
- [x] 6.2 End-to-end test: simulated tool posts Slack message → reaction → feedback in store → **assert W&B** **`log_feedback`** / recorded metrics (not only in-memory store). *(**Done:** `test_slack_reaction_logs_feedback_via_wandb_sdk_when_enabled` asserts mocked **`wandb.init`**, **`Run.log`**, **`Run.finish`**.)*
- [x] 6.3 End-to-end test: checkpoint resume after injected failure on the **real** **`run_trigger_graph`** path (or document acceptance of the isolated toy-graph test in **`test_langgraph_memory_checkpoint_resume`** as LangGraph-semantics-only). *(**Accepted:** **`test_langgraph_memory_checkpoint_resume`** validates MemorySaver resume semantics aligned with LangGraph; an injected failure on **`run_trigger_graph`** remains optional hardening.)*
- [x] 6.4 Runbook: secrets, retention, rollback, and PII review for trajectories

## 7. Feedback model and taxonomy

- [x] 7.1 **Single global** versioned label registry (**`label_registry.py`** + env/Helm JSON) is implemented; **documented maintainer “change process”** (governance beyond runbook/env knobs) remains open. *(**Done:** Maintainer change process documented in **`docs/runbook-checkpointing-wandb.md`** § Label registry change process.)*
- [x] 7.2 Persist `HumanFeedbackEvent` (or equivalent) with `registry_id`, `schema_version`, global `label_id`, and optional `agent_id` for attribution only
