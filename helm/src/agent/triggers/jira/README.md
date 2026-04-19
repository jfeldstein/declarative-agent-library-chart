# Jira trigger (`jira-trigger`)

<!-- Traceability: [DALC-REQ-JIRA-TRIGGER-002] [DALC-REQ-JIRA-TRIGGER-004] -->

Inbound **Jira Cloud webhooks** → hosted **`run_trigger_graph`** (same outcome as **`POST /api/v1/trigger`**), with **issue / project / event** context on **`TriggerContext`**. Verification uses a **shared operator secret** (constant-time compare). This path is **disjoint** from **`scrapers.jira`** and from **`HOSTED_AGENT_JIRA_TOOLS_*`** ([DALC-REQ-JIRA-TRIGGER-004]).

## Environment variables

| Variable | Purpose |
| --- | --- |
| `HOSTED_AGENT_JIRA_TRIGGER_ENABLED` | `1` / `true` to enable the bridge |
| `HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET` | Shared secret for verification (required when the HTTP route is active) |
| `HOSTED_AGENT_JIRA_TRIGGER_EVENT_DEDUPE` | `1` / `true` to dedupe retries using `X-Atlassian-Webhook-Identifier` |
| `HOSTED_AGENT_JIRA_TRIGGER_HTTP_PATH` | POST path (default `/api/v1/integrations/jira/webhook`) |

## Operator setup (Jira Cloud)

1. **Create a random secret** (store in Kubernetes Secret; reference via Helm `jiraTrigger.webhookSecretSecretName` / `webhookSecretSecretKey`).
2. In **Jira → System → WebHooks**, register your **public URL** including the secret Jira appends as a query parameter, **or** configure a reverse proxy that injects header **`X-Jira-Webhook-Secret`** with the same value.
3. Point the webhook at your ingress URL + default path (`/api/v1/integrations/jira/webhook`) unless you override `HOSTED_AGENT_JIRA_TRIGGER_HTTP_PATH`.
4. Enable delivery for the issue/comment events you need.

The runtime compares the configured secret to the **`secret`** query parameter first, then **`X-Jira-Webhook-Secret`** if the query is absent.

## Verification material

- **Shared secret:** must match **`HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET`** (never logged or exposed as metric labels).
- **Delivery identity:** optional header **`X-Atlassian-Webhook-Identifier`** is used for optional dedupe when `HOSTED_AGENT_JIRA_TRIGGER_EVENT_DEDUPE` is enabled.
