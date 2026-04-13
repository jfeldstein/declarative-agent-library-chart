## ADDED Requirements

### Requirement: [CFHA-REQ-HELM-UNITTEST-001] Helm-unittest replaces grep-based template assertions

The system SHALL use the official [helm-unittest](https://github.com/helm-unittest/helm-unittest) plugin to assert rendered template behavior for the example charts, eliminating reliance on `helm template ... | grep -c` for the following checks: default `examples/hello-world` produces zero `CronJob` documents and zero occurrences of the RAG component selector label `app.kubernetes.io/component: rag`; `examples/with-scrapers` produces at least one `CronJob` and at least one RAG component label; `examples/with-observability` produces at least four `prometheus.io/scrape` annotations (or equivalent stable assertions agreed in implementation) and exactly two `ServiceMonitor` documents.

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

#### Scenario: with-observability exposes scrape config and ServiceMonitors

- **WHEN** helm-unittest runs against `examples/with-observability` with default example values
- **THEN** the rendered output satisfies the same intent as prior CI: multiple targets carry `prometheus.io/scrape` and exactly two `ServiceMonitor` resources exist

### Requirement: [CFHA-REQ-HELM-UNITTEST-002] Library chart is covered by unittest where applicable

The system SHALL include helm-unittest coverage for `helm/chart` for behaviors that are testable without an example parent chart, or SHALL document that the library is validated only via `ct lint` and example chart tests, with no reduction in coverage versus the pre-change grep-based template checks in the former root CI script.

#### Scenario: No loss of coverage versus previous CI

- **WHEN** the change is complete and grep counts on `helm template` output are no longer used for those assertions
- **THEN** every assertion previously enforced by those grep checks remains enforced by helm-unittest or by `ct lint`, without weakening thresholds

### Requirement: [CFHA-REQ-HELM-UNITTEST-003] Official helm-unittest install path

The system SHALL reference the official helm-unittest installation method (`helm plugin install https://github.com/helm-unittest/helm-unittest.git` or a pinned release/binary) in developer or CI documentation used for this project.

#### Scenario: Reproducible unittest invocation

- **WHEN** a maintainer follows the documented install steps
- **THEN** `helm unittest` runs successfully against the charts that contain `tests/` suites
