## Why

`hosted_agents/observability/` was introduced for checkpointing, feedback, W&B hooks, and related runtime behavior, but `runtime/pyproject.toml` currently **omits** `*/observability/*` from coverage while CI still enforces **≥85%** on the rest of `hosted_agents`. That makes the gate pass without measuring the observability package and **narrows the spirit of ADR 0002** (enforce 85% test coverage on the runtime). Teams may assume the omit is accidental or that observability is “not really tested.” Restoring coverage (or explicitly documenting a narrower policy in an ADR) removes that ambiguity; this change **adds the missing coverage** by including observability in the coverage denominator and raising tests until the global threshold holds.

## What Changes

- Remove the coverage **`omit`** entry for `*/observability/*` (or replace it with a **documented, minimal** exception list only if strictly necessary).
- Add **unit and/or contract tests** under `runtime/tests/` targeting `hosted_agents.observability` modules until **`pytest-cov` meets `fail-under`** with observability included.
- Optionally add a short **ADR** or amendment clarifying that ADR 0002 applies to **all** first-party runtime packages under `src/hosted_agents/` unless a future ADR explicitly carves out a path (this change prefers **no carve-out**).

## Capabilities

### New Capabilities

- `cfha-runtime-observability-coverage`: Requirements for measuring and maintaining automated test coverage on `hosted_agents/observability/` alongside the rest of the runtime, consistent with ADR 0002.

### Modified Capabilities

- _(none — no existing `openspec/specs/` capability defines observability coverage today.)_

## Impact

- **`runtime/pyproject.toml`**: coverage configuration; possibly `fail-under` if raising the bar is desired after baseline measurement.
- **`runtime/tests/`**: new or expanded tests (mocks for W&B, Slack payloads, checkpointer factory branches, etc.).
- **CI**: `ci.sh` / pytest path unchanged; coverage total may drop until tests land, so **implementation should land in an order that keeps main green** (tests first or same PR as removing omit).
- **Docs**: optional ADR `0003` or amendment to `0002` if the project wants the policy written in `docs/adrs/` as well as OpenSpec.
