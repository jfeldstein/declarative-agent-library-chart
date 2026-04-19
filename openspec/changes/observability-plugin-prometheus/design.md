## Behavior

- **Bus subscription:** `register_prometheus_agent_plugin` / `register_prometheus_scraper_plugin` mirror prior legacy subscribers; HTTP/RAG/trigger integrations continue to publish lifecycle events unchanged.
- **Naming:** `dalc_*` families per repository ADR 0011 (updated) and promoted **`dalc-runtime-token-metrics`** / **`dalc-agent-o11y-scrape`** specs.
- **HTTP surface:** FastAPI **`/metrics`** routes register only when **`plugins_config_from_env().prometheus.enabled`** is true; RAG ASGI matches.
- **Helm:** chart sets **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED`** when **`observability.plugins.prometheus.enabled`** is true; scrape annotations and **`ServiceMonitor`** rendering require **both** **`prometheusAnnotations.enabled`** and **`plugins.prometheus.enabled`**.

## Traceability

Promoted SHALL rows updated under **`openspec/specs/dalc-agent-o11y-scrape/spec.md`**, **`openspec/specs/dalc-runtime-token-metrics/spec.md`**, with matrix rows in **`docs/spec-test-traceability.md`** and pytest / module citations per **[DALC-VER-005]**.
