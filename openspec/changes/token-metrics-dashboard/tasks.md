## 1. Metrics scaffolding

- [ ] 1.1 Register new Prometheus metrics in `helm/src/hosted_agents/metrics.py` per **`cfha-runtime-token-metrics`** names, buckets, and HELP strings
- [ ] 1.2 Add bounded label helpers (reuse existing tagify / config patterns) and document allowed label keys in `docs/observability.md`

## 2. Runtime instrumentation

- [ ] 2.1 Attach LangChain/LangGraph callback or wrapper at the trigger LLM invocation site to capture token usage and stream timing
- [ ] 2.2 Record **TTFT** once per invocation for streaming and non-streaming paths per **[DALC-REQ-TOKEN-MET-003]**
- [ ] 2.3 Increment **input/output** token counters and **`agent_runtime_llm_usage_missing_total`** when counts absent per **[DALC-REQ-TOKEN-MET-001]** / **[DALC-REQ-TOKEN-MET-002]**
- [ ] 2.4 Observe trigger request/response byte sizes at HTTP boundary per **[DALC-REQ-TOKEN-MET-004]** (clamp per design)
- [ ] 2.5 Wire **estimated cost** counter from env-configured rates per **[DALC-REQ-TOKEN-MET-005]**; document env vars in `docs/observability.md` and optional Helm `values` comments

## 3. Tests

- [ ] 3.1 Pytest: metrics increment on mocked LLM response with usage metadata; missing usage increments missing counter
- [ ] 3.2 Pytest: TTFT histogram receives observation when streaming callback fires (mock clock or callback order)
- [ ] 3.3 Pytest: HELP text substrings for new collectors (lightweight registry inspection)

## 4. Grafana dashboard

- [ ] 4.1 Add `grafana/cfha-token-metrics.json` (or chosen filename) with panels for token rate, TTFT quantiles, payload histograms, estimated cost per **[DALC-REQ-O11Y-LOGS-005]**
- [ ] 4.2 Update `grafana/README.md` with import path, datasource uid note, and cross-link to `docs/observability.md` metric names

## 5. Traceability (on promotion)

- [ ] 5.1 When promoting **`cfha-runtime-token-metrics`** and **`cfha-agent-o11y-logs-dashboards`** deltas to `openspec/specs/`, add matrix rows to `docs/spec-test-traceability.md` and requirement IDs to pytest/Helm evidence per **ADR 0003**
