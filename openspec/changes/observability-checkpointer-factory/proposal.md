## Why

`build_checkpointer` selects in-memory LangGraph checkpointer vs no-op.

This is **step 2 of 13** in the checkpointing/observability delivery sequence. **Order:** see `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

## What Changes

- **Baseline:** Runtime behavior for this slice is **already on `main`** (merged PR **#11**, *feat: checkpoints, observability, ATIF v1.4, and OpenSpec follow-ups*).
- **This change** exists so future work and reviews stay **slice-scoped**; follow-up tasks below capture remaining gaps (if any).

## Dependencies

- **Prerequisites:** step **1** — `observability-foundation-settings-context`

## Capabilities

### New Capabilities

- `cfha-observability-checkpointer`: checkpointer factory (memory / none).

## Impact

- Bounded PRs for regressions and enhancements; no monolithic OpenSpec bucket.
