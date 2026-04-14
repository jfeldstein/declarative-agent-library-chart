## 1. Specs and traceability

- [ ] 1.1 Merge delta specs from `openspec/changes/observability-automatic-enabled-components/specs/` into `openspec/specs/cfha-agent-o11y-scrape/spec.md`, `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md`, and `openspec/specs/cfha-helm-unittest/spec.md` (or follow project archive workflow if merging happens at archive time—keep repo consistent with **CFHA-VER-005**).
- [ ] 1.2 Update `docs/spec-test-traceability.md` for any new or materially changed **`### Requirement:`** lines (`[CFHA-REQ-O11Y-LOGS-005]`, modified scrape/unittest rows).
- [ ] 1.3 Run `python3 scripts/check_spec_traceability.py` and fix any gaps.

## 2. Helm unittest (`examples/with-observability`)

- [ ] 2.1 Refactor `examples/with-observability/tests/with_observability_test.yaml` to use **component-neutral** test titles (not “RAG-only” wording) while still validating the managed RAG `Service` when deployed.
- [ ] 2.2 Add or adjust values (suite-level or fixture) so tests assert **`ServiceMonitor` exists for each enabled metrics `Service`** when multiple components are on (agent + optional deployed service).
- [ ] 2.3 Add a test case with **`o11y.serviceMonitor.enabled`** true **and** an optional metrics workload **not** deployed (for example all scraper jobs `enabled: false` or equivalent) asserting **`rag-servicemonitor.yaml` renders zero documents** while `servicemonitor.yaml` still renders the agent monitor.
- [ ] 2.4 Run `helm unittest` for affected charts and capture passing output for the PR.

## 3. Grafana artifact and README

- [ ] 3.1 Rewrite `grafana/README.md` Prometheus section so instructions are **generic** (every enabled metrics `Service` / matching scrape jobs)—remove “scrape **both** targets” framing; align with `examples/with-observability` and `runtime/tests/scripts/prometheus-kind-o11y-values.yaml` without RAG-only assumptions.
- [ ] 3.2 Update `grafana/cfha-agent-overview.json` so **optional component** metrics (e.g. RAG) are **optional in the UX** per **LOGS-003** (variables, repeated rows, or clearly titled sections with dependency called out)—document the mechanism in the README.
- [ ] 3.3 If dashboard JSON structure changes, smoke-check import instructions still work.

## 4. Verification

- [ ] 4.1 Run the project’s standard Python/Helm CI checks locally (pytest if touched, `helm unittest`, `check_spec_traceability`).
- [ ] 4.2 Add a short entry to `docs/development-log.md` summarizing the behavioral and doc intent (if this repo logs changes there for releases).
