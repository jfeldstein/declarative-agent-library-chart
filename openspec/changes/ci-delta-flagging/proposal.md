## Why

Evaluation and runtime behavior will drift unless CI can **detect regressions** against a committed baseline (deltas, thresholds, or suite summaries). That concern is **orthogonal** to agent authoring and belongs in its own change.

## What Changes

- _(Stub)_ Define **`ci-delta-flagging`**: how CI consumes eval artifacts or metrics, what constitutes a regression, and how failures surface on PRs.

## Capabilities

### New Capabilities

- `ci-delta-flagging`: _(deferred — stub proposal only.)_

### Modified Capabilities

- _(none until spec work begins.)_

## Impact

- **`agent-maker-system`** may require generated PRs to pass whatever checks this capability defines; integration is **documentation + workflow** once both exist.
