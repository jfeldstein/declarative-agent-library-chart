## Why

Automatic tracing hooks with fixed tag schema; tests use stubs—no outbound network.

This is **step 8 of 13** in the checkpointing/observability delivery sequence. **Order:** see `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

## What Changes

- **Baseline:** Runtime behavior for this slice is **already on `main`** (merged PR **#11**, *feat: checkpoints, observability, ATIF v1.4, and OpenSpec follow-ups*).
- **This change** exists so future work and reviews stay **slice-scoped**; follow-up tasks below capture remaining gaps (if any).

## Dependencies

- **Prerequisites:** step **3** — `trigger-graph-memory-checkpoints`

## Capabilities

### New Capabilities

- `cfha-wandb-runtime-traces`: w&b runtime traces (optional).

## Impact

- Bounded PRs for regressions and enhancements; no monolithic OpenSpec bucket.
