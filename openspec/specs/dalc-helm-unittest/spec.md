## ADDED Requirements

### Requirement: [DALC-REQ-HELM-UNITTEST-001] Helm-unittest replaces grep-based template assertions

The system SHALL use the official [helm-unittest](https://github.com/helm-unittest/helm-unittest) plugin to assert rendered template behavior for the example charts, eliminating reliance on `helm template ... | grep -c` for the following checks: default `examples/hello-world` produces zero `CronJob` documents and zero occurrences of the RAG component selector label `app.kubernetes.io/component: rag`; `examples/with-scrapers` produces at least one `CronJob` and at least one RAG component label; `examples/with-observability` produces at least four `prometheus.io/scrape` annotations (or equivalent stable assertions agreed in implementation) and **assertions that `ServiceMonitor` documents exist for each deployed chart-managed metrics `Service` in that example** (with **at least two** `ServiceMonitor` documents when both the agent and a scraper-gated optional metrics service are enabled), **and** assertions that **no** `ServiceMonitor` is rendered for an optional metrics workload’s template when that workload is **not** deployed.

#### Scenario: hello-world default has no CronJob

- **WHEN** helm-unittest runs against `examples/hello-world` with default values
- **THEN** no rendered manifest has `kind: CronJob`

#### Scenario: hello-world default has no RAG workload

- **WHEN** helm-unittest runs against `examples/hello-world` with default values
- **THEN** the flattened rendered output contains zero occurrences of `app.kubernetes.io/component: rag`

#### Scenario: with-scrapers includes a CronJob

- **WHEN** helm-unittest runs against `examples/with-scrapers` with default example values
- **THEN** at least one rendered manifest has `kind: CronJob`

#### Scenario: with-scrapers includes RAG workload

- **WHEN** helm-unittest runs against `examples/with-scrapers` with default example values
- **THEN** the flattened rendered output contains at least one occurrence of `app.kubernetes.io/component: rag`

#### Scenario: with-observability exposes scrape config and ServiceMonitors for enabled metrics services

- **WHEN** helm-unittest runs against `examples/with-observability` with example values that deploy **multiple** chart metrics **`Services`** (for example agent and an optional service such as scraper-gated RAG)
- **THEN** the rendered output SHALL include multiple targets carrying `prometheus.io/scrape` as before, and SHALL include **one `ServiceMonitor` per deployed metrics `Service`** asserted by stable template tests (for example agent `ServiceMonitor` and optional workload `ServiceMonitor` when that workload is enabled)

#### Scenario: with-observability does not render ServiceMonitor for an optional metrics workload that is disabled

- **WHEN** helm-unittest runs against `examples/with-observability` with **`observability.serviceMonitor.enabled`** true (or equivalent) but values **do not** deploy a given optional metrics **`Service`** (for example RAG not deployed)
- **THEN** the rendered output SHALL include **no** `ServiceMonitor` document from that optional workload’s chart template

### Requirement: [DALC-REQ-HELM-UNITTEST-002] Library chart is covered by unittest where applicable

The system SHALL include helm-unittest coverage for `helm/chart` for behaviors that are testable without an example parent chart, or SHALL document that the library is validated only via `ct lint` and example chart tests, with no reduction in coverage versus the pre-change grep-based template checks in the former root CI script.

#### Scenario: No loss of coverage versus previous CI

- **WHEN** the change is complete and grep counts on `helm template` output are no longer used for those assertions
- **THEN** every assertion previously enforced by those grep checks remains enforced by helm-unittest or by `ct lint`, without weakening thresholds

### Requirement: [DALC-REQ-HELM-UNITTEST-003] Official helm-unittest install path

The system SHALL reference the official helm-unittest installation method (`helm plugin install https://github.com/helm-unittest/helm-unittest.git` or a pinned release/binary) in developer or CI documentation used for this project.

#### Scenario: Reproducible unittest invocation

- **WHEN** a maintainer follows the documented install steps
- **THEN** `helm unittest` runs successfully for each example application chart when invoked from that chart’s directory with the documented **`-f`** path to the corresponding suite file under **`helm/tests/`**, with the suite’s **`values:`** entries pointing at that example’s committed **`values.yaml`** (paths relative to the suite file, e.g. **`../../examples/<example>/values.yaml`**) so rendering matches the example defaults

### Requirement: [DALC-REQ-HELM-UNITTEST-004] Helm-unittest covers each documented multi-setup values file

For any **`examples/<name>/`** chart whose **README documents two or more** distinct values files as separate setups (per **`dalc-example-values-files`**), the repository SHALL run helm-unittest (suites under **`helm/tests/`** following repository conventions) such that **each** documented values file is loaded in **at least one** test case or suite `values:` block, and assertions SHALL validate behavior specific to that setup (for example presence or absence of workloads, labels, or annotations described for that file).

#### Scenario: Every documented setup file has unittest coverage

- **WHEN** an example README lists multiple values files as distinct setups
- **THEN** the matching `helm/tests/` suite SHALL include coverage that targets each listed file (or equivalent inlined values) with at least one `it:` (or equivalent) whose expectations match that setup’s description

#### Scenario: Single-file examples do not require extra values files

- **WHEN** an example documents only one values story
- **THEN** this requirement SHALL NOT require additional values files beyond what **`dalc-example-values-files`** and existing **`dalc-helm-unittest`** requirements already impose
