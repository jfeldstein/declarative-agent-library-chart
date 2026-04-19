## ADDED Requirements

### Requirement: [DALC-REQ-RAG-SCRAPERS-001] No top-level `rag` values key

The Declarative Agent Library Helm chart SHALL NOT define a top-level **`rag`** key in its published **`values.yaml`** or **`values.schema.json`**. RAG workload configuration that remains operator-tunable SHALL live only under documented keys nested beneath **`scrapers`**.

#### Scenario: Schema excludes top-level rag

- **WHEN** an operator inspects `values.schema.json` for the chart
- **THEN** the root `properties` SHALL NOT include a property named `rag`

### Requirement: [DALC-REQ-RAG-SCRAPERS-002] Managed RAG workload is deployed when any scraper job is enabled

The chart SHALL render the managed RAG HTTP **Deployment** and **Service** (names and selectors as documented for the chart) **if and only if** **`scrapers.jira.enabled`** or **`scrapers.slack.enabled`** is **true** and the corresponding **`jobs`** list contains **at least one** job with **`enabled: true`** (when **`enabled`** is omitted on a job, it SHALL be treated as **true**). If both parents are **false** or every job has **`enabled: false`**, the chart SHALL NOT render those RAG workload resources.

#### Scenario: Single enabled scraper deploys RAG

- **WHEN** `scrapers.jira.enabled` is `true` and `scrapers.jira.jobs` contains one job with `enabled: true` and `helm template` is run
- **THEN** the output SHALL include the RAG Deployment and RAG Service resources

#### Scenario: All scrapers disabled skips RAG

- **WHEN** both `scrapers.jira.enabled` and `scrapers.slack.enabled` are `false`, or every job under enabled parents has `enabled: false`
- **THEN** the output SHALL NOT include the RAG Deployment or RAG Service resources

### Requirement: [DALC-REQ-RAG-SCRAPERS-003] RAG tunables are nested under `scrapers.ragService`

The chart SHALL expose **`scrapers.ragService`** for operator tuning of the managed RAG workload: at minimum **replica count**, **Service type and port**, and **Pod resources**, with defaults equivalent to the chart’s prior RAG defaults documented in the migration note for this change.

#### Scenario: Operator sets RAG service port

- **WHEN** an operator sets `scrapers.ragService.service.port` to a valid TCP port and at least one scraper job is enabled
- **THEN** rendered RAG Service and container `containerPort` SHALL use that port

### Requirement: [DALC-REQ-RAG-SCRAPERS-004] Cluster-internal RAG base URL follows RAG deployment

The chart SHALL populate the cluster-internal RAG base URL (for example the helper used for **`HOSTED_AGENT_RAG_BASE_URL`** and scraper **`RAG_SERVICE_URL`**) with a non-empty URL **when and only when** the RAG workload is deployed per the scraper gate above; otherwise it SHALL be empty or unset as documented.

#### Scenario: No enabled scrapers yields no internal RAG URL

- **WHEN** no scraper job is enabled under `scrapers.jira` / `scrapers.slack` per [DALC-REQ-RAG-SCRAPERS-002]
- **THEN** the agent Deployment SHALL not receive a non-empty RAG base URL from this helper (consistent with no RAG Service)

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
