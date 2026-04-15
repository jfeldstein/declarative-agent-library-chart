# Runbook: checkpoints, Slack feedback, and W&B

This runbook covers the **runtime** feature flags for durable LangGraph checkpoints, Slack reaction correlation, and optional Weights & Biases traces (see OpenSpec change `agent-checkpointing-wandb-feedback`). **ATIF export** and **shadow rollout** Helm/runtime surfaces were removed; use `extraEnv` on a fork if you still need those env toggles.

## Thread and checkpoint identifiers

- **`thread_id`**: stable per conversation or operator session. Clients may send `thread_id` in the trigger JSON body or `X-Agent-Thread-Id` on `POST /api/v1/trigger`. If omitted, the runtime falls back to a new UUID for the HTTP request’s `run_id` (less ideal for resume semantics).
- **`checkpoint_id`**: assigned by the LangGraph checkpointer (and additional **side-effect** records for tools such as `slack.post_message`). Side-effect metadata is listed under `GET /api/v1/runtime/threads/{thread_id}/side-effects`.
- **`run_id`**: UUID generated per trigger invocation (distinct from `X-Request-Id`).

## Checkpointer backends

| `HOSTED_AGENT_CHECKPOINT_BACKEND` | Behavior |
|-----------------------------------|----------|
| `memory` (default) | In-process `MemorySaver`; suitable for dev / single replica. |
| `postgres` | **Not bundled** in the default image. Set `HOSTED_AGENT_POSTGRES_URL` and add a LangGraph Postgres checkpointer dependency, then extend `build_checkpointer` in `hosted_agents/observability/checkpointer.py`. |
| `redis` | Reserved until a Redis saver is pinned for this chart. |

When `HOSTED_AGENT_CHECKPOINTS_ENABLED` is **false** (Helm default), the runtime uses the original single-node graph without persistence.

**Ephemeral runs:** JSON field `ephemeral: true` opts out of checkpoint persistence even when checkpointing is enabled globally.

### Embedded PostgreSQL (PGlite) for local dev

Set **`HOSTED_AGENT_USE_PGLITE=1`** to start an embedded [PGlite](https://pglite.dev/) instance (via optional Python package **`py-pglite`**) and set **`HOSTED_AGENT_POSTGRES_URL`** when it is unset. Install: **`uv sync --extra pglite`**. First run may install Node dependencies (PGlite is WASM/Node-backed).

- Uses **TCP** mode on **`127.0.0.1`** with a free port (or **`HOSTED_AGENT_PGLITE_TCP_PORT`** / **`HOSTED_AGENT_PGLITE_TCP_HOST`** to pin).
- Checkpoint and shared Postgres consumers read **`HOSTED_AGENT_POSTGRES_URL`** only.
- **Single process only** (e.g. one Uvicorn worker). Do not rely on one embedded DB across multiple Gunicorn workers.
- CI and minimal images: omit the **`pglite`** extra; use a real Postgres service or stay on **`memory`**.

## Operator HTTP APIs

- `GET /api/v1/runtime/threads/{thread_id}/state` — latest checkpoint snapshot (LangGraph `get_state` semantics).
- `GET /api/v1/runtime/threads/{thread_id}/checkpoints` — history (`get_state_history`).
- `GET /api/v1/runtime/threads/{thread_id}/side-effects` — logical checkpoints around visible side effects (Slack posts).
- `POST /api/v1/integrations/slack/reactions` — normalized reaction payload (`channel_id`, `message_ts`, `reaction`, `event_id`, `user_id`).
- `GET /api/v1/runtime/feedback/human` — recorded human feedback events (process-local store in default build).

## Secrets, retention, rollback, PII

- **Secrets:** store `WANDB_API_KEY`, Slack tokens, and database URLs in Kubernetes Secrets; reference them from the Deployment (not committed to values).
- **Retention:** checkpoint and trajectory retention are deployment-specific; the default in-memory stores reset on restart.
- **Rollback:** disable feature flags (`HOSTED_AGENT_CHECKPOINTS_ENABLED`, `HOSTED_AGENT_WANDB_ENABLED`, `HOSTED_AGENT_SLACK_FEEDBACK_ENABLED`, etc.) via Helm values; the runtime remains compatible with older clients.
- **PII:** scrub prompts, tokens, and user identifiers before sending data to W&B or external stores; keep W&B tags low-cardinality per `docs/observability.md`.

## Helm values (short)

See `helm/chart/values.yaml` → top-level **`checkpoints`**, **`wandb`**, and **`scrapers.slack.feedback`** for toggles that map to the env vars above. **`checkpoints.postgresUrl`** sets **`HOSTED_AGENT_POSTGRES_URL`**. Optional **`scrapers.slack.feedback.labelRegistry`** overrides the default global feedback label registry JSON (`HOSTED_AGENT_LABEL_REGISTRY_JSON`).
