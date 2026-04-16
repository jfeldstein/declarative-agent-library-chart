## Why

Observability (Prometheus scrape metadata, optional `ServiceMonitor`s, and Grafana guidance) is described and tested in ways that center the **RAG** optional workload. Operators and maintainers need a **component-neutral** contract: any **enabled** chart-managed workload that exposes `/metrics` should follow the same discovery rules, and tests/docs should prove **positive** coverage for enabled components and **negative** coverage when a component is off—without implying RAG is special beyond being one optional service.

## What Changes

- **Specs**: Generalize `cfha-agent-o11y-scrape` so optional `ServiceMonitor` behavior is defined per **enabled** metrics-exporting component (not “agent + RAG” as a one-off). Add explicit scenarios for **no** `ServiceMonitor` when a component is not deployed or not enabled.
- **Helm unittest (`examples/with-observability`)**: Replace RAG-centric test names/assertions with tests that (1) enable **multiple** chart components that each warrant scrape discovery / `ServiceMonitor` resources, asserting the expected monitors exist, and (2) **disable at least one** optional component and assert its `ServiceMonitor` template does **not** render a document (while the agent monitor still does when enabled).
- **Grafana**: Update `grafana/README.md` (and dashboard JSON as needed) so documentation is **not RAG-specific** for Prometheus scrape setup; align the starter dashboard story with **enabled components** (panels or rows for components that are deployed; no misleading panels or import steps that assume RAG when it is off—e.g. variable-driven rows, clearly optional sections, or documented filtering).
- **Traceability**: Update `docs/spec-test-traceability.md` and test comments/docstrings per **DALC-VER-005** wherever `SHALL` rows change.

## Capabilities

### New Capabilities

- _(none — behavior is a refinement of existing observability and helm-unittest specs)_

### Modified Capabilities

- `cfha-agent-o11y-scrape`: Reframe **ServiceMonitor** and annotation requirements so they apply to **all** chart-managed workloads that expose `/metrics` when the corresponding component is enabled, with scenarios for presence and absence of monitors per component.
- `cfha-agent-o11y-logs-dashboards`: Extend starter Grafana requirements so documentation and the dashboard artifact reflect **per-component** visibility (enabled workload → relevant panels/rows; disabled optional workload → no requirement to show that component’s sections, or hide them via documented mechanism).
- `cfha-helm-unittest`: Replace fixed counts like “exactly two `ServiceMonitor` documents” with assertions that match the generalized scrape/ServiceMonitor contract and the new example tests (including negative cases).

## Impact

- **Specs**: Delta files under `openspec/changes/observability-automatic-enabled-components/specs/` for the three capabilities above; later promotion to `openspec/specs/` during apply/archive.
- **Charts / examples**: `examples/with-observability/tests/with_observability_test.yaml`, possibly `examples/with-observability/values.yaml` (if additional enabled components are needed to satisfy “multiple components”).
- **Grafana**: `grafana/README.md`, `grafana/dalc-agent-overview.json` (if panel/row structure changes).
- **Docs**: `docs/spec-test-traceability.md` if requirement IDs or evidence paths change.
- **CI**: `scripts/check_spec_traceability.py` must pass after spec/test updates.
