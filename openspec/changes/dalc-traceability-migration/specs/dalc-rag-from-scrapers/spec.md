## MODIFIED Requirements

### Requirement: [DALC-REQ-RAG-SCRAPERS-001] No top-level `rag` values key

The Declarative Agent Library Helm chart SHALL NOT define a top-level **`rag`** key in its published **`values.yaml`** or **`values.schema.json`**. RAG workload configuration that remains operator-tunable SHALL live only under documented keys nested beneath **`scrapers`**.

#### Scenario: Schema excludes top-level rag

- **WHEN** an operator inspects `values.schema.json` for the chart
- **THEN** the root `properties` SHALL NOT include a property named `rag`

### Requirement: [DALC-REQ-RAG-SCRAPERS-002] Managed RAG workload is deployed when any scraper job is enabled

The chart SHALL render the managed RAG HTTP **Deployment** and **Service** (names and selectors as documented for the chart) **if and only if** the **`scrapers.jobs`** list contains **at least one** job object with **`enabled: true`**. If there are no jobs or every job has **`enabled: false`**, the chart SHALL NOT render those RAG workload resources.

#### Scenario: Single enabled scraper deploys RAG

- **WHEN** `scrapers.jobs` contains one job with `enabled: true` and `helm template` is run
- **THEN** the output SHALL include the RAG Deployment and RAG Service resources

#### Scenario: All scrapers disabled skips RAG

- **WHEN** `scrapers.jobs` is empty or every job has `enabled: false`
- **THEN** the output SHALL NOT include the RAG Deployment or RAG Service resources

### Requirement: [DALC-REQ-RAG-SCRAPERS-003] RAG tunables are nested under `scrapers.ragService`

The chart SHALL expose **`scrapers.ragService`** for operator tuning of the managed RAG workload: at minimum **replica count**, **Service type and port**, and **Pod resources**, with defaults equivalent to the chart’s prior RAG defaults documented in the migration note for this change.

#### Scenario: Operator sets RAG service port

- **WHEN** an operator sets `scrapers.ragService.service.port` to a valid TCP port and at least one scraper job is enabled
- **THEN** rendered RAG Service and container `containerPort` SHALL use that port

### Requirement: [DALC-REQ-RAG-SCRAPERS-004] Cluster-internal RAG base URL follows RAG deployment

The chart SHALL populate the cluster-internal RAG base URL (for example the helper used for **`HOSTED_AGENT_RAG_BASE_URL`** and scraper **`RAG_SERVICE_URL`**) with a non-empty URL **when and only when** the RAG workload is deployed per the scraper gate above; otherwise it SHALL be empty or unset as documented.

#### Scenario: No enabled scrapers yields no internal RAG URL

- **WHEN** no scraper job is enabled
- **THEN** the agent Deployment SHALL not receive a non-empty RAG base URL from this helper (consistent with no RAG Service)
