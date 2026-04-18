## Why

Users need to **@mention the Slack app** and have that event **start a hosted agent run** the same way **`POST /api/v1/trigger`** does. That path is **inbound only**: verify Slack’s delivery (URL challenge, signing secret, or Socket Mode), normalize the payload, and **pipe** it into **`run_trigger_graph`**. It is **not** a scraper (no cron, no **`/v1/embed`**). **Outbound** Slack actions (react, reply, read history) belong in the separate **`slack-tools`** change.

## What Changes

- Accept **`app_mention`** (and transport-specific verification) from Slack’s servers.
- Forward normalized **channel / thread / text** context into the **hosted trigger pipeline** (internal call or documented equivalent to **`POST /api/v1/trigger`**).
- **Helm/env** for trigger-only secrets (signing secret, Socket Mode app token, etc.) **documented as distinct** from **`scrapers`** and from **Slack tools** token keys.
- **Non-goal**: Implementing **`slack_sdk`** chat tools here—that is **`slack-tools`**.

## Capabilities

### New Capabilities

- `slack-trigger`: Inbound **Slack → hosted trigger** bridge for **`app_mention`** plus URL challenge / request verification as required by the transport.

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level.)_

## Impact

- **Runtime**: HTTP route and/or Socket Mode listener; payload → **`TriggerBody`** / **`run_trigger_graph`**.
- **Helm**: values/env for trigger listener and verification material (disjoint from scraper and from tools—see **`openspec/changes/slack-tools/`** for tools-side config).
- **Related change**: **`openspec/changes/slack-tools/`** — LLM-time Web API tools so the triggered run can respond in Slack.
