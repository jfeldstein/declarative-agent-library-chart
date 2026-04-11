## ADDED Requirements

### Requirement: Scrapers run on a schedule

The platform SHALL run **scrapers** as **scheduled jobs** using **cron** (or semantically equivalent scheduling, such as Kubernetes `CronJob` schedules). Each enabled scraper instance SHALL execute on its configured schedule until disabled.

#### Scenario: Scheduled execution

- **WHEN** a scraper is enabled and its cron expression indicates a run time
- **THEN** the platform SHALL start an execution of that scraper’s logic at that time (subject to platform skew and backoff policies)

### Requirement: Scrapers integrate with external services per configuration

Each scraper type SHALL define the **configuration fields** required to perform its work against an external system (for example: Slack channel IDs, Google Doc identifiers, JIRA project keys). The operator SHALL enable or disable scraper instances via configuration so that **not every agent deployment** runs every scraper type.

#### Scenario: Selective enablement

- **WHEN** values list only a subset of scraper types as enabled for a given deployment
- **THEN** the platform SHALL not run disabled scrapers and SHALL run only configured enabled scrapers on their schedules

#### Scenario: Integration-specific configuration

- **WHEN** a Slack (or Docs, or JIRA, or other supported) scraper is enabled with valid configuration for that integration
- **THEN** the scraper SHALL fetch or crawl the configured resources according to that type’s contract and SHALL handle transient errors with retry or backoff as defined by implementation documentation

### Requirement: Scrapers feed the shared RAG service

Scrapers that produce textual or chunkable content for retrieval SHALL send that content to the **managed RAG HTTP service** via **`/embed`** (or a documented batch variant) so that **agents and other components** can retrieve it via **`/query`**.

When the integration exposes **stable object identities** and **links** (for example issue keys, parent epics, thread ids, document hierarchy), the scraper SHALL include **entity** and **relationship** declarations in ingest payloads as required by **`runtime-rag-http`**, so relationship-aware retrieval is populated from real source structure rather than only inferred text.

#### Scenario: Ingestion path

- **WHEN** a scraper successfully retrieves new or updated content from its integration
- **THEN** it SHALL submit that content for embedding through the RAG service such that **`/query`** can return it when relevant

#### Scenario: Structured links forwarded to RAG

- **WHEN** a scraper run materializes content that belongs to a known entity **E** and the source API provides a link to another entity **F** with a known relationship type (for example parent issue, thread root, or containing folder)
- **THEN** the scraper SHALL send **E**, **F**, and the typed relationship to the RAG service on ingest so that **`/query`** can expand or filter using that edge

### Requirement: Scraper workloads expose Prometheus metrics

Each scraper **process** (for example the container invoked by a `CronJob`) SHALL expose **`/metrics`** and SHALL register at minimum:

- Counter **`agent_runtime_scraper_runs_total`** labeled **`integration`** and **`result`**, where **`integration`** is one of a **bounded, documented** set of integration type names (for example `slack`, `google_docs`, `jira`) and **`result`** is one of **`success`**, **`error`**.
- Histogram **`agent_runtime_scraper_run_duration_seconds`** labeled **`integration`** (same bounded set).
- Counter **`agent_runtime_scraper_rag_submissions_total`** labeled **`integration`** and **`result`**, counting **attempts** to submit ingested material to the RAG **`/embed`** path (or documented batch equivalent), with **`result`** in **`success`**, **`client_error`**, **`server_error`** using the same mapping as **`runtime-rag-http`** metrics.

Implementations SHALL NOT label metrics with channel ids, document ids, issue keys, or other unbounded identifiers.

#### Scenario: Successful scraper run

- **WHEN** a scraper run completes without uncaught exceptions and submits new content to RAG successfully
- **THEN** **`agent_runtime_scraper_runs_total{integration="<type>",result="success"}`** and **`agent_runtime_scraper_rag_submissions_total{integration="<type>",result="success"}`** SHALL increase for that integration type **`<type>`**

#### Scenario: RAG submission failure

- **WHEN** a scraper receives **5xx** from RAG during ingest for a given integration type
- **THEN** **`agent_runtime_scraper_rag_submissions_total`** SHALL record **`result="server_error"`** for that **`integration`**
