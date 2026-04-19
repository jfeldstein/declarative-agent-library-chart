## ADDED Requirements

### Requirement: [DALC-REQ-RAG-SCRAPERS-005] Scraper CronJob concurrency policy is operator-tunable per job

For each rendered scraper **CronJob** under **`scrapers.jira.jobs`** and **`scrapers.slack.jobs`**, the Helm chart SHALL set **`spec.concurrencyPolicy`** from operator values when provided, and SHALL default to **`Forbid`** when omitted, matching the previous chart behavior. Allowed values SHALL be those accepted by Kubernetes **`batch/v1` `CronJob` `concurrencyPolicy`** at the chart’s targeted Kubernetes version (**`Forbid`**, **`Allow`**, **`Replace`**). The chart SHALL NOT place this field inside mounted **`job.json`** (it is Helm-only configuration, like **`schedule`**).

#### Scenario: Default remains Forbid

- **WHEN** a scraper job entry omits **`concurrencyPolicy`**
- **THEN** rendered **CronJob** **`spec.concurrencyPolicy`** SHALL be **`Forbid`**

#### Scenario: Operator selects Allow

- **WHEN** an operator sets **`concurrencyPolicy: Allow`** on a scraper job entry and the value is valid
- **THEN** the rendered **CronJob** **`spec.concurrencyPolicy`** SHALL be **`Allow`**
