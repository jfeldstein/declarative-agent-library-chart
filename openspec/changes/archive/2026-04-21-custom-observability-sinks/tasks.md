## Status

**Completed and promoted** (2026-04-21): normative requirements live under **`openspec/specs/dalc-custom-observability-plugins/spec.md`** and **`openspec/specs/dalc-chart-runtime-values/spec.md`** (**`[DALC-REQ-CHART-RTV-005]`** consumer plugins list). The checklist below reflects the original plan; implementation diverged (attach-only hooks, list-shaped **`consumerPlugins`**, no strict fail-fast mode).

## 1. Phase 1 — Runtime loader and hook protocol

- [x] 1.1 **`ConsumerPluginsSettings`** on **`ObservabilityPluginsConfig`**; **`plugins_config_from_env`** (**`HOSTED_AGENT_OBSERVABILITY_PLUGINS_*`**).
- [x] 1.2 **`importlib.metadata`** discovery for **`declarative_agent.observability_plugins`**; **`attach`** hook (attach-only bootstrap).
- [x] 1.3 **`attach_consumer_plugins`** after **`attach_plugins_from_config`** in **`build_event_bus`**.
- [x] 1.4 Non-strict: per-entry-point **`structlog`** warning and continue (no env-gated strict mode).
- [x] 1.5 Pytest: disabled skips discovery; enabled allowlist loads hooks; broken entry points logged, startup continues.

## 2. Phase 2 — Packaging and Helm wiring

- [x] 2.1 **`helm/src/pyproject.toml`** entry-point group + noop test entry.
- [x] 2.2–2.4 Helm **`observability.plugins.consumerPlugins`** (string list), schema, templates (agent, scraper, RAG).
- [x] 2.5 Helm unittest / examples (**`examples/with-plugins`**, **`helm/tests/with_plugins_test.yaml`**).

## 3. Phase 3 — Examples, docs, traceability

- [x] 3.1 **`examples/with-plugins`** + consumer wheel demo.
- [x] 3.2 **`docs/observability.md`** and ADR cross-links.
- [x] 3.3 Promoted specs + **`docs/spec-test-traceability.md`** + pytest / Helm evidence.

## 4. Verification gates

- [x] 4.1 **`uv run pytest`** (**`helm/src`**) with coverage floor.
- [x] 4.2 Helm **`ct`** / **`helm unittest`** parity for touched charts.
