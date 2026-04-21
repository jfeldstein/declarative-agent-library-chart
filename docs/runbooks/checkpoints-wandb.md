# Runbook: checkpoints, W&B, and feedback (DALC runtime)

## Secrets

- **W&B** — `WANDB_API_KEY` (Kubernetes Secret). Optional: `WANDB_ENTITY`.
- **Slack** (when reaction ingestion is implemented) — bot token + signing secret; not required for checkpoint/W&B-only operation.

## Enablement flags

| Variable | Purpose |
| -------- | ------- |
| `HOSTED_AGENT_CHECKPOINT_STORE` | `memory` (default), `none`, or future `postgres` / `redis`. |
| `HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED` | `true` / `1` / `yes` / `on` — intent to trace (requires `WANDB_API_KEY` + project). Legacy `HOSTED_AGENT_WANDB_ENABLED` is still honored. |
| `WANDB_PROJECT` or `HOSTED_AGENT_WANDB_PROJECT` | W&B project name. |
| `HOSTED_AGENT_SLACK_FEEDBACK_ENABLED` | Reserved for Slack reaction ingestion (off until implemented). |

Verify configuration with **`GET /api/v1/runtime/summary`** → `observability`.

## Rollback

1. Set `HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED` (or legacy `HOSTED_AGENT_WANDB_ENABLED`) off and redeploy (traces stop; checkpoints unaffected).
2. Set `HOSTED_AGENT_CHECKPOINT_STORE=none` to disable persistence and state HTTP APIs (**503** on thread routes).
3. Existing checkpoint data in memory is process-local; restarting pods clears it.

## PII and retention

- Do not put raw user content in W&B **tags**; use trace payloads with redaction policies.
- `MemorySaver` checkpoints contain graph state (may include model outputs); use `none` or a bounded store for strict ephemeral workloads.

## Failure modes

- **Postgres/Redis store** — Until implemented, misconfiguration raises at graph compile; set `memory` or `none`.
- **W&B** — If the SDK is unavailable in the image, tracing is skipped even when env suggests readiness; install `wandb` in the image when enabling traces.
