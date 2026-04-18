# In-process MCP tools (`tools_impl`)

Tools are dispatched from `hosted_agents.tools_impl.dispatch.invoke_tool` when the tool id is allow-listed (`HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON`) and invoked via `POST /api/v1/trigger` (`tool` + `tool_arguments`) or the supervisor runtime.

<!-- Traceability: [DALC-REQ-JIRA-TOOLS-001] [DALC-REQ-JIRA-TOOLS-002] -->

## Slack tools

Runtime integration uses **`slack_sdk.WebClient`** with credentials from **`HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN`** only (Helm: `slackTools.botTokenSecretName` / `botTokenSecretKey`). This is **separate** from:

- **Scraper** tokens on CronJobs: `SLACK_BOT_TOKEN` / `SLACK_USER_TOKEN` (`scrapers.slack.auth`).
- **Slack trigger** (Events API / Socket Mode) verification secrets when that feature lands.

When the bot token env is **unset**, Slack tool calls use a **simulated** path (no network) so CI and local runs stay hermetic.

### OAuth scopes (typical bot)

Install the smallest set your product needs; common starting points:

| Capability | OAuth scope |
|------------|-------------|
| Post & update messages, thread replies | `chat:write` |
| Add / remove reactions | `reactions:write` |
| Read channel / thread history | `channels:history`, `groups:history`, `im:history`, `mpim:history` (as applicable) |

### Tool ids

| Tool id | Behavior |
|---------|----------|
| `slack.post_message` | `chat.postMessage`; optional `thread_ts` / `reply_to_ts` for replies |
| `slack.reactions_add` | `reactions.add`; args: `channel_id`, `timestamp` (or `ts`), `name` / `emoji` |
| `slack.reactions_remove` | `reactions.remove`; same args |
| `slack.chat_update` | `chat.update`; args: `channel_id`, `ts`, `text` |
| `slack.conversations_history` | `conversations.history`; optional `limit` |
| `slack.conversations_replies` | `conversations.replies`; args: `channel_id`, `thread_ts`; optional `limit` |

Limits are capped by **`HOSTED_AGENT_SLACK_TOOLS_HISTORY_LIMIT`** (default 50, max 200).

### Managed RAG

These tools **do not** call `POST /v1/embed` or ingest tool I/O into the managed RAG index.

### Smoke with `slack-trigger` (manual)

End-to-end validation needs **`openspec/changes/slack-trigger`** applied so `@mention` → `run_trigger_graph`, plus this chart values fragment:

1. Create a Secret with an `xoxb` token; set `slackTools.botTokenSecretName` / `botTokenSecretKey`.
2. Allow-list tools in `mcp.enabledTools` (e.g. `slack.post_message`, `slack.reactions_add`).
3. Deploy the agent **with** the Slack ingress/Socket Mode listener from `slack-trigger`.
4. Mention the bot; confirm threaded reply and reaction via real API (check Slack UI); verify agent logs/metrics show `agent_runtime_slack_tool_web_api_calls_total` without token material in stdout.

There is **no** requirement that the tools path call `/v1/embed`.

## Jira tools

| Tool id | Module | Notes |
|---------|--------|-------|
| `jira.search_issues` | `jira/` | Bounded JQL search (`jql`, optional `max_results`) |
| `jira.get_issue` | `jira/` | Fetch issue (`issue_key`, optional `fields[]`) |
| `jira.add_comment` | `jira/` | Add comment (`issue_key`, `body`) |
| `jira.transition_issue` | `jira/` | Transition (`issue_key`, `transition_id` or `transition_name`) |
| `jira.create_issue` | `jira/` | Create (`project_key`, `summary`, `issue_type`, optional `description`) |
| `jira.update_issue` | `jira/` | Update (`issue_key`, `fields` object) |

**Jira tools configuration** uses chart values `jiraTools` → environment prefix `HOSTED_AGENT_JIRA_TOOLS_*`. That is **separate** from scheduled scraper auth (`scrapers.jira.auth`) and from future Jira webhook trigger verification keys (`jira-trigger`). When `jiraTools.simulated` is true (default), or credentials are missing, implementations return structured **simulated** payloads and still emit side-effect checkpoints for mutations.

**Atlassian Cloud API tokens (recommended for tools)** map to Jira account email + API token using Basic HTTP auth (handled by `httpx`). Required Atlassian OAuth scopes for equivalent OAuth clients align with tool scopes: **read Jira** work items (search/read), **write Jira** work items (comment/create/update), and **transition** requires workflow transition permissions on the issues touched. Exact OAuth scope strings follow Atlassian’s product documentation for your OAuth app type; prefer API tokens for server-style agents unless OAuth is mandated.

These tools **do not** call `POST /v1/embed` or ingest tool I/O into the managed RAG index by default.
