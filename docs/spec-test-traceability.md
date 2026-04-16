# Spec–test traceability matrix

<!-- Traceability: [DALC-VER-003] [DALC-VER-004] -->

This file holds the **authoritative test-to-spec map** (requirement → automated test evidence) and **CI tier** summary. In prose, call this **test-to-spec traceability** or **spec–test traceability** so “traceability” is not confused with unrelated domains (lineage, supply chain, etc.). Rules (IDs, waivers, pytest `::` convention) are in **[ADR 0003: Spec–test traceability](adrs/0003-spec-test-traceability.md)**.

**Waiver columns:** use **`-`** for active rows. For a **waived** row, set **Waiver approver** (GitHub username of the approving maintainer) and **Waiver reason** (≥10 characters). Evidence may be **`-`** only when waived.

The table is parsed by `scripts/check_spec_traceability.py`; keep the **Matrix** section format stable.

## CI tiers

| Tier | Meaning | This repository |
|------|---------|-----------------|
| **Default PR** | Runs on every PR | `ruff`, `pytest` (85%+ coverage), `scripts/check_spec_traceability.py`, `tests/integration/smoke_rag.py`, `helm unittest -f helm/tests/*_test.yaml` from each `examples/*` chart, `ct lint` |
| **Opt-in integration** | Env-gated locally | `RUN_KIND_O11Y_INTEGRATION=1` → `helm/src/tests/integration/test_kind_o11y_prometheus.py` |
| **Scheduled** | Cron on `main` | `.github/workflows/scheduled-o11y-integration.yml` runs the same integration test |
| **Manual** | On demand | Full cluster e2e (not wired in-repo) |

## Matrix

