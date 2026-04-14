## Context

The runtime already exposes an allowlisted **`slack.post_message`** tool, but **`hosted_agents.tools_impl.slack_post`** is **simulated** (correlation / checkpoints only). **Slack scraper** work targets **CronJob → RAG** (`/v1/embed`). Interactive Slack needs two pieces: **something that turns `@mention` into a trigger run**, and **something that lets the running graph talk back to Slack**.

## Goals / Non-Goals

**Goals:**

- **`slack-trigger`**: **Only** “user can @ tag the bot”: receive events from Slack, satisfy Slack’s **transport requirements** (URL challenge, signing secret, or Socket Mode handshake as applicable), and **invoke the same trigger pipeline** as **`POST /api/v1/trigger`** with a normalized **message + Slack context** payload.
- **`slack-tools`**: **Only** what a **triggered** agent uses to **ack and respond**: reactions, posts (including thread), updates, and **bounded** history reads via **`slack_sdk`**, registered like other **`tools_impl`** tools.
- Keep **Helm/env names** for **trigger**, **tools**, and **scraper** separable so operators do not route chat into RAG jobs or confuse tokens.

**Non-Goals:**

- **No** default path from **Slack tools** or **Slack trigger** body text into **`POST /v1/embed`**.
- **No** mandate to use two different Slack **apps** if one app is sufficient; the split is **logical** (trigger vs tools), not necessarily two OAuth clients.

## Decisions

### A. Slack Trigger

1. **Topology**: **Socket Mode** as default for clusters without a stable public URL; **HTTP Events API** (`POST` to runtime) when ingress and signing-secret verification are available.
2. **Invocation**: On **`app_mention`**, build **`TriggerBody`** (or equivalent internal call) and call **`run_trigger_graph`** (or **internal HTTP** to `/api/v1/trigger` only if we explicitly want network round-trip—prefer **direct** internal call in implementation to avoid auth loops; document the choice).
3. **Scope**: Trigger layer **SHALL NOT** call Slack Web **`chat.*`** APIs itself except what Slack requires for the listener (none for pure forward); all user-visible Slack actions go through **`slack-tools`**.

### B. Slack Tools

1. **Surface**: Explicit tool ids in **`hosted_agents.tools_impl.dispatch`**, backed by **`slack_sdk.WebClient`**, env prefix e.g. **`HOSTED_AGENT_SLACK_TOOLS_*`** (illustrative).
2. **Simulation**: Keep CI behavior by gating real WebClient on presence of configured token (**design default: (b)** from prior note).
3. **Observability**: Reuse correlation / side-effect checkpoint patterns for real calls.

### C. Cross-cutting

- **Scraper disjointness**: Scraper CronJob env continues to use **`scrapers`** / scraper-specific keys; **trigger** and **tools** use keys documented in this change only.
- **IDs in prompts**: Trigger passes **channel id**, **thread ts** / root **ts**, and **team** where available so the model can call tools without guessing.

## Risks / Trade-offs

- **[Risk] Conflating trigger and tools in one Helm blob** → **Mitigation**: separate sub-objects or prefixes in values schema with clear descriptions.
- **[Risk] Internal vs HTTP trigger** → **Mitigation**: document one approach; if HTTP is chosen, secure it (same-process auth or network policy).
- **[Risk] Socket Mode requires long-lived process** → **Mitigation**: same as before—document Deployment expectations.

## Migration Plan

1. Ship **Slack trigger** behind feature flag; verify URL challenge and **`app_mention`** → one successful **`run_trigger_graph`** invocation per event (with idempotency if Slack retries).
2. Ship **Slack tools** with mocks; then enable real token in staging; verify reactions + thread reply.
3. Production rollout; monitor Slack API errors and trigger latency.

**Rollback**: disable event subscription or env flags; tools fall back to simulation.

## Open Questions

- **DM parity**: same trigger path for **DM** `message` events or **app_mention** only in v1.
- **Helm layout**: nested `slack.trigger` / `slack.tools` vs flat keys—align with **`dedupe-helm-values-observability`** if merged first.
- **Idempotency**: `event_id` dedupe for trigger to avoid double-runs on Slack retries.
