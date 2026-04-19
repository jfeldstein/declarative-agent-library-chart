# Spec ↔ code validation — observability & chart contracts

Worktree validation snapshot: promoted specs under `openspec/specs/` vs `docs/spec-test-traceability.md` evidence paths and spot-checks (metrics names, Helm keys, templates). Per-requirement verdicts: **OK** (evidence exists + implementation aligns), **PARTIAL** (traceability/evidence OK but automated proof is thin or incomplete vs the SHALL), **GAP** (likely drift or missing evidence).

## Summary

| Capability | Requirement IDs | OK | PARTIAL | GAP |
| --- | --- | --- | --- | --- |
| `dalc-agent-o11y-logs-dashboards` | O11Y-LOGS-001 … 006 | 6 | 0 | 0 |
| `dalc-agent-o11y-scrape` | O11Y-SCRAPE-001 … 006 | 6 | 0 | 0 |
| `dalc-runtime-token-metrics` | TOKEN-MET-001 … 006 | 6 | 0 | 0 |
| `dalc-chart-presence` | CHART-PRESENCE-001 … 003 | 3 | 0 | 0 |
| `dalc-chart-runtime-values` | CHART-RTV-001 … 004 | 4 | 0 | 0 |
| `dalc-chart-testing-ct` | CHART-CT-001 … 002 | 2 | 0 | 0 |

**GAP count (this segment): 0.**

---

## `dalc-agent-o11y-logs-dashboards`

| ID | Status | Evidence (matrix) | Spot-check |
| --- | --- | --- | --- |
| [DALC-REQ-O11Y-LOGS-001] | OK | `helm/src/tests/test_o11y_metrics.py::test_json_log_format_emits_message_key` | Subprocess probe with `HOSTED_AGENT_LOG_FORMAT=json` asserts `message`, `request_id`, `service` on the JSON line. `hosted_agents/o11y_logging.py` uses `add_log_level` + `JSONRenderer()` so `level` is present on the JSON path even though the test does not assert it. |
| [DALC-REQ-O11Y-LOGS-002] | OK | `helm/src/tests/test_o11y_metrics.py::test_x_request_id_echo_and_generation`, `helm/src/tests/test_o11y_metrics.py::test_json_logs_emit_structured_correlation_for_trigger_route` | Header echo/generation plus subprocess JSON logs from a full trigger round-trip with fixed `X-Request-Id`, asserting `request_id` on `http_request_*` lines. |
| [DALC-REQ-O11Y-LOGS-003] | OK | `grafana/dalc-overview.json`, `grafana/README.md` | Starter dashboard JSON exists; README documents import path, placeholder datasource uid, and optional RAG/scraper sections. |
| [DALC-REQ-O11Y-LOGS-004] | OK | `docs/observability.md`, `README.md` | `docs/observability.md` documents stdout JSON and collectors (Fluent Bit / Promtail / Vector) and `HOSTED_AGENT_LOG_FORMAT`. |
| [DALC-REQ-O11Y-LOGS-005] | OK | `grafana/README.md` | “Prometheus scrape alignment” section describes variable target counts and optional components; avoids a fixed mandatory RAG scrape count. |
| [DALC-REQ-O11Y-LOGS-006] | OK | `grafana/cfha-token-metrics.json`, `grafana/README.md`, `docs/observability.md`; `helm/src/tests/test_token_metrics.py::test_o11y_logs_token_dashboard_capability_documented`, `helm/src/tests/test_token_metrics.py::test_cfha_token_dashboard_promql_matches_observability_metric_names` | README cross-link preserved; **`test_cfha_token_dashboard_promql_matches_observability_metric_names`** parses dashboard `expr` strings and asserts each `dalc_*` token maps to documentation in **`docs/observability.md`**. |

---

## `dalc-agent-o11y-scrape`

| ID | Status | Evidence (matrix) | Spot-check |
| --- | --- | --- | --- |
| [DALC-REQ-O11Y-SCRAPE-001] | OK | `helm/src/tests/test_o11y_metrics.py::test_metrics_endpoint_exposes_registry` | `GET /metrics` returns 200 and exposition text with `# TYPE` and `dalc_http_trigger`. |
| [DALC-REQ-O11Y-SCRAPE-002] | OK | adds `helm/src/tests/test_o11y_metrics.py::test_trigger_unhandled_exception_increments_server_error`, `test_trigger_http_error_5xx_increments_server_error`, `test_trigger_http_error_4xx_stays_client_error` | Success/client_error counters unchanged; **`server_error`** asserted for unhandled `RuntimeError`, `TriggerHttpError` ≥500; `<500` **`TriggerHttpError`** maps to **`client_error`**. |
| [DALC-REQ-O11Y-SCRAPE-003] | OK | `helm/src/tests/test_o11y_metrics.py::test_subagent_and_skill_and_mcp_metrics` | `/metrics` includes `dalc_subagent_*`, `dalc_skill_*`, `dalc_mcp_tool_*` series after exercised paths. |
| [DALC-REQ-O11Y-SCRAPE-004] | OK | `helm/tests/with_observability_test.yaml`, `helm/tests/with_scrapers_test.yaml` (`it: scraper CronJob pod template has prometheus scrape annotations when enabled`), `examples/with-scrapers/values.prometheus-annotations.yaml` | Agent/RAG unchanged; **`with_scrapers_test`** overlays **`values.prometheus-annotations.yaml`** and asserts CronJob **`spec.jobTemplate.spec.template.metadata.annotations`** `prometheus.io/scrape|port|path`. |
| [DALC-REQ-O11Y-SCRAPE-005] | OK | `helm/tests/with_observability_test.yaml` | ServiceMonitor for agent and optional RAG; RAG absent → single ServiceMonitor document. |
| [DALC-REQ-O11Y-SCRAPE-006] | OK | `helm/tests/with_observability_test.yaml` | Agent container env `HOSTED_AGENT_LOG_FORMAT` = `json` when observability values require it. |

