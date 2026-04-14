# Checkpointing and W&B traces

Operator-oriented summary for **`openspec/changes/agent-checkpointing-wandb-feedback`**. See also [docs/observability.md](observability.md).

## Thread and checkpoint identifiers

- **`thread_id`** — Stable id for a logical conversation. Clients may send **`thread_id`** in the trigger JSON body or **`X-Thread-Id`** on `POST /api/v1/trigger`. If omitted, the server generates a new UUID (one-shot run; no resume).
- **`run_id`** — New UUID per trigger invocation; used for W&B run identity and tool-call id prefixes.
- **`checkpoint_id`** — Assigned by the LangGraph checkpointer (see `checkpoint_id` in `GET /api/v1/trigger/threads/{thread_id}/checkpoints` responses).

## Checkpointer backend

| `HOSTED_AGENT_CHECKPOINT_STORE` | Behavior |
| ------------------------------- | -------- |
| *(unset)* | **`memory`** — in-process `MemorySaver` (default-on). |
| `memory` | Same as default. |
| `none` | No checkpointer; `ephemeral` is implied for persistence APIs. |
| `postgres`, `redis` | Reserved; raises at compile time until implemented. |

## Inspection HTTP API

Requires **`HOSTED_AGENT_CHECKPOINT_STORE` ≠ `none`**:

- **`GET /api/v1/trigger/threads/{thread_id}/state`** — Latest `StateSnapshot` (`values`, `next`, `metadata`, `config`, …).
- **`GET /api/v1/trigger/threads/{thread_id}/checkpoints`** — Ordered checkpoint history (`get_state_history`).

## Trigger body flags

- **`ephemeral`: true** — This invocation uses a graph **without** a checkpointer; it does **not** append to thread history.
- **`thread_id`** — Reuse across requests to accumulate checkpoints on the same thread.

## W&B tags (bounded)

Populate via environment (see [observability.md](observability.md)): `HOSTED_AGENT_ID`, `HOSTED_AGENT_ENV`, `HOSTED_AGENT_SKILL_ID`, `HOSTED_AGENT_SKILL_VERSION`, `HOSTED_AGENT_CHAT_MODEL`, `HOSTED_AGENT_PROMPT_HASH`. `thread_id` and `run_id` are always added in code when tracing runs.

## Global feedback registry

Bundled JSON: `helm/src/hosted_agents/data/feedback_registry.v1.json`. Bump **`schema_version`** and ship a new file when adding Slack emoji → label mappings.
