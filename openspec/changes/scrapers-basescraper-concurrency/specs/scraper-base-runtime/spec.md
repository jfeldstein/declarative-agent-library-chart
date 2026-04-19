## ADDED Requirements

### Requirement: [DALC-REQ-SCRAPER-BASE-001] Shared scraper runtime owns lifecycle, RAG ingest, and incremental persistence

The Python package **`hosted_agents.scrapers`** SHALL provide a documented **shared runtime** (implemented in a coordinator module such as **`base.py`** alongside **`typing.Protocol`** / ABC definitions) that owns **`job.json`** loading, environment validation, optional **metrics HTTP** listener lifecycle, **all** managed RAG **`POST /v1/embed`** requests for the process (sole ingest path to the RAG HTTP API), **cursor / watermark** persistence via **`cursor_store`** (including when state advances relative to embed success), process exit codes on fatal misconfiguration, and graceful shutdown hooks.

Integration-specific modules SHALL **not** implement embed submission or durable incremental persistence themselves.

#### Scenario: Entrypoint stability

- **WHEN** the chart invokes **`python -m hosted_agents.scrapers.jira_job`** or **`python -m hosted_agents.scrapers.slack_job`**
- **THEN** the module **`run()`** or equivalent SHALL remain the supported entrypoint and SHALL delegate orchestration to this shared runtime after this change

#### Scenario: RAG ingest is centralized

- **WHEN** a scraper run produces normalized chunks ready for indexing
- **THEN** only the shared runtime SHALL send those chunks to the managed RAG service using **`POST /v1/embed`** (or its documented successor path)

### Requirement: [DALC-REQ-SCRAPER-BASE-002] Integration adapters return data only

Integration-specific scraper code (Jira, Slack, or future sources) SHALL be responsible only for **authenticated remote API interaction**, **pagination**, **rate-limit handling** as documented, and **mapping** remote payloads into **in-memory** structures ready for embedding (deterministic **`entity_id`**, **`items[]`**, **`relationships`** where applicable).

It SHALL **NOT** invoke the managed RAG **embed** HTTP API, **NOT** write **cursor / watermark** or other incremental persistence, **NOT** configure the scraper **Prometheus** registry or metrics HTTP server, and **NOT** duplicate **bounded `integration`** label logic.

It MAY return **proposed persistence updates** (for example a candidate next watermark) as plain data for the runtime; the runtime SHALL commit such state only according to documented **post-embed** / **batch success** rules.

#### Scenario: No direct RAG calls from integration code

- **WHEN** integration-specific code runs as part of a scraper job
- **THEN** it SHALL NOT issue HTTP requests to the RAG service’s **`/v1/embed`** endpoint (or equivalent)

#### Scenario: Deterministic identifiers unchanged

- **WHEN** an integration adapter yields normalized chunks for a run
- **THEN** **`entity_id`** and metadata keys SHALL follow the same deterministic rules as documented for that integration prior to this refactor (unless a separate **BREAKING** change explicitly updates them)

### Requirement: [DALC-REQ-SCRAPER-BASE-003] Bounded observability labels preserved

The shared runtime SHALL enforce the existing **bounded `integration` label** behavior for Prometheus metrics (including sanitization/truncation per **`metrics.py`**) for all integrations using the abstraction, so adapters cannot accidentally emit unbounded label values.

#### Scenario: Label contract

- **WHEN** **`SCRAPER_INTEGRATION`** or an operator override supplies a long or unusual string
- **THEN** scraper metrics SHALL still record **`integration`** using the bounded label mapping documented for scrapers
