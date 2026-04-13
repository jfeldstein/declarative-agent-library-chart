## Delivery sequence

This change is **step 13 of 13** in `checkpointing-observability-delivery-plan` (see `openspec/changes/checkpointing-observability-delivery-plan/design.md`). **Depends on:** step **9** (`observability-shadow-runtime-hooks`), **`shadow-rollout-evaluation`**, and tracing/checkpointing shipped in earlier steps.

---

## Why

Shadow rollout today is mostly **configuration and telemetry scaffolding** (flags, sampling, operational signals). Operators still lack a **guaranteed non-mutating second execution** that exercises the same high-level request through planner/model/tool selection with **external mutations stubbed**, so comparisons of latency, tokens, tool plans, and outcomes remain incomplete or unsafe. This change specifies a **full twin execution path** that runs alongside (or immediately after) the primary path without committing side effects, except under explicit allowlists or dangerous overrides.

## What Changes

- Define a **shadow twin runner** that accepts the same normalized request context as the primary run and produces a **shadow outcome** (messages, tool call graph, metrics) under an isolated execution context.
- Specify **tool classification** (mutating vs read-only vs internal) and **default stub behavior** for mutating tools: no network I/O to external systems unless allowlisted; record **planned args**, **stubbed result shape**, and **stub reason** in trajectory and telemetry.
- Specify **correlation and identity**: mandatory `request_correlation_id`, `thread_id`, `rollout_arm=shadow`, `shadow_variant_id`, and **separate** LangGraph checkpoint thread namespace (or equivalent) so shadow state never overwrites primary checkpoints.
- Specify **scheduling**: after-primary vs in-parallel (async) with **failure isolation** (shadow failure must not fail the primary HTTP response unless explicitly configured).
- Specify **telemetry parity** with primary for comparable fields (latency, token usage, tool names/order, outcome classification) and **W&B** join keys.
- Specify **ATIF / export** rules: shadow steps are **provenance-tagged** and optional inclusion in exports (default: separate manifest or filter by `rollout_arm`).
- **BREAKING**: None at spec level (behavioral additions); runtime implementations may add new env flags and API fields.

## Capabilities

### New Capabilities

- `shadow-twin-execution`: End-to-end specification of the **non-mutating twin execution path** for shadow rollouts: runner lifecycle, tool stubbing contract, checkpoint isolation, scheduling, failure semantics, and export/telemetry parity.

### Modified Capabilities

- _(none — `openspec/specs/` has no published capability files yet; this change aligns with `shadow-rollout-evaluation` and delivery step 9 (`observability-shadow-runtime-hooks`) without a formal delta file in `openspec/specs/`.)_

## Impact

- **Runtime** (`hosted_agents`): new or extended modules for shadow scheduling, tool dispatch wrappers, stub registry, and second graph invocation; possible changes to `trigger_graph` / supervisor entrypoints.
- **Helm / config**: additional values for twin mode (sync vs async), stub profiles, allowlists, and danger flags.
- **Observability**: W&B runs/spans, Prometheus metrics, structured logs; trajectory and ATIF export shape.
- **Tests**: contract tests for stub behavior, isolation, and telemetry join keys; load/e2e tests optional follow-up.
