# Spec–test traceability matrix

<!-- Traceability: [CFHA-VER-003] [CFHA-VER-004] -->

This file holds the **authoritative requirement → evidence map** and **CI tier** summary. Rules (IDs, waivers, pytest `::` convention) are in **[ADR 0003: Spec–test traceability](adrs/0003-spec-test-traceability.md)**.

**Waiver columns:** use **`-`** for active rows. For a **waived** row, set **Waiver approver** (GitHub username of the approving maintainer) and **Waiver reason** (≥10 characters). Evidence may be **`-`** only when waived.

The table is parsed by `scripts/check_spec_traceability.py`; keep the **Matrix** section format stable.

## CI tiers

| Tier | Meaning | This repository |
|------|---------|-----------------|
| **Default PR** | Runs on every PR | `ruff`, `pytest` (85%+ coverage), `scripts/check_spec_traceability.py`, `scripts/smoke_rag.py`, `helm unittest` on `examples/*`, `ct lint` |
| **Opt-in integration** | Env-gated locally | `RUN_KIND_O11Y_INTEGRATION=1` → `runtime/tests/integration/test_kind_o11y_prometheus.py` |
| **Manual** | On demand | Full cluster e2e (not wired in-repo) |

## Matrix

| ID | Spec | Evidence | CI tier | Waiver approver | Waiver reason |
| --- | --- | --- | --- | --- | --- |
| [CFHA-REQ-HELM-UNITTEST-001] | `openspec/specs/cfha-helm-unittest/spec.md` | `examples/hello-world/tests/hello_world_test.yaml`, `examples/with-scrapers/tests/with_scrapers_test.yaml`, `examples/with-observability/tests/with_observability_test.yaml`, `.github/workflows/ci.yml` | default PR | - | - |
| [CFHA-REQ-HELM-UNITTEST-002] | `openspec/specs/cfha-helm-unittest/spec.md` | `examples/hello-world/tests/hello_world_test.yaml`, `ct.yaml`, `.github/workflows/ci.yml` | default PR | - | - |
| [CFHA-REQ-HELM-UNITTEST-003] | `openspec/specs/cfha-helm-unittest/spec.md` | `.github/workflows/ci.yml`, `README.md` | default PR | - | - |
| [CFHA-REQ-RAG-SCRAPERS-001] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `helm/chart/values.schema.json` | default PR | - | - |
| [CFHA-REQ-RAG-SCRAPERS-002] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `examples/with-scrapers/tests/with_scrapers_test.yaml`, `examples/hello-world/tests/hello_world_test.yaml` | default PR | - | - |
| [CFHA-REQ-RAG-SCRAPERS-003] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `helm/chart/values.yaml`, `helm/chart/values.schema.json` | default PR | - | - |
| [CFHA-REQ-RAG-SCRAPERS-004] | `openspec/specs/cfha-rag-from-scrapers/spec.md` | `runtime/tests/test_runtime_config.py::test_from_env_empty`, `examples/hello-world/tests/hello_world_test.yaml` | default PR | - | - |
| [CFHA-REQ-O11Y-SCRAPE-001] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `runtime/tests/test_o11y_metrics.py::test_metrics_endpoint_exposes_registry` | default PR | - | - |
| [CFHA-REQ-O11Y-SCRAPE-002] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `runtime/tests/test_o11y_metrics.py::test_trigger_success_increments_counter`, `runtime/tests/test_o11y_metrics.py::test_trigger_client_error_increments_client_error` | default PR | - | - |
| [CFHA-REQ-O11Y-SCRAPE-003] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `runtime/tests/test_o11y_metrics.py::test_subagent_and_skill_and_mcp_metrics` | default PR | - | - |
| [CFHA-REQ-O11Y-SCRAPE-004] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `examples/with-observability/tests/with_observability_test.yaml` | default PR | - | - |
| [CFHA-REQ-O11Y-SCRAPE-005] | `openspec/specs/cfha-agent-o11y-scrape/spec.md` | `examples/with-observability/tests/with_observability_test.yaml` | default PR | - | - |
| [CFHA-REQ-O11Y-LOGS-001] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `runtime/tests/test_o11y_metrics.py::test_json_log_format_emits_message_key` | default PR | - | - |
| [CFHA-REQ-O11Y-LOGS-002] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `runtime/tests/test_o11y_metrics.py::test_x_request_id_echo_and_generation` | default PR | - | - |
| [CFHA-REQ-O11Y-LOGS-003] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `grafana/cfha-agent-overview.json`, `grafana/README.md` | default PR | - | - |
| [CFHA-REQ-O11Y-LOGS-004] | `openspec/specs/cfha-agent-o11y-logs-dashboards/spec.md` | `docs/observability.md`, `README.md` | default PR | - | - |
| [CFHA-REQ-CHART-CT-001] | `openspec/specs/cfha-chart-testing-ct/spec.md` | `.github/workflows/ci.yml`, `ct.yaml` | default PR | - | - |
| [CFHA-REQ-CHART-CT-002] | `openspec/specs/cfha-chart-testing-ct/spec.md` | `.github/workflows/ci.yml`, `README.md` | default PR | - | - |
| [CFHA-VER-001] | `openspec/specs/cfha-requirement-verification/spec.md` | `scripts/check_spec_traceability.py` | default PR | - | - |
| [CFHA-VER-002] | `openspec/specs/cfha-requirement-verification/spec.md` | `runtime/tests/test_o11y_metrics.py`, `examples/hello-world/tests/hello_world_test.yaml` | default PR | - | - |
| [CFHA-VER-003] | `openspec/specs/cfha-requirement-verification/spec.md` | `docs/spec-test-traceability.md`, `docs/adrs/0003-spec-test-traceability.md` | default PR | - | - |
| [CFHA-VER-004] | `openspec/specs/cfha-requirement-verification/spec.md` | `.github/workflows/ci.yml`, `docs/spec-test-traceability.md` | default PR | - | - |
| [CFHA-VER-005] | `openspec/specs/cfha-requirement-verification/spec.md` | `docs/AGENTS.md`, `.cursor/rules/spec-traceability.mdc` | default PR | - | - |
