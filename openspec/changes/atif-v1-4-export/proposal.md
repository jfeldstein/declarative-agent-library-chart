## Why

Harbor ATIF v1.4 mapping and export endpoints; ADR 0004.

This is **step 7 of 13** in the checkpointing/observability delivery sequence. **Order:** see `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

## What Changes

- **Baseline:** Runtime behavior for this slice is **already on `main`** (merged PR **#11**, *feat: checkpoints, observability, ATIF v1.4, and OpenSpec follow-ups*).
- **This change** exists so future work and reviews stay **slice-scoped**; follow-up tasks below capture remaining gaps (if any).

## Dependencies

- **Prerequisites:** step **6** — `trajectory-canonical-model`

## Capabilities

### New Capabilities

- `cfha-atif-export`: atif v1.4 export.

## Impact

- Bounded PRs for regressions and enhancements; no monolithic OpenSpec bucket.
