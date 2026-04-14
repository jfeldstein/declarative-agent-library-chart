## 1. Checkpointing foundation

- [x] 1.1 Select and configure production checkpointer backend (e.g. Postgres/Redis) and document `thread_id` / `checkpoint_id` usage
- [x] 1.2 Wire LangGraph functional API (or equivalent) so `@entrypoint` receives an injected checkpointer and tasks persist automatically per step
- [x] 1.3 Implement host policy: default-on checkpointing with explicit ephemeral opt-out flag
- [x] 1.4 Expose `get_state` / `get_state_history`-compatible read APIs for operators and internal services
- [x] 1.5 Persist checkpoints around user-visible external side effects (e.g. Slack post) with `checkpoint_id`, `tool_call_id`, `external_ref`, timestamp per spec

## 2. Correlation and Slack feedback

- [x] 2.1 Define stable `tool_call_id`, `run_id`, and `thread_id` propagation through tool execution context
- [x] 2.2 Add durable store mapping `(slack_channel_id, message_ts)` → tool/run/`checkpoint_id` correlation
- [x] 2.3 Implement Slack Events subscription for reactions; map configured emoji to **global registry** labels (positive / negative / neutral per policy)
- [x] 2.4 Implement idempotency and conflict policy for duplicate, changed, or removed reactions; reconcile with latest Slack state where feasible
- [x] 2.5 Orphan reactions: log/queue only—no training-eligible label without resolved correlation

## 3. Weights & Biases integration

- [x] 3.1 Initialize W&B per top-level run with mandatory tag schema (`agent_id`, `environment`, `skill_id`, `skill_version`, `model_id`, `prompt_hash`, `rollout_arm`, `thread_id`)
- [x] 3.2 Emit hierarchical telemetry: tool calls as child spans (or equivalent) including `tool_call_id` and timing
- [x] 3.3 On feedback ingestion, update W&B trace/span or keyed metrics so feedback is queryable by `tool_call_id` and `checkpoint_id` (`feedback_label`, `feedback_source`)
- [x] 3.4 Add integration tests or contract tests against W&B SDK (mocked) for tags and feedback payload shape
- [x] 3.5 Support **late** feedback after span close; enforce tag cardinality limits and hash/omit sensitive tag values

## 4. Canonical trajectory and ATIF

- [x] 4.1 Implement in-memory/streaming CanonicalTrajectory builder fed by checkpoints and tool results
- [x] 4.2 Pin ATIF schema version and implement exporter from CanonicalTrajectory to ATIF JSON
- [x] 4.3 Implement +1-only (or no -1) dataset filter; terminal-checkpoint segment extraction; default exclusion of negative terminal segments; optional contrastive override
- [x] 4.4 Implement configurable **redaction** before export; document rules for messages, tool args, and Slack identifiers

## 5. Shadow rollouts

- [x] 5.1 Add configuration for shadow variants (skill version, model, prompt hash) and `request_correlation_id` linking to primary
- [x] 5.2 Implement default non-mutating shadow path with tool stubbing/skip list and explicit allowlist/danger flag for full mirror
- [x] 5.3 Ensure shadow runs emit the same mandatory W&B tags (with `rollout_arm=shadow`), `shadow_variant_id`, and comparable metrics (latency, tokens, tool selection, outcome) joined by `request_correlation_id` / `thread_id`
- [x] 5.4 Shadow off by default; support traffic bounds (percentage, allowlist tenants, time windows)

## 6. Rollout and verification

- [x] 6.1 Feature-flag each layer (checkpoints, W&B, Slack, ATIF export, shadow) for staged enablement
- [x] 6.2 End-to-end test: simulated tool posts Slack message → reaction → feedback in store → W&B metric/span update
- [x] 6.3 End-to-end test: checkpoint resume after injected failure matches LangGraph semantics for completed tasks
- [x] 6.4 Runbook: secrets, retention, rollback, and PII review for trajectories

## 7. Feedback model and taxonomy

- [x] 7.1 Implement **single global** versioned label registry and change process (no per-agent label namespaces); document how new labels ship
- [x] 7.2 Persist `HumanFeedbackEvent` (or equivalent) with `registry_id`, `schema_version`, global `label_id`, and optional `agent_id` for attribution only
