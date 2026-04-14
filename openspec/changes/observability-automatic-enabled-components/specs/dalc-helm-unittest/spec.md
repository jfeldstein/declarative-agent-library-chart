## MODIFIED Requirements

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

- **WHEN** helm-unittest runs against `examples/with-observability` with **`o11y.serviceMonitor.enabled`** true (or equivalent) but values **do not** deploy a given optional metrics **`Service`** (for example RAG not deployed)
- **THEN** the rendered output SHALL include **no** `ServiceMonitor` document from that optional workload’s chart template
