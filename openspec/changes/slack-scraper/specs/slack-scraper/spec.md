## ADDED Requirements

### Requirement: [DALC-REQ-SLACK-SCRAPER-001] Slack scraper executes an operator-defined search list each run

The Slack scraper **SHALL** read an operator-supplied **ordered list of search definitions** and **SHALL** execute **every** definition **once** per scraper run, in list order, unless a step fails in a way that aborts the run as documented.

#### Scenario: All search steps succeed

- **WHEN** the Slack scraper starts with a valid non-empty search list and valid Slack credentials
- **THEN** it **SHALL** execute each search definition to completion for that run (subject to documented per-run limits)

#### Scenario: Invalid search list

- **WHEN** the search list is missing, empty, or fails structural validation
- **THEN** the scraper **SHALL** exit non-zero without calling Slack APIs for that list (beyond optional auth validation as documented)

### Requirement: [DALC-REQ-SLACK-SCRAPER-002] Slack scraper uses the Slack-maintained Python stack anchored on bolt-python

The Slack scraper **SHALL** perform Slack Web API calls using the **`slack_sdk`** client libraries **as published and versioned alongside the [bolt-python](https://github.com/slackapi/bolt-python/) project** (declare **`slack_sdk`** and **`slack-bolt`** in the runtime dependency set). The scraper **SHALL NOT** depend on undocumented private Slack APIs.

#### Scenario: Dependency declaration

- **WHEN** the runtime package metadata for the scraper image is rendered for release
- **THEN** it **SHALL** include **`slack_sdk`** and **`slack-bolt`** with pinned or lower-bounded versions consistent with the repository’s dependency policy

### Requirement: [DALC-REQ-SLACK-SCRAPER-003] New Slack messages are embedded into the managed RAG HTTP service

For **each** Slack message **selected** by the configured searches that is classified as **new or updated** for ingestion per the scraper’s documented dedupe rules, the scraper **SHALL** submit **at least one** textual chunk to the managed RAG service using **`POST /v1/embed`** with the same **`scope`** semantics as other scrapers (**`SCRAPER_SCOPE`**), and **SHALL** include stable **Slack-derived identifiers** in payload **metadata** (for example team id, channel id, message `ts`, permalink if available).

#### Scenario: Successful embed for a selected message

- **WHEN** a Slack message is selected and passes dedupe rules and `RAG_SERVICE_URL` points at a healthy RAG service
- **THEN** the scraper **SHALL** send a **`/v1/embed`** request that includes the normalized message text and the documented metadata keys

#### Scenario: RAG service error

- **WHEN** the RAG service returns a **5xx** or the request cannot be completed due to transport failure
- **THEN** the scraper **SHALL** classify the outcome using the same **result** taxonomy as existing scraper RAG submission metrics and **SHALL** surface failure without claiming success

### Requirement: [DALC-REQ-SLACK-SCRAPER-004] Slack scraper exposes standard scraper metrics with bounded integration labels

The Slack scraper **SHALL** expose scraper metrics consistent with existing scraper processes, including counters and histograms documented in the scraper metrics checklist, and **SHALL** use a **bounded** **`integration`** label value (default **`slack`** unless overridden by a documented, bounded operator setting such as **`SCRAPER_INTEGRATION`**).

#### Scenario: Successful run labels

- **WHEN** a Slack scraper run completes without uncaught exceptions and records a successful RAG submission for a selected message
- **THEN** metrics **SHALL** increment **`agent_runtime_scraper_runs_total{integration="<bounded>",result="success"}`** and **`agent_runtime_scraper_rag_submissions_total{integration="<bounded>",result="success"}`** for that integration label

### Requirement: [DALC-REQ-SLACK-SCRAPER-005] Secrets are never written to logs or metrics labels

The Slack scraper **SHALL** load Slack tokens and other secrets **only** from environment variables or mounted files provided by the platform, and **SHALL NOT** print secrets to stdout/stderr and **SHALL NOT** attach secrets to Prometheus metric labels.

#### Scenario: Debug logging

- **WHEN** debug logging is enabled for the scraper process
- **THEN** logs **SHALL** remain free of token values and **SHALL** redact or omit authorization headers
