## Why

Layered env/ConfigMap-friendly `ObservabilitySettings` and contextvars for run/thread/tool/W&B session ids.

This is **step 1 of 13** in the checkpointing/observability delivery sequence. **Order:** see `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

## What Changes

- **Baseline:** Runtime behavior for this slice is **already on `main`** (merged PR **#11**, *feat: checkpoints, observability, ATIF v1.4, and OpenSpec follow-ups*).
- **This change** exists so future work and reviews stay **slice-scoped**; follow-up tasks below capture remaining gaps (if any).

## Dependencies

- **Prerequisites:** none (first slice).

## Capabilities

### New Capabilities

- `cfha-observability-foundation`: observability settings and run context.

## Impact

- Bounded PRs for regressions and enhancements; no monolithic OpenSpec bucket.
