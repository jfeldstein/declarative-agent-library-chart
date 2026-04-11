## 1. Instrumentation and checkpoint model

- [ ] 1.1 Define internal schema for `checkpoint_id`, `run_id`, `tool_call_id`, `external_ref`, and timestamps; add to agent runtime tracing contract.
- [ ] 1.2 Implement checkpoint emission for at least one user-visible tool (e.g. Slack post) with durable persistence suitable for reaction lookup.
- [ ] 1.3 Add configuration for which tools require checkpoints and which channels qualify for feedback ingestion.

## 2. Slack (or first channel) reaction ingestion

- [ ] 2.1 Implement webhook/handler for reaction events; map configured emoji to positive/negative/neutral enums.
- [ ] 2.2 Resolve `channel` + `ts` to `checkpoint_id` via index; implement orphan queue and operational metrics.
- [ ] 2.3 Implement idempotency/upsert and reaction_removed handling per design policy.

## 3. Weights & Biases traces and tags

- [ ] 3.1 Add wandb client initialization (API key, project, entity) with environment-based configuration.
- [ ] 3.2 Emit wandb run/trace spans for LLM and tool calls aligned with internal `tool_call_id` values.
- [ ] 3.3 Apply required tags (`env`, `agent_name`, `agent_version`, `skill_set_version`, `model_id`, `rollout`, optional `shadow_variant_id`).
- [ ] 3.4 On correlated feedback, append or update trace data with `feedback_label`, `feedback_source`, and `checkpoint_id` (including late reactions).

## 4. ATIF export and positive mining

- [ ] 4.1 Implement log → ATIF JSON mapper with a versioned schema/fixture test.
- [ ] 4.2 Integrate redaction pipeline for secrets and disallowed PII before export.
- [ ] 4.3 Build positive-segment extraction job (configurable window, terminal positive checkpoint) for SFT/RLFT consumers.
- [ ] 4.4 Ensure default positive mining excludes negative terminal checkpoints unless contrastive override is set.

## 5. Shadow rollouts

- [ ] 5.1 Add configuration for shadow variants (prompt/skill/model identifiers) and traffic bounds (default off).
- [ ] 5.2 Implement shadow execution path with `rollout=shadow` labeling in logs and wandb.
- [ ] 5.3 Enforce default non-mutation for shadow external tools (stub/skip/sandbox) unless policy allows.
- [ ] 5.4 Emit joinable comparison fields (`request_id` / `correlation_id`) between primary and shadow.

## 6. Verification and rollout

- [ ] 6.1 Add integration tests: checkpoint → wandb span → synthetic reaction → feedback on trace.
- [ ] 6.2 Add export test: positive-labeled run produces expected ATIF slice; negative excluded from default mining.
- [ ] 6.3 Document operator runbook (feature flags, Slack app scopes, wandb project naming, retention).
- [ ] 6.4 Pilot in non-production workspace; enable production gradually with monitoring and rollback steps from design.
