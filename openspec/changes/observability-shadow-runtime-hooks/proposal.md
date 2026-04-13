## Why

Feature flags and runtime hooks feeding `shadow-rollout-evaluation` / step 13.

This is **step 9 of 13** in the checkpointing/observability delivery sequence. **Order:** see `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

## What Changes

- **Baseline:** Runtime behavior for this slice is **already on `main`** (merged PR **#11**, *feat: checkpoints, observability, ATIF v1.4, and OpenSpec follow-ups*).
- **This change** exists so future work and reviews stay **slice-scoped**; follow-up tasks below capture remaining gaps (if any).

## Dependencies

- **Prerequisites:** steps **3** (`trigger-graph-memory-checkpoints`) and **8** (`wandb-runtime-traces`)

## Capabilities

### New Capabilities

- `cfha-observability-shadow-hooks`: shadow runtime hooks.

## Impact

- Bounded PRs for regressions and enhancements; no monolithic OpenSpec bucket.
