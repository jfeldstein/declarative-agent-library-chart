## Why

The monolithic OpenSpec change `agent-checkpointing-wandb-feedback` bundled checkpointing, Slack feedback, W&B, ATIF export, Helm, and follow-on work into one review surface. Delivery is clearer as **thirteen ordered slices** (eleven new tracked changes plus two existing long-horizon changes), each mergeable with **full `hosted_agents` coverage** per ADR 0002—**no package-wide coverage omit**.

## What Changes

- **Archive** (historical reference only): `openspec/changes/archive/2026-04-13-agent-checkpointing-wandb-feedback`, `openspec/changes/archive/2026-04-13-observability-package-coverage`.
- **Active plan**: this directory’s `design.md` is the **authoritative order** (steps **1–13**) and dependency notes.
- **Implementation** proceeds by **opening PRs against each slice** (or small stacks), not by re-expanding a single mega-change.

## Capabilities

### New Capabilities

- `checkpointing-observability-delivery-plan`: Meta capability—ordering and traceability only; no runtime behavior.

### Modified Capabilities

- *(none in `openspec/specs/` — plan lives under `openspec/changes/`.)*

## Impact

- Docs and dependent OpenSpec proposals reference this plan instead of the archived monolithic path.
