## 1. Checkpointing foundation

- [ ] 1.1 Select and configure **production** checkpointer backends (**Postgres** / **Redis** savers) and document **`thread_id` / `checkpoint_id`**. *(**Shipped today:** in-process **`MemorySaver`** by default; **PGlite** optional for local dev; **`build_checkpointer`** still **raises** for `postgres`/`redis` until **`postgres-agent-persistence`** (or follow-on) lands.)*
- [ ] 1.2 Wire persistence via **`StateGraph` + `compile(checkpointer=…)`** + **`graph.invoke`** (**`trigger_graph.py`**). *(**Not used in v1:** LangGraph **`@entrypoint` / `@task`** functional API as in some upstream docs; treat “equivalent” as compiled graph + saver, not literal **`@entrypoint`**.)*
- [x] 1.3 Implement host policy: default-on checkpointing with explicit ephemeral opt-out flag
- [x] 1.4 Expose `get_state` / `get_state_history`-compatible read APIs for operators and internal services
- [x] 1.5 Persist checkpoints around user-visible external side effects (e.g. Slack post) with `checkpoint_id`, `tool_call_id`, `external_ref`, timestamp per spec

## 2. Correlation and Slack feedback

- [x] 2.1 Define stable `tool_call_id`, `run_id`, and `thread_id` propagation through tool execution context
- [ ] 2.2 Add **durable** (survives restarts / multi-replica) store mapping **`(slack_channel_id, message_ts)`** → tool/run/**`checkpoint_id`**. *(**Shipped today:** process-local **`CorrelationStore`** singleton—enough for single-pod dev/tests, not production durability.)*
- [x] 2.3 Implement Slack Events subscription for reactions; map configured emoji to **global registry** labels (positive / negative / neutral per policy)
- [ ] 2.4 Implement idempotency and conflict policy for duplicate, changed, or removed reactions; reconcile with latest Slack state where feasible. *(**Shipped today:** **`dedupe_key`** upsert (“latest wins”) on ingest; **no** removal/reconcile loop against Slack.)*
- [x] 2.5 Orphan reactions: log/queue only—no training-eligible label without resolved correlation

## 3. Weights & Biases integration

- [ ] 3.1 Initialize W&B per top-level run with **fully populated** mandatory tag schema (`agent_id`, `environment`, `skill_id`, `skill_version`, `model_id`, `prompt_hash`, `rollout_arm`, `thread_id`). *(**Shipped today:** schema exists but **`run_trigger_graph`** often passes **`None`** for several tags—tighten wiring before checking this off.)*
- [x] 3.2 Emit hierarchical telemetry: tool calls as child spans (or equivalent) including `tool_call_id` and timing
- [x] 3.3 On feedback ingestion, update W&B trace/span or keyed metrics so feedback is queryable by `tool_call_id` and `checkpoint_id` (`feedback_label`, `feedback_source`)
- [ ] 3.4 Add integration tests or **contract** tests against the real **W&B SDK** shape (or high-fidelity stub), not only ad-hoc mock objects. *(Tests today use lightweight mocks for **`log_tool_span`** / feedback paths.)*
- [x] 3.5 Support **late** feedback after span close; enforce tag cardinality limits and hash/omit sensitive tag values

## 4. Canonical trajectory and ATIF

- [x] 4.1 Implement in-memory/streaming CanonicalTrajectory builder fed by checkpoints and tool results
- [x] 4.2 Pin ATIF schema version and implement exporter from CanonicalTrajectory to ATIF JSON
- [ ] 4.3 Implement **`positive_mining_filter`** on **export** (HTTP **`export_atif`** path): +1-only / terminal-segment rules per spec. *(Filter exists in **`atif.py`** but **export** currently streams raw trajectory without applying it.)*
- [x] 4.4 Implement configurable **redaction** before export; document rules for messages, tool args, and Slack identifiers

## 5. Shadow rollouts

- [x] 5.1 Add configuration for shadow variants (skill version, model, prompt hash) and `request_correlation_id` linking to primary
- [ ] 5.2 Implement default non-mutating shadow path with tool stubbing/skip list and explicit allowlist/danger flag for full mirror. *(**`ShadowSettings` / `should_run_shadow` exist** but **no** request path calls **`should_run_shadow`** yet.)*
- [ ] 5.3 Ensure shadow runs emit the same mandatory W&B tags (with **`rollout_arm=shadow`**), **`shadow_variant_id`**, and comparable metrics joined by **`request_correlation_id` / `thread_id`**. *(Depends on **5.2** wiring.)*
- [ ] 5.4 Shadow off by default; support traffic bounds (**percentage**, **allowlist tenants**, **time windows**). *(**Percentage + allowlist:** implemented in settings. **Time windows:** not implemented.)*

## 6. Rollout and verification

- [x] 6.1 Feature-flag each layer (checkpoints, W&B, Slack, ATIF export, shadow) for staged enablement
- [ ] 6.2 End-to-end test: simulated tool posts Slack message → reaction → feedback in store → **assert W&B** **`log_feedback`** / recorded metrics (not only in-memory store). *(Reaction → **`feedback_store`** is covered; W&B assertions on that path are thin.)*
- [ ] 6.3 End-to-end test: checkpoint resume after injected failure on the **real** **`run_trigger_graph`** path (or document acceptance of the isolated toy-graph test in **`test_langgraph_memory_checkpoint_resume`** as LangGraph-semantics-only).
- [x] 6.4 Runbook: secrets, retention, rollback, and PII review for trajectories

## 7. Feedback model and taxonomy

- [ ] 7.1 **Single global** versioned label registry (**`label_registry.py`** + env/Helm JSON) is implemented; **documented maintainer “change process”** (governance beyond runbook/env knobs) remains open.
- [x] 7.2 Persist `HumanFeedbackEvent` (or equivalent) with `registry_id`, `schema_version`, global `label_id`, and optional `agent_id` for attribution only
