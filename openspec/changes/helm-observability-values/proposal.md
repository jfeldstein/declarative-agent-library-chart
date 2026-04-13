## Why

Library chart `observability.*` mapping to runtime env vars.

This is **step 10 of 13** in the checkpointing/observability delivery sequence. **Order:** see `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

## What Changes

- **Baseline:** Runtime behavior for this slice is **already on `main`** (merged PR **#11**, *feat: checkpoints, observability, ATIF v1.4, and OpenSpec follow-ups*).
- **This change** exists so future work and reviews stay **slice-scoped**; follow-up tasks below capture remaining gaps (if any).

## Dependencies

- **Prerequisites:** steps **1–9** (Helm values must match the runtime env contract established by those slices)

## Capabilities

### New Capabilities

- `cfha-helm-observability`: helm observability values.

## Impact

- Bounded PRs for regressions and enhancements; no monolithic OpenSpec bucket.
