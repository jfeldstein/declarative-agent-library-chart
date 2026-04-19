## ADDED Requirements

### Requirement: [DALC-REQ-SCRAPER-BASE-001] Shared scraper runtime owns process lifecycle

The Python package **`hosted_agents.scrapers`** SHALL provide a documented **shared runtime** (for example a **`BaseScraper`** abstract type or **`ScraperRuntime`** coordinator plus a **`typing.Protocol`** for integrations) that implements **`job.json`** loading, environment validation, optional **metrics HTTP** listener lifecycle, **RAG** **`POST /v1/embed`** submission with the existing result taxonomy, **cursor / watermark** coordination via **`cursor_store`**, process exit codes on fatal misconfiguration, and graceful shutdown hooks. Integration-specific modules SHALL delegate those concerns to this runtime rather than reimplementing them.

#### Scenario: Entrypoint stability

- **WHEN** the chart invokes **`python -m hosted_agents.scrapers.jira_job`** or **`python -m hosted_agents.scrapers.slack_job`**
- **THEN** the module **`run()`** or equivalent SHALL remain the supported entrypoint and SHALL route execution through the shared runtime after this change

### Requirement: [DALC-REQ-SCRAPER-BASE-002] Integration adapters focus on remote calls and normalization

Integration-specific scraper code (Jira, Slack, or future sources) SHALL be responsible only for **authenticated remote API interaction**, **pagination**, **rate-limit handling** as documented, and **mapping** remote payloads into the repository’s **normalized embed contract** (deterministic **`entity_id`**, **`items[]`**, **`relationships`** where applicable). It SHALL NOT duplicate metrics registry setup, scraper **`integration`** label normalization, or generic RAG HTTP client wiring except through the shared runtime.

#### Scenario: Deterministic identifiers unchanged

- **WHEN** a scraper adapter emits chunks for RAG ingestion
- **THEN** **`entity_id`** and metadata keys SHALL follow the same deterministic rules as documented for that integration prior to this refactor (unless a separate **BREAKING** change explicitly updates them)

### Requirement: [DALC-REQ-SCRAPER-BASE-003] Bounded observability labels preserved

The shared runtime SHALL enforce the existing **bounded `integration` label** behavior for Prometheus metrics (including sanitization/truncation per **`metrics.py`**) for all integrations using the abstraction, so adapters cannot accidentally emit unbounded label values.

#### Scenario: Label contract

- **WHEN** **`SCRAPER_INTEGRATION`** or an operator override supplies a long or unusual string
- **THEN** scraper metrics SHALL still record **`integration`** using the bounded label mapping documented for scrapers
