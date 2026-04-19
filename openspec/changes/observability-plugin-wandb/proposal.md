# Proposal: W&B observability plugin (lifecycle bus)

## Context

Weights & Biases tracing was implemented ad hoc in `run_trigger_graph`, `run_tool_json`, and Slack feedback ingestion. Observability Phase 1 introduced a synchronous lifecycle bus (`SyncEventBus`) with stable `EventName` values; legacy Prometheus metrics already subscribe there.

## Goal

- Move `WandbTraceSession` implementation under `agent/observability/plugins/wandb/` and register a **wandb trace plugin** on the agent bus for `run.started`, `run.ended`, `tool.call.completed`, and `feedback.recorded`.
- Preserve existing recording and SDK contract behavior (tests unchanged in intent).
- **Breaking Helm change:** consolidate chart values from top-level **`wandb.*`** to **`observability.plugins.wandb.*`** (enabled, project, entity) while keeping the same runtime env vars (`HOSTED_AGENT_WANDB_ENABLED`, `WANDB_PROJECT`, `WANDB_ENTITY`).

## Non-goals

- Changing LangGraph checkpoint semantics or Postgres correlation schemas (remain in `agent-checkpointing-wandb-feedback` / persistence specs).
- Adding LLM-level W&B spans (still deferred); tool spans and feedback logging remain as today.

## Spec delta

See `specs/dalc-plugin-wandb-traces/spec.md` (draft under this change).

## Risks / mitigations

- **Subscriber ordering:** W&B handlers run after publish order; synchronous bus preserves deterministic order with legacy metrics.
- **Helm migration:** Operators must move values keys; documented in promoted `dalc-chart-runtime-values` RTV-002 and this change.
