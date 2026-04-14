## Context

Slack **Events API** and **Socket Mode** deliver **`app_mention`** payloads to something the operator runs. The runtime already compiles **`run_trigger_graph`** for **`POST /api/v1/trigger`**. This change is **only** the bridge from Slack → that pipeline.

## Goals / Non-Goals

**Goals:**

- **Verify** inbound Slack traffic per topology (HTTP signing + URL challenge, or Socket Mode handshake).
- **Map** **`app_mention`** → **`TriggerBody.message`** plus structured Slack ids for downstream use (so **`slack-tools`** can be invoked without guessing context).
- **Never** call Slack **`chat.*`** for user-visible effects on the trigger path; responses use **`slack-tools`**.

**Non-Goals:**

- **`slack_sdk.WebClient`** for posting messages (tools change).
- **RAG** / **`POST /v1/embed`** on the trigger path.

## Decisions

1. **Topology**: **Socket Mode** default when no stable public URL; **HTTP Events** when ingress exists.
2. **Invocation**: Prefer **direct** internal **`run_trigger_graph`** over loopback HTTP to avoid auth complexity; document if HTTP is chosen instead.
3. **Idempotency**: Optional **`event_id`** dedupe for Slack retries (see tasks).

## Risks / Trade-offs

- Long-lived Socket Mode listener → requires a **Deployment**, not ephemeral-only scale-to-zero, unless HTTP mode is used.

## Migration Plan

1. Feature-flag listener; verify URL challenge and one mention → one trigger.
2. Enable in staging; monitor duplicates and latency.
3. Production; rollback by disabling subscription / env.

## Open Questions

- **DM** events vs **`app_mention`** only for v1.
