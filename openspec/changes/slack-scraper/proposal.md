## Why

Hosted agents need **up-to-date Slack context** in the shared RAG index so retrieval-augmented flows can answer questions about conversations, decisions, and links that live in Slack. The chart already supports scheduled scrapers and a managed RAG HTTP service, but there is **no first-party Slack scraper** that turns operator-defined recurring “searches” into embeddings. Adding one closes that gap while reusing the existing **`/v1/embed`** path agents already query.

## What Changes

- Introduce a **Slack scraper** job type (distinct from the reference fixture and generic stub) that runs on the existing **CronJob** scraper mechanism.
- Accept an operator-provided **ordered list of search definitions** executed on each scrape (for example Slack **`search.messages`** queries and/or bounded **`conversations.history`** windows against configured channel IDs), normalized into fetch units with stable keys for deduplication.
- For **new or updated** messages surfaced by those searches, **normalize text + metadata** and submit chunks to the **managed RAG HTTP API** so they become retrievable via existing agent **`/v1/query`** usage.
- Add **Python dependencies** aligned with the Slack-maintained stack described in **[bolt-python](https://github.com/slackapi/bolt-python/)** (notably **`slack_sdk`** / **`slack-bolt`** as documented for building Slack apps in Python) for token handling, pagination, and API calls; the scheduled job remains **non-interactive** (no requirement for Socket Mode or HTTP mode Bolt servers in-cluster unless we explicitly choose that for auth—design will pick the smallest surface).
- Extend **Helm values / schema** (under existing **`scrapers`**) so a Slack job can be enabled with **secrets references**, schedules, scopes, and the **search list** without reintroducing a top-level **`rag`** key (per **`cfha-rag-from-scrapers`**).
- Register **bounded `integration` metrics labels** (for example **`slack`**) consistent with existing scraper metric contracts.

## Capabilities

### New Capabilities

- `slack-scraper`: Operator-configured Slack searches on a schedule; fetch → normalize → dedupe → **`/v1/embed`** (with entity metadata where stable Slack ids exist: channel, thread ts, user, permalink).

### Modified Capabilities

- _(none at published `openspec/specs/*/spec.md` level in this change proposal; archiving may later fold requirements into a long-lived capability spec if maintainers want consolidation.)_

## Impact

- **Runtime**: new module under `hosted_agents.scrapers` (or parallel package) plus dependency additions in the runtime image build (`pyproject`/lockfile).
- **Helm**: `values.yaml`, `values.schema.json`, and `scraper-cronjobs.yaml` (or equivalent) to route **`SCRAPER_INTEGRATION=slack`** (name TBD in design) to the new entrypoint; optional **`Secret`** volume/env wiring pattern consistent with other integrations.
- **Docs / examples**: example values fragment showing a **list of searches** and RAG-enabled Slack job.
- **Security**: Slack bot/user tokens via Kubernetes secrets; least-privilege OAuth scopes documented.
- **CI**: unit tests for normalization/idempotency; possible extension to integration smoke if fixtures exist.
