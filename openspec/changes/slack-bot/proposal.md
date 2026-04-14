## Why

Hosted agents need **Slack as a live channel**: users **@mention the bot** to start a run, and the running agent needs **Slack Web API tools** to **acknowledge and respond** (react, thread, update, read context) **during** that run. Those two concerns differ: **inbound delivery** from Slack’s servers is a **trigger** problem (verify, normalize, call the hosted trigger pipeline), while **outbound / read** behavior is a **tools** problem (allowlisted tool ids backed by `slack_sdk`). **Slack-oriented RAG scrapers** remain the wrong place for either; they target **cron + `/v1/embed`**, not **mention → trigger** or **LLM-time** chat actions.

## What Changes

- **`slack-trigger`**: When a user **@tags the bot**, accept Slack **`app_mention`** (and documented URL verification / signing behavior for the chosen topology) and **pipe** the normalized payload into the existing **hosted trigger** path (same outcome as **`POST /api/v1/trigger`** / **`run_trigger_graph`**), including enough **channel / thread / text** context for the agent to act.
- **`slack-tools`**: Allowlisted **runtime tools** so a **triggered** agent can **ack and respond** to the ping: reactions, threaded replies, message post/update, and **bounded** channel/thread history reads—**without** treating that traffic as **RAG ingestion** by default.
- **Configuration**: **Secrets and Helm keys** documented so **Slack scraper** (CronJob → RAG) stays disjoint from **Slack trigger** (events in) and **Slack tools** (Web API out); overlap is allowed only where explicitly documented (for example one Slack app with one bot token used for both tools and trigger **if** the design chooses that), but **never** with scraper-only secrets.
- **Non-goals**: No requirement that **Slack tools** or **Slack trigger** automatically call **`POST /v1/embed`** unless a future change says so.

## Capabilities

### New Capabilities

- `slack-trigger`: Inbound **Slack → hosted trigger** bridge for **`app_mention`** (and URL challenge / request verification as required by the transport); forwards into the **trigger endpoint semantics** so the supervisor run starts like any other trigger.
- `slack-tools`: **LLM-time** Slack Web API surface (post, thread, react, update, read history) invoked via existing **tool dispatch**; **not** RAG/scraper lifecycle; credentials/config **distinct from scraper** keys.

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level; behavior is additive and scoped to this change’s specs.)_

## Impact

- **Runtime**: trigger-side listener or HTTP route (Socket Mode **or** Events API) plus **`slack_sdk`**-backed tool modules and **`tools_impl.dispatch`** registration.
- **Helm**: separate value subtrees or env for **trigger** (signing secret, Socket Mode app token if used) vs **tools** (bot token, etc.) vs **`scrapers`**; docs for operators.
- **Security**: verify Slack requests on the trigger path; least-privilege OAuth scopes split **trigger subscription** vs **tool** needs; no secrets in logs or metric labels.
- **CI**: unit tests for verification, payload mapping, and mocked WebClient tool paths.
