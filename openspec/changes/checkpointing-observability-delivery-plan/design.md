# Checkpointing & observability — delivery order (1 of 13 through 13 of 13)

**Rule:** Each step **SHALL** keep `pytest-cov` on `hosted_agents` at the configured `fail-under` (**≥85%**) **without** adding broad `omit` globs for new code. Use **narrow** `pragma: no cover` only where ADR 0002 already allows.

| Step | Change directory (under `openspec/changes/`) | Depends on | Notes |
|------|----------------------------------------------|------------|-------|
| 1 | `observability-foundation-settings-context` | — | Env-driven settings + observability `run_context` contextvars; coverage includes `hosted_agents/observability/`. |
| 2 | `observability-checkpointer-factory` | 1 | `build_checkpointer` / memory vs none. |
| 3 | `trigger-graph-memory-checkpoints` | 2 | LangGraph compile, `thread_id` / `ephemeral`, checkpointed trigger graph. |
| 4 | `operator-thread-checkpoint-apis` | 3 | FastAPI operator routes for state / checkpoints / side-effects. |
| 5 | `slack-feedback-correlation-ingest` | 4 | Correlation store, `slack.post_message`, reaction ingest (mocked in tests). |
| 6 | `trajectory-canonical-model` | 1 | Canonical trajectory / step log structures. |
| 7 | `atif-v1-4-export` | 6 | Harbor ATIF v1.4 export; ADR 0004. |
| 8 | `wandb-runtime-traces` | 3 | Optional W&B spans; no network in unit tests. |
| 9 | `observability-shadow-runtime-hooks` | 3, 8 | Shadow flags + runtime hooks; full policy in `shadow-rollout-evaluation`. |
| 10 | `helm-observability-values` | 1–9 (conceptually) | Chart `observability.*` → env. |
| 11 | `docs-runbook-checkpoint-wandb` | 10 | Operator runbook + cross-links. |
| 12 | `postgres-agent-persistence` | 2, 3 | **Existing** change; durable Postgres checkpointer + related storage. |
| 13 | `shadow-non-mutating-twin-execution` | 9, `shadow-rollout-evaluation` | **Existing** change; non-mutating twin runner. |

**Archived (superseded as active work):** `archive/2026-04-13-agent-checkpointing-wandb-feedback`, `archive/2026-04-13-observability-package-coverage`.

**Related (not renumbered):** `shadow-rollout-evaluation` — product requirements for shadow rollouts; depends on checkpointing + tracing shipped in steps 1–8.
