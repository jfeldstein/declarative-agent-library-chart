## ADDED Requirements

### Requirement: [DALC-REQ-JIRA-SCRAPER-001] Chart exposes structured `scrapers.jira` values

The Helm chart SHALL publish a **`scrapers.jira`** object in **`values.yaml`** and **`values.schema.json`** for operator-tunable Jira Cloud scraping, including at minimum **`siteUrl`**, **authentication via Secret references**, **`defaults`** for run caps and overlap, and a **`jobs`** list whose entries include **`schedule`**, **`source`** (`jira`), and **`query`** (JQL), without introducing a top-level **`rag`** property.

#### Scenario: Schema documents scrapers.jira

- **WHEN** an operator inspects **`values.schema.json`**
- **THEN** **`properties.scrapers.properties`** SHALL include a documented **`jira`** object suitable for validating **`siteUrl`**, secret-backed credentials, **`jobs[].query`**, and related job fields

### Requirement: [DALC-REQ-JIRA-SCRAPER-002] Jira scraper job routes to `jira_job` by integration

When a scraper CronJob is configured for the Jira integration (**`SCRAPER_INTEGRATION`** **`jira`** and **`source: jira`** in **`job.json`**), the chart SHALL invoke **`agent.scrapers.jira_job`** as the container entrypoint module (or a documented successor).

#### Scenario: Enabled Jira integration uses jira entrypoint

- **WHEN** `helm template` renders an enabled scraper job for Jira
- **THEN** the scraper container command SHALL target **`agent.scrapers.jira_job`**

### Requirement: [DALC-REQ-JIRA-SCRAPER-003] Incremental Jira sync uses JQL on `updated` with a persisted watermark

The Jira scraper SHALL discover candidate issues using Jira Cloud **enhanced JQL search** (`POST /rest/api/3/search/jql` or the documented successor) with a query that includes **`updated >= <watermark>`** (including a configurable **overlap** window), SHALL paginate until **caps** or end of result set, and SHALL advance a **durable per-scope watermark** only after a successful RAG embed for the processed batch (or SHALL document and implement an equivalent atomicity strategy that prevents permanent data loss on partial failure).

#### Scenario: Watermark narrows JQL

- **WHEN** a watermark **W** is stored for scope **S** and overlap **O** minutes is configured
- **THEN** the scraper SHALL issue JQL that restricts issues to those with **`updated`** not earlier than **W minus O** (expressed in UTC per Jira JQL rules) before fetching details

### Requirement: [DALC-REQ-JIRA-SCRAPER-004] Issue payload includes status, assignee, links, and paginated comments

For each candidate issue, the scraper SHALL retrieve **status**, **assignee**, **issue links** (`issuelinks`), and **all comments** (via **`GET /rest/api/3/issue/{issueIdOrKey}/comment`** pagination or a documented equivalent that returns full bodies), SHALL honor operator-configured **`extraFields`** when present, and SHALL normalize this material into one or more RAG **`items[]`** entries with a deterministic **`entity_id`** derived from the **issue key** (and optional suffixed chunk ids in **metadata** when splitting).

#### Scenario: Linked issues appear in normalized output

- **WHEN** an issue contains **`issuelinks`** referencing at least one other issue
- **THEN** the normalized text and/or **`relationships`** payload submitted to **`POST /v1/embed`** SHALL include each linked issue’s **key** and **relationship type** (inward/outward as applicable)

#### Scenario: Long comment threads are fully read up to cap

- **WHEN** an issue has more comments than a single comments page returns
- **THEN** the scraper SHALL follow Jira’s comments pagination until all comments are retrieved **or** the configured **max comments per issue** cap is reached, and SHALL record truncation explicitly in the normalized text if capped

### Requirement: [DALC-REQ-JIRA-SCRAPER-005] Secrets and metrics stay bounded

The Jira scraper SHALL NOT print **credentials** or **Authorization** headers to logs, SHALL NOT place unbounded values (issue keys, project keys, custom strings) into **Prometheus label values**, and SHALL use the **`integration`** label contract documented for scrapers (bounded string **`jira`** unless the repository documents a wider allowlist for **`SCRAPER_INTEGRATION`**).

#### Scenario: Unknown integration label remains bounded

- **WHEN** metrics are emitted for a Jira scraper run
- **THEN** the **`integration`** label value SHALL be **`jira`** for the default configuration path described in **`metrics.py`**
