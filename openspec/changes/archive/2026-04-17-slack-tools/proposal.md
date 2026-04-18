## Why

When a run is started (including from **`openspec/changes/slack-trigger/`**), the agent needs **Slack Web API** operations to **acknowledge and respond**: reactions, threaded posts, updates, and **bounded** history reads. That is **LLM-time** tool dispatch via **`tools_impl`**, not cron scrapers and **not** automatic RAG ingestion.

## What Changes

- Allowlisted **tool ids** backed by **`slack_sdk.WebClient`** (post, thread reply, reactions, update, read history with caps).
- **Credentials and Helm keys** for tools **documented as distinct** from **`scrapers`** and from **Slack trigger** verification tokens.
- **Non-goal**: Subscribing to Slack events or **`app_mention`** ingress—that is **`slack-trigger`**.

## Capabilities

### New Capabilities

- `slack-tools`: **Runtime tools** for Slack **write/read** during an agent invocation; no default **`/v1/embed`**.

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level.)_

## Impact

- **Runtime**: **`hosted_agents.tools_impl`** modules + **`dispatch`** registration; optional gate on existing simulated **`slack.post_message`** when a real token is configured.
- **Helm**: env for bot token and related tool settings (disjoint from scraper and trigger—see **`openspec/changes/slack-trigger/`**).
- **Related change**: **`openspec/changes/slack-trigger/`** — inbound **`@mention`** → trigger pipeline.