| ID | Spec | Evidence | CI tier | Waiver approver | Waiver reason |
| --- | --- | --- | --- | --- | --- |
| [DALC-REQ-HELM-UNITTEST-001] | `openspec/specs/dalc-helm-unittest/spec.md` | `helm/tests/hello_world_test.yaml`, `helm/tests/with_scrapers_test.yaml`, `helm/tests/with_observability_test.yaml`, `helm/tests/checkpointing_test.yaml`, `examples/with-observability/values-observability-no-rag.yaml`, `.github/workflows/ci.yml` | default PR | - | - |
| [DALC-REQ-HELM-UNITTEST-002] | `openspec/specs/dalc-helm-unittest/spec.md` | `helm/tests/hello_world_test.yaml`, `helm/tests/checkpointing_test.yaml`, `ct.yaml`, `.github/workflows/ci.yml` | default PR | - | - |
| [DALC-REQ-HELM-UNITTEST-003] | `openspec/specs/dalc-helm-unittest/spec.md` | `.github/workflows/ci.yml`, `README.md` | default PR | - | - |
| [DALC-REQ-HELM-UNITTEST-004] | `openspec/specs/dalc-helm-unittest/spec.md` | `helm/tests/with_scrapers_test.yaml`, `examples/with-scrapers/README.md` | default PR | - | - |
| [DALC-REQ-EXAMPLE-VALUES-FILES-001] | `openspec/specs/dalc-example-values-files/spec.md` | `examples/with-scrapers/README.md`, `helm/tests/with_scrapers_test.yaml` | default PR | - | - |
| [DALC-REQ-EXAMPLE-VALUES-FILES-002] | `openspec/specs/dalc-example-values-files/spec.md` | `examples/with-scrapers/README.md` | default PR | - | - |
| [DALC-REQ-DALC-PKG-001] | `openspec/specs/dalc-library-chart-packaging/spec.md` | `helm/chart/Chart.yaml`, `helm/src/tests/test_chart_values_contract.py::test_library_chart_name_is_dalc_packaging` | default PR | - | - |
| [DALC-REQ-DALC-PKG-002] | `openspec/specs/dalc-library-chart-packaging/spec.md` | `examples/hello-world/Chart.yaml`, `examples/hello-world/values.yaml`, `helm/tests/hello_world_test.yaml` | default PR | - | - |
| [DALC-REQ-DALC-PKG-003] | `openspec/specs/dalc-library-chart-packaging/spec.md` | `helm/chart/values.yaml`, `helm/src/tests/test_chart_values_contract.py::test_library_image_repository_default_is_dalc_packaging` | default PR | - | - |
| [DALC-REQ-RAG-SCRAPERS-001] | `openspec/specs/dalc-rag-from-scrapers/spec.md` | `helm/chart/values.schema.json` | default PR | - | - |
| [DALC-REQ-RAG-SCRAPERS-002] | `openspec/specs/dalc-rag-from-scrapers/spec.md` | `helm/tests/with_scrapers_test.yaml`, `helm/tests/hello_world_test.yaml`, `helm/chart/templates/scraper-job-configmaps.yaml` | default PR | - | - |
| [DALC-REQ-RAG-SCRAPERS-003] | `openspec/specs/dalc-rag-from-scrapers/spec.md` | `helm/chart/values.yaml`, `helm/chart/values.schema.json` | default PR | - | - |
| [DALC-REQ-RAG-SCRAPERS-004] | `openspec/specs/dalc-rag-from-scrapers/spec.md` | `helm/src/tests/test_runtime_config.py::test_from_env_empty`, `helm/tests/hello_world_test.yaml` | default PR | - | - |
| [DALC-REQ-SCRAPER-CURSOR-001] | `openspec/specs/dalc-scraper-cursor-store/spec.md` | `helm/src/tests/test_cursor_store.py::test_file_store_jira_compat_roundtrip`, `helm/src/tests/test_cursor_store.py::test_file_store_slack_compat_roundtrip`, `helm/src/hosted_agents/scrapers/cursor_store.py` | default PR | - | - |
| [DALC-REQ-SCRAPER-CURSOR-002] | `openspec/specs/dalc-scraper-cursor-store/spec.md` | `helm/src/tests/test_cursor_store.py::test_postgres_store_issues_idempotent_ddl_and_upsert`, `helm/src/hosted_agents/scrapers/cursor_store.py` | default PR | - | - |
| [DALC-REQ-SCRAPER-CURSOR-003] | `openspec/specs/dalc-scraper-cursor-store/spec.md` | `helm/tests/with_scrapers_test.yaml`, `helm/chart/templates/scraper-cronjobs.yaml`, `helm/chart/values.yaml`, `helm/chart/values.schema.json` | default PR | - | - |
| [DALC-REQ-SCRAPER-CURSOR-004] | `openspec/specs/dalc-scraper-cursor-store/spec.md` | `helm/tests/with_scrapers_test.yaml`, `helm/chart/templates/scraper-cronjobs.yaml` | default PR | - | - |
| [DALC-REQ-O11Y-SCRAPE-001] | `openspec/specs/dalc-agent-o11y-scrape/spec.md` | `helm/src/tests/test_o11y_metrics.py::test_metrics_endpoint_exposes_registry` | default PR | - | - |
| [DALC-REQ-O11Y-SCRAPE-002] | `openspec/specs/dalc-agent-o11y-scrape/spec.md` | `helm/src/tests/test_o11y_metrics.py::test_trigger_success_increments_counter`, `helm/src/tests/test_o11y_metrics.py::test_trigger_client_error_increments_client_error` | default PR | - | - |
| [DALC-REQ-O11Y-SCRAPE-003] | `openspec/specs/dalc-agent-o11y-scrape/spec.md` | `helm/src/tests/test_o11y_metrics.py::test_subagent_and_skill_and_mcp_metrics` | default PR | - | - |
| [DALC-REQ-O11Y-SCRAPE-004] | `openspec/specs/dalc-agent-o11y-scrape/spec.md` | `helm/tests/with_observability_test.yaml` | default PR | - | - |
| [DALC-REQ-O11Y-SCRAPE-005] | `openspec/specs/dalc-agent-o11y-scrape/spec.md` | `helm/tests/with_observability_test.yaml`, `examples/with-observability/values-observability-no-rag.yaml` | default PR | - | - |
| [DALC-REQ-O11Y-SCRAPE-006] | `openspec/specs/dalc-agent-o11y-scrape/spec.md` | `helm/tests/with_observability_test.yaml` | default PR | - | - |
| [DALC-REQ-CHART-RTV-001] | `openspec/specs/dalc-chart-runtime-values/spec.md` | `helm/tests/hello_world_test.yaml`, `helm/tests/checkpointing_test.yaml`, `examples/checkpointing/values.yaml` | default PR | - | - |
| [DALC-REQ-CHART-RTV-002] | `openspec/specs/dalc-chart-runtime-values/spec.md` | `helm/tests/hello_world_test.yaml` | default PR | - | - |
| [DALC-REQ-CHART-RTV-003] | `openspec/specs/dalc-chart-runtime-values/spec.md` | `helm/tests/hello_world_test.yaml` | default PR | - | - |
| [DALC-REQ-CHART-RTV-004] | `openspec/specs/dalc-chart-runtime-values/spec.md` | `helm/src/tests/test_chart_values_contract.py::test_library_values_yaml_excludes_atif_and_shadow`, `helm/src/tests/test_chart_values_contract.py::test_library_values_schema_excludes_atif_and_shadow` | default PR | - | - |
| [DALC-REQ-O11Y-LOGS-001] | `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | `helm/src/tests/test_o11y_metrics.py::test_json_log_format_emits_message_key` | default PR | - | - |
| [DALC-REQ-O11Y-LOGS-002] | `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | `helm/src/tests/test_o11y_metrics.py::test_x_request_id_echo_and_generation` | default PR | - | - |
| [DALC-REQ-O11Y-LOGS-003] | `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | `grafana/dalc-overview.json`, `grafana/README.md` | default PR | - | - |
| [DALC-REQ-O11Y-LOGS-004] | `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | `docs/observability.md`, `README.md` | default PR | - | - |
| [DALC-REQ-O11Y-LOGS-005] | `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | `grafana/README.md` | default PR | - | - |
| [DALC-REQ-CHART-CT-001] | `openspec/specs/dalc-chart-testing-ct/spec.md` | `.github/workflows/ci.yml`, `ct.yaml` | default PR | - | - |
| [DALC-REQ-CHART-CT-002] | `openspec/specs/dalc-chart-testing-ct/spec.md` | `.github/workflows/ci.yml`, `README.md` | default PR | - | - |
| [DALC-VER-001] | `openspec/specs/dalc-requirement-verification/spec.md` | `scripts/check_spec_traceability.py` | default PR | - | - |
| [DALC-VER-002] | `openspec/specs/dalc-requirement-verification/spec.md` | `helm/src/tests/test_o11y_metrics.py`, `helm/tests/hello_world_test.yaml` | default PR | - | - |
| [DALC-VER-003] | `openspec/specs/dalc-requirement-verification/spec.md` | `docs/spec-test-traceability.md`, `docs/adrs/0003-spec-test-traceability.md` | default PR | - | - |
| [DALC-VER-004] | `openspec/specs/dalc-requirement-verification/spec.md` | `.github/workflows/ci.yml`, `docs/spec-test-traceability.md`, `.github/workflows/scheduled-o11y-integration.yml` | default PR + scheduled | - | - |
| [DALC-VER-005] | `openspec/specs/dalc-requirement-verification/spec.md` | `docs/AGENTS.md`, `.cursor/rules/spec-traceability.mdc` | default PR | - | - |
