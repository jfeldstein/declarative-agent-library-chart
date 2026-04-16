# Example: `with-scrapers`

<!-- Traceability: [DALC-REQ-EXAMPLE-VALUES-FILES-001] [DALC-REQ-EXAMPLE-VALUES-FILES-002] [DALC-REQ-HELM-UNITTEST-004] -->

Application chart demonstrating **`scrapers.jira`** and **`scrapers.slack`** with `enabled` plus `jobs[]`.

## Values files

| File | Use when |
|------|----------|
| **`values.yaml`** (default) | You want the **full** walkthrough: multiple Jira and Slack jobs (mixed sources), matching the primary CI unittest path for scraper + RAG rendering. |
| **`values.jira-only.yaml`** | You only run **Jira** scrapers (`slack.enabled: false`); one enabled JQL job; still deploys **RAG** and one **CronJob** + **ConfigMap**. |
| **`values.slack-only.yaml`** | You only run **Slack** Real-time Search (`jira.enabled: false`); one `slack_search` job; still deploys **RAG** and one **CronJob** + **ConfigMap**. |

### Behavior notes (all files)

- Each **enabled** job under an **enabled** parent gets a **ConfigMap** (`job.json`) and a **CronJob** on `schedule`. Non-secret fields live in the ConfigMap; tokens use `auth.*SecretName` → env `valueFrom`.
- **Jira** — `source: jira`, `query` (JQL). Site URL, watermark dir, and auth live under `scrapers.jira`; optional numeric `defaults` merge into `job.json`.
- **Slack** — `source: slack_search` (Real-time Search + `conversations.replies` / `conversations.history`; needs user token) or `source: slack_channel` (`conversationId` + incremental history under `stateDir`; needs bot token).
- Unknown `source` values cause the scraper process to exit non-zero (CrashLoop).
- At least one **enabled** job under an **enabled** parent deploys the managed **RAG** Deployment and Service.

When adding a scraper source, update: the values files here, `helm/tests/with_scrapers_test.yaml`, `grafana/dalc-overview.json`, and `helm/chart/templates/scraper-*.yaml`.

## Install

From this directory (after [cloning the repo](../../README.md)):

```bash
helm dependency build --skip-refresh
```

**Default** (`values.yaml`):

```bash
helm upgrade --install with-scrapers . -n default --wait
```

**Jira-only** or **Slack-only** setups (extra `-f` after the chart path):

```bash
helm upgrade --install with-scrapers . -n default --wait -f values.jira-only.yaml
helm upgrade --install with-scrapers . -n default --wait -f values.slack-only.yaml
```

Build or load the agent image as described in the repository root [README](../../README.md) (for example `declarative-agent:local` on kind).
