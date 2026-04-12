## Why

Teams need to compare **candidate** skills, models, or system prompts against the **primary** path without doubling production side effects. That capability was scoped in **`agent-checkpointing-wandb-feedback`** and **split out** so checkpointing, W&B tracing, and Slack feedback can ship first.

## What Changes

- Configuration and execution of **shadow variants** (skill version, model id, prompt hash) sharing the same high-level request context as the primary run.
- **Default non-mutating** shadow execution: stub or skip external side-effect tools unless allowlisted or a **dangerous** override is enabled.
- **Comparable telemetry** in **Weights & Biases** (and checkpoints where relevant): mandatory **`rollout_arm`** (`primary` | `shadow`), **`shadow_variant_id`** (or equivalent), and join keys such as **`request_correlation_id`** / **`thread_id`**.
- Shadow is **opt-in** and **bounded** (percentage, allowlist, time windows).

## Capabilities

### New Capabilities

- `shadow-rollout-evaluation`: As above.

### Dependencies

- **`agent-checkpointing-wandb-feedback`** (or equivalent shipped behavior): automatic checkpoints, W&B tracing, and tag schema—extended here with shadow-specific tags and policies.

## Impact

- Runtime and Helm: shadow config surface, tool policy for shadow runs, correlation IDs linking primary and shadow.
- Ops: cost controls, feature flags, runbooks for “full mirror” shadow if enabled.
