## 1. Configuration

- [ ] 1.1 Add configuration for shadow variants (skill version, model id, prompt hash) and `request_correlation_id` (or equivalent) linking to primary
- [ ] 1.2 Document feature flags and traffic bounds (percentage, allowlist tenants, time windows); default **off**

## 2. Execution and safety

- [ ] 2.1 Implement default **non-mutating** shadow path with tool stubbing/skip list
- [ ] 2.2 Add explicit allowlist and **dangerous** feature flag for full mirror shadow (if ever enabled)
- [ ] 2.3 Ensure shadow runs do not double-post to external channels unless policy explicitly allows

## 3. Telemetry

- [ ] 3.1 Emit W&B telemetry for shadow with `rollout_arm=shadow`, `shadow_variant_id`, and the same mandatory tag keys as primary where applicable (plus join keys for comparison)
- [ ] 3.2 Record checkpoint or run metadata sufficient to compare primary vs shadow for the same correlation id (latency, tokens, tool selection, outcome)

## 4. Verification

- [ ] 4.1 Integration or contract tests: shadow disabled → no shadow spans; shadow enabled → comparable tags and no unintended side effects in default mode
- [ ] 4.2 Runbook: cost limits, rollback, and when to enable full mirror
