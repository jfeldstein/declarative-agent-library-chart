## 1. Execution context and tool registry

- [ ] 1.1 Add `ShadowExecutionContext` (or equivalent) with `rollout_arm`, `shadow_variant_id`, `request_correlation_id`, shadow persistence key, stub policy, and budgets; thread through trigger/supervisor entrypoints
- [ ] 1.2 Define tool shadow metadata schema (`shadowBehavior`, optional allowlist hints) and validate at startup for registered tools
- [ ] 1.3 Implement default classification rule: unknown tool ids → mutating external

## 2. Twin runner and scheduling

- [ ] 2.1 Implement shadow twin runner that clones normalized request boundary state (messages, skill unlocks snapshot, MCP allowlist) and invokes the same graph entrypoint under shadow context
- [ ] 2.2 Add after-primary synchronous mode with configurable deadline; ensure primary HTTP response is not blocked beyond policy when async is enabled
- [ ] 2.3 Add optional async shadow queue (in-process first) with cancellation on client disconnect when configured

## 3. Tool dispatch, stubbing, and overrides

- [ ] 3.1 Centralize tool dispatch so shadow context intercepts mutating external tools before real I/O
- [ ] 3.2 Implement stub envelope (`shadow_stub`, `tool`, `reason`, redacted args) and unit tests for shape stability
- [ ] 3.3 Implement shadow tool allowlist and dangerous full-mirror flag per design; refuse ambiguous configurations
- [ ] 3.4 Apply variant overrides (model id, prompt hash, skill version) only inside shadow context

## 4. Checkpoint isolation and failure semantics

- [ ] 4.1 Ensure shadow graph uses isolated checkpoint namespace or ephemeral shadow compile path; verify no primary `thread_id` checkpoint mutation
- [ ] 4.2 Map shadow failures to operational telemetry without affecting primary HTTP status (default)
- [ ] 4.3 Enforce shadow budgets (wall time, tokens, tool calls) with clean termination and telemetry reason codes

## 5. Observability (metrics, logs, W&B)

- [ ] 5.1 Emit comparable primary vs shadow metrics (latency, tokens, tool order/count, outcome) joined by `request_correlation_id`
- [ ] 5.2 Initialize distinct W&B runs or clearly separated spans per arm with mandatory tag parity (`rollout_arm`, `shadow_variant_id`, `thread_id` / correlation)
- [ ] 5.3 Add Prometheus counters/histograms for shadow invocations, stubs, budget hits, and failures

## 6. Trajectory and ATIF export

- [ ] 6.1 Append shadow steps to canonical trajectory with provenance tags; default export filters per spec
- [ ] 6.2 Document and implement export flag for include/exclude shadow manifest

## 7. Configuration and Helm

- [ ] 7.1 Add env/Helm values for twin enable, mode (sync/async), deadlines, budgets, allowlist, dangerous mirror, checkpoint mode for shadow
- [ ] 7.2 Extend runbook with operational guidance (cost, rollback, misclassification response)

## 8. Verification

- [ ] 8.1 Contract tests: mutating tool stubbed; allowlisted tool executes; full mirror gated by danger flag
- [ ] 8.2 Tests: primary checkpoint unchanged after shadow; correlation id joins primary and shadow telemetry records
- [ ] 8.3 Integration or e2e test (optional): sample echo read-only vs slack mutating stub under shadow twin enabled
