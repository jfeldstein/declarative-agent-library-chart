## Why

Hosted agents need **Jira as a live system of record**: **webhooks or automation** should be able to **start a run** when work changes (issue updated, comment added, transition), and the running agent needs **Jira REST tools** to **read and mutate issues** **during** that run. Those two concerns differ: **inbound delivery** from Jira (or the Atlassian proxy) is a **trigger** problem (verify, normalize, call the hosted trigger pipeline), while **issue CRUD / search / transition** during the graph is a **tools** problem (allowlisted tool ids backed by **`httpx`** or a documented REST client). **Jira-oriented RAG scrapers** (`jira-scraper`, CronJob → **`/v1/embed`**) remain the wrong place for either; they target **scheduled ingestion**, not **webhook → trigger** or **LLM-time** Jira actions.

## What Changes

- **`jira-trigger`**: When Jira delivers a **documented webhook** (or successor) payload to the runtime, accept it only after **documented verification**, map it into the existing **hosted trigger** path (same functional outcome as **`POST /api/v1/trigger`** / **`run_trigger_graph`**), including enough **issue key**, **project**, **event type**, and **human-readable summary or comment text** (as available) for **`TriggerBody.message`** and downstream context.
- **`jira-tools`**: Allowlisted **runtime tools** so a **triggered** agent can **inspect and update Jira**: bounded search/read, comments, transitions, and scoped create/update—**without** treating that traffic as **RAG ingestion** by default.
- **Configuration**: **Secrets and Helm keys** documented so **Jira scraper** (**`scrapers.jira`**, CronJob → RAG) stays disjoint from **Jira trigger** (webhooks in) and **Jira tools** (REST out); overlap is allowed only where explicitly documented (for example one OAuth client or API token pair **if** the design chooses that), but **never** with scraper-only secret fields required for the other paths.
- **Non-goals**: No requirement that **Jira tools** or **Jira trigger** automatically call **`POST /v1/embed`** unless a future change says so.

## Capabilities

### New Capabilities

- `jira-trigger`: Inbound **Jira → hosted trigger** bridge for **operator-selected webhook events** (and verification as required by the transport); forwards into **trigger endpoint semantics** so the supervisor run starts like any other trigger.
- `jira-tools`: **LLM-time** Jira Cloud REST surface (read/search/comment/transition/create within configured scopes) invoked via existing **tool dispatch**; **not** RAG/scraper lifecycle; credentials/config **distinct from scraper** keys.

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level; behavior is additive and scoped to this change’s specs. The draft **`tools.jira`** shape in chart values may later be split or aliased into trigger vs tools sub-objects when implemented.)_

## Impact

- **Runtime**: HTTP route for Jira webhooks (or documented ingress path) plus Jira REST-backed **`tools_impl`** modules and **`tools_impl.dispatch`** registration.
- **Helm**: separate value subtrees or env for **trigger** (webhook signing secret, optional Connect/JWT settings if used) vs **tools** (API token / OAuth client for REST) vs **`scrapers.jira`**; docs for operators.
- **Security**: verify Jira requests on the trigger path; least-privilege scopes split **webhook subscription** vs **tool** needs; no secrets in logs or metric labels.
- **CI**: unit tests for verification, payload mapping, and mocked REST tool paths.