---

## `dalc-runtime-token-metrics`

| ID | Status | Evidence (matrix) | Spot-check |
| --- | --- | --- | --- |
| [DALC-REQ-TOKEN-MET-001] | OK | `helm/src/agent/metrics.py`, `helm/src/agent/llm_metrics.py`, `helm/src/tests/test_token_metrics.py` | Counters and `test_llm_usage_missing_when_no_usage_metadata` / token tests. |
| [DALC-REQ-TOKEN-MET-002] | OK | same | Input tokens asserted in `test_llm_token_counters_and_cost_with_usage_metadata`. |
| [DALC-REQ-TOKEN-MET-003] | OK | same | `dalc_llm_time_to_first_token_seconds` + streaming labels covered by TTFT tests. |
| [DALC-REQ-TOKEN-MET-004] | OK | same + `helm/src/tests/test_token_metrics.py::test_trigger_payload_histograms_record_response_size` | Request histogram coverage unchanged; **`test_trigger_payload_histograms_record_response_size`** asserts **`dalc_http_trigger_response_bytes_sum`** increases by at least the UTF-8 length of the successful plain-text trigger response body. |
| [DALC-REQ-TOKEN-MET-005] | OK | same + `docs/observability.md` | Cost counter increments when pricing env vars set in test. |
| [DALC-REQ-TOKEN-MET-006] | OK | same | `test_new_metric_help_lines_include_semantics` checks HELP for estimated cost includes “estimate”; HELP strings in `metrics.py` document provider vs runtime semantics. |

---

## `dalc-chart-presence`

| ID | Status | Evidence (matrix) | Spot-check |
| --- | --- | --- | --- |
| [DALC-REQ-CHART-PRESENCE-001] | OK | `helm/chart/values.yaml`, `helm/chart/values.schema.json`, `helm/tests/hello_world_test.yaml` | Top-level `presence.slack` / `presence.jira` Secret-reference shape in schema and defaults. |
| [DALC-REQ-CHART-PRESENCE-002] | OK | `helm/chart/templates/_manifest_deployment.tpl`, `helm/tests/hello_world_test.yaml`, `helm/src/tests/test_runtime_config.py` | Template injects `HOSTED_AGENT_SLACK_BOT_USER_ID` / `HOSTED_AGENT_JIRA_BOT_ACCOUNT_ID` from `secretKeyRef`; unittest covers wired and omitted cases. |
| [DALC-REQ-CHART-PRESENCE-003] | OK | `README.md` | Example `values.yaml` fragment includes **both** `presence.slack` and `presence.jira` with `secretName` / `secretKey`. |

---

## `dalc-chart-runtime-values`

| ID | Status | Evidence (matrix) | Spot-check |
| --- | --- | --- | --- |
| [DALC-REQ-CHART-RTV-001] | OK | `helm/tests/hello_world_test.yaml`, `helm/tests/checkpointing_test.yaml`, `examples/checkpointing/values.yaml` | `checkpoints.postgresUrl` → `HOSTED_AGENT_POSTGRES_URL`; checkpoints not nested under `observability`. |
| [DALC-REQ-CHART-RTV-002] | OK | `helm/tests/hello_world_test.yaml` | W&B enabled → `HOSTED_AGENT_WANDB_*` / project / entity env. |
| [DALC-REQ-CHART-RTV-003] | OK | `helm/tests/hello_world_test.yaml` | `scrapers.slack.feedback` → feedback env and label registry wiring per tests. |
| [DALC-REQ-CHART-RTV-004] | OK | `helm/src/tests/test_chart_values_contract.py` | `test_library_values_yaml_excludes_atif_and_shadow` and schema test forbid `atifExport` / `shadow`. |

---

## `dalc-chart-testing-ct`

| ID | Status | Evidence (matrix) | Spot-check |
| --- | --- | --- | --- |
| [DALC-REQ-CHART-CT-001] | OK | `.github/workflows/ci.yml`, `ct.yaml` | `ct.yaml` sets `chart-dirs: helm, examples`; CI runs `ct lint --config ct.yaml --all`. |
| [DALC-REQ-CHART-CT-002] | OK | `.github/workflows/ci.yml`, `README.md` | Workflow comments pin `helm/chart-testing-action` / `ct` version; README traceability banner includes this ID. Operators can also follow **`docs/local-ci.md`** for installing `ct` and the same lint command (not listed in the matrix but consistent with CI). |

---

## Notes

- All file paths listed in **`docs/spec-test-traceability.md`** for these IDs were verified to exist at validation time under the target worktree.
- Prior **PARTIAL** rows in this segment were closed with additional pytest + Helm unittest coverage (see **`docs/spec-test-traceability.md`** for exact nodes).
