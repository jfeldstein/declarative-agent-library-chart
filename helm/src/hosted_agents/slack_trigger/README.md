# Slack trigger bridge (`slack-trigger`)

Inbound **`app_mention`** events from Slack are verified (HTTP Events API and/or Socket Mode) and forwarded into **`run_trigger_graph`**, equivalent to **`POST /api/v1/trigger`**. Outbound Slack actions use **`slack-tools`** (`HOSTED_AGENT_SLACK_TOOLS_*`), not this module.

## Environment variables (distinct from scrapers and Slack tools)

| Variable | Purpose |
|----------|---------|
| `HOSTED_AGENT_SLACK_TRIGGER_ENABLED` | `1` / `true` to enable the bridge |
| `HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET` | Signing secret for **HTTP Event Subscriptions** (request verification) |
| `HOSTED_AGENT_SLACK_TRIGGER_APP_TOKEN` | App-level token (`xapp-…`) for **Socket Mode** |
| `HOSTED_AGENT_SLACK_TRIGGER_BOT_TOKEN` | Bot token (`xoxb-…`) for the Slack Bolt app (Socket Mode listener) |
| `HOSTED_AGENT_SLACK_TRIGGER_SOCKET_MODE` | `1` / `true` to start the Socket Mode listener (requires app + bot token) |
| `HOSTED_AGENT_SLACK_TRIGGER_EVENT_DEDUPE` | `1` / `true` to dedupe HTTP retries using envelope `event_id` |
| `HOSTED_AGENT_SLACK_TRIGGER_HTTP_PATH` | HTTP POST path (default `/api/v1/integrations/slack/events`) |

**Scraper** CronJobs use `SLACK_BOT_TOKEN` / `SLACK_USER_TOKEN` under `scrapers.slack.auth`. **Slack tools** use `HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN`. Do not reuse those env names for trigger secrets.

## Slack app setup

1. Create a Slack app and enable **Event Subscriptions** (HTTP) and/or **Socket Mode** under **Settings → Install App**.
2. Subscribe to bot events: **`app_mention`**.
3. OAuth scopes: include **`app_mentions:read`** (and **`chat:write`** only if you use **slack-tools** for replies).
4. **HTTP**: set the Request URL to your ingress URL + `HOSTED_AGENT_SLACK_TRIGGER_HTTP_PATH`, using the signing secret from **Basic Information → Signing Secret**.
5. **Socket Mode**: enable Socket Mode, create an **App-Level Token** with `connections:write`, and set `HOSTED_AGENT_SLACK_TRIGGER_APP_TOKEN`; set `HOSTED_AGENT_SLACK_TRIGGER_BOT_TOKEN` to the bot user OAuth token.

## Helm

See chart `slackTrigger` values in `helm/chart/values.yaml` (wired in `_manifest_deployment.tpl`).
