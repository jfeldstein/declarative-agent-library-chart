# Spec–test traceability

<!-- Traceability: [CFHA-VER-003] -->

This matrix maps each **promoted** requirement ID under `openspec/specs/` to evidence the project accepts for **default PR CI** or a **documented tier**. It is enforced by `scripts/check_spec_traceability.py` (see `ci.sh`).

## CI tiers

| Tier | Meaning | This repository |
|------|---------|-----------------|
| **Default PR** | Runs on every PR and on `./ci.sh` without extra flags | `ruff`, `pytest` (85%+ coverage), `scripts/smoke_rag.py`, `helm unittest` on `examples/*`, `ct lint` when Helm toolchain is installed |
| **Opt-in integration** | Maintainer sets an environment variable locally or in a custom job | `RUN_KIND_O11Y_INTEGRATION=1` runs `runtime/tests/integration/test_kind_o11y_prometheus.py` (kind + Prometheus); use `uv run pytest … --no-cov` when running only that test |
| **Scheduled** | Nightly or main-branch automation | `.github/workflows/scheduled-o11y-integration.yml` runs the kind/Prometheus integration on `main` on a cron schedule |
| **Manual** | Release or on-demand | Full cluster e2e in a staging environment (not wired in-repo) |

**Helm `helm test`:** Example charts may ship test hooks documented under `helm/tests/chart/`; default PR evidence for chart **SHALL** clauses is primarily **helm unittest** under `examples/*/tests/` plus `ct lint`, not necessarily `helm test` on every run.

## Matrix

| ID | Spec | Evidence | CI tier |
| --- | --- | --- | --- |
| [CFHA-REQ-HELM-UNITTEST-001] | `openspec/specs/cfha-helm-unittest/spec.md` | `examples/hello-world/tests/hello_world_test.yaml`, `examples/with-scrapers/tests/with_scrapers_test.yaml`, `examples/with-observability/tests/with_observability_test.yaml`, `ci.sh` | default PR |
| [CFHA-REQ-HELM-UNITTEST-002] | `openspec/specs/cfha-helm-unittest/spec.md` | `examples/hello-world/tests/hello_world_test.yaml`, `ct.yaml`, `ci.sh` | default PR |
| [CFHA-REQ-HELM-UNITTEST-003] | `openspec/specs/cfha-helm-unittest/spec.md` | `ci.sh`, `README.md` | default PR |
| [CFHA-REQ-RAG-SCRAPERS-001] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `helm/chart/values.schema.json` | default PR |
| [CFHA-REQ-RAG-SCRAPERS-002] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `examples/with-scrapers/tests/with_scrapers_test.yaml`, `examples/hello-world/tests/hello_world_test.yaml` | default PR |
| [CFHA-REQ-RAG-SCRAPERS-003] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `helm/chart/values.yaml`, `helm/chart/values.schema.json` | default PR |
| [CFHA-REQ-RAG-SCRAPERS-004] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `runtime/tests/test_runtime_config.py`, `examples/hello-world/tests/hello_world_test.yaml` | default PR |
| [CFHA-REQ-O11Y-SCRAPE-001] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `runtime/tests/test_o11y_metrics.py::test_metrics_endpoint_exposes_registry` | default PR |
| [CFHA-REQ-O11Y-SCRAPE-002] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `runtime/tests/test_o11y_metrics.py::test_trigger_success_increments_counter`, `runtime/tests/test_o11y_metrics.py::test_trigger_client_error_increments_client_error` | default PR |
| [CFHA-REQ-O11Y-SCRAPE-003] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `runtime/tests/test_o11y_metrics.py::test_subagent_and_skill_and_mcp_metrics` | default PR |
| [CFHA-REQ-O11Y-SCRAPE-004] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `examples/with-observability/tests/with_observability_test.yaml` | default PR |
| [CFHA-REQ-O11Y-SCRAPE-005] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `examples/with-observability/tests/with_observability_test.yaml` | default PR |
| [CFHA-REQ-O11Y-LOGS-001] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `runtime/tests/test_o11y_metrics.py::test_json_log_format_emits_message_key` | default PR |
| [CFHA-REQ-O11Y-LOGS-002] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `runtime/tests/test_o11y_metrics.py::test_x_request_id_echo_and_generation` | default PR |
| [CFHA-REQ-O11Y-LOGS-003] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `grafana/cfha-agent-overview.json`, `grafana/README.md` | default PR |
| [CFHA-REQ-O11Y-LOGS-004] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `docs/observability.md`, `README.md` | default PR |
| [CFHA-REQ-CHART-CT-001] | `openspec/specs/cfha-chart-testing-ct/spec.md` | `ci.sh`, `ct.yaml` | default PR |
| [CFHA-REQ-CHART-CT-002] | `openspec/specs/cfha-chart-testing-ct/spec.md` | `ci.sh`, `README.md` | default PR |
| [CFHA-VER-001] | `openspec/specs/cfha-requirement-verification/spec.md` | `scripts/check_spec_traceability.py` | default PR |
| [CFHA-VER-002] | `openspec/specs/cfha-requirement-verification/spec.md` | `runtime/tests/test_o11y_metrics.py`, `examples/hello-world/tests/hello_world_test.yaml` | default PR |
| [CFHA-VER-003] | `openspec/specs/cfha-requirement-verification/spec.md` | `docs/spec-test-traceability.md` | default PR |
| [CFHA-VER-004] | `openspec/specs/cfha-requirement-verification/spec.md` | `ci.sh`, `docs/spec-test-traceability.md`, `.github/workflows/scheduled-o11y-integration.yml` | default PR + scheduled |
| [CFHA-VER-005] | `openspec/specs/cfha-requirement-verification/spec.md` | `AGENTS.md`, `.cursor/rules/spec-traceability.mdc` | default PR |
