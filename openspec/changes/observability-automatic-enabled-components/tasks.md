## 1. Specs and traceability

- [x] 1.1 Merge delta specs from `openspec/changes/observability-automatic-enabled-components/specs/` into `openspec/specs/dalc-agent-o11y-scrape/spec.md`, `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md`, and `openspec/specs/dalc-helm-unittest/spec.md` (or follow project archive workflow if merging happens at archive time—keep repo consistent with **DALC-VER-005**).
- [x] 1.2 Update `docs/spec-test-traceability.md` for any new or materially changed **`### Requirement:`** lines (`[DALC-REQ-O11Y-LOGS-005]`, modified scrape/unittest rows).
- [x] 1.3 Run `python3 scripts/check_spec_traceability.py` and fix any gaps.

## 2. Helm unittest (`examples/with-observability`)

- [x] 2.1 Refactor `helm/tests/with_observability_test.yaml` (consolidated unittest path) to use **component-neutral** test titles (not “RAG-only” wording) while still validating the managed RAG `Service` when deployed.
- [x] 2.2 Add or adjust values (suite-level or fixture) so tests assert **`ServiceMonitor` exists for each enabled metrics `Service`** when multiple components are on (agent + optional deployed service).
- [x] 2.3 Add a test case with **`o11y.serviceMonitor.enabled`** true **and** an optional metrics workload **not** deployed (for example all scraper jobs `enabled: false` or equivalent) asserting **`rag-servicemonitor.yaml` renders zero documents** while `servicemonitor.yaml` still renders the agent monitor.
- [x] 2.4 Run `helm unittest` for affected charts and capture passing output for the PR.

## 3. Grafana artifact and README

- [x] 3.1 Rewrite `grafana/README.md` Prometheus section so instructions are **generic** (every enabled metrics `Service` / matching scrape jobs)—remove “scrape **both** targets” framing; align with `examples/with-observability` and `helm/src/tests/scripts/prometheus-kind-o11y-values.yaml` without RAG-only assumptions.
- [x] 3.2 Update `grafana/dalc-agent-overview.json` so **optional component** metrics (e.g. RAG) are **optional in the UX** per **LOGS-003** (variables, repeated rows, or clearly titled sections with dependency called out)—document the mechanism in the README.
- [x] 3.3 If dashboard JSON structure changes, smoke-check import instructions still work.

## 4. Verification

- [x] 4.1 Run the project’s standard Python/Helm CI checks locally (pytest if touched, `helm unittest`, `check_spec_traceability`).
- [x] 4.2 Add a short entry to `docs/development-log.md` summarizing the behavioral and doc intent (if this repo logs changes there for releases).
