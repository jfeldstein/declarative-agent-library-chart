## Context

This change **extracts** shadow rollout requirements from **`agent-checkpointing-wandb-feedback`**. Primary workstreams (checkpointer as source of truth, automatic W&B traces, Slack feedback) should land first; shadow adds **variant execution** and **comparison** without blocking that spine.

## Goals / Non-Goals

**Goals:**

- Run **shadow** variants with **comparable** W&B tags and correlation ids to **primary**.
- **Prevent duplicate mutations** (e.g. double Slack posts) by default.
- **Opt-in** and **bounded** traffic for cost and risk control.

**Non-Goals:**

- Defining ATIF export (not required for shadow; comparisons use W&B and/or checkpoint APIs).
- Replacing the primary checkpointer model from the parent change.

## Decisions

1. **Tagging** — Shadow runs **SHALL** set `rollout_arm=shadow`, `shadow_variant_id`, and share join keys with primary (`thread_id` and/or `request_correlation_id`) per deployment config.
2. **Safety** — Default **read-only / stubbed** tools for shadow; **full mirror** only behind an explicit dangerous flag and allowlists.
3. **Ordering** — Implement after parent change’s W&B + checkpoint linkage exists so shadow spans are comparable in the same project UI.

## Risks

- **Cost**: duplicate LLM calls—mitigate with sampling and caps.
- **Leaks**: shadow accidentally posting—mitigate with default stubbing and tests.

## Open Questions

- Exact Helm/runtime config shape for variant matrix vs single shadow slot.
- Whether shadow shares `thread_id` with primary or uses a derived id plus explicit correlation tag only.
