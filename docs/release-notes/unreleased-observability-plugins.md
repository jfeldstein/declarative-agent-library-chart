# Release notes draft — observability lifecycle events & plugins

**Target audience:** operators upgrading the Helm library chart agent/RAG/scraper stack alongside **`openspec/changes/observability-lifecycle-events`** (Phase 1+) and any parallel **Helm/runtime** work that later promotes under **`openspec/changes/`**.

This file is a **skeleton**: fill in concrete tokens, Helm paths, and PromQL deltas before tagging a release; link to **`docs/observability.md`**, **`docs/adrs/0014-observability-plugin-architecture.md`**, and **`docs/release-notes/`** successors when published.

---

## Highlights (TBD)

- Lifecycle **event bus** instrumentation with backward-compatible **`agent_runtime_*`** series where applicable.
- Helm **`agent.observability.plugins.*`** scaffold for future Langfuse / Grafana / log-shipping integrations (defaults **false**).

---

## Breaking changes

| Topic | Before | After | Operator action |
| ----- | ------ | ----- | ---------------- |
| **Prometheus metric names** | _(list prior series touched by the release — e.g. renamed histograms or dropped labels)_ | _(new canonical names / labels)_ | Update **Prometheus** rules and **Alertmanager** routes; refresh **`grafana/*.json`** imports that embed PromQL (see **`docs/observability.md`** metric tables). |
| **Helm W&B / Langfuse env** | Legacy short names (`HOSTED_AGENT_WANDB_ENABLED`, `HOSTED_AGENT_LANGFUSE_*`) | Chart emits **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED`** / **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_*`**; runtime still accepts legacy names when canonical vars are unset | **`helm diff upgrade`** on agent Deployment env; custom **`extraEnv`** using legacy names keeps working. |
| **Dashboards** | Imported **`grafana/dalc-overview.json`**, **`grafana/cfha-token-metrics.json`**, _(others)_ | Panels referencing renamed metrics or labels | **Re-import** refreshed JSON from this repo revision; verify datasource UIDs per **`grafana/README.md`**. |

_Add rows per release for scraper-only or RAG-only series if they change._

---

## Upgrade checklist (TBD)

1. Run **`helm dependency build`** on parent charts; diff rendered manifests for **`agent.observability.plugins`** and **`wandb.*`**.
2. **`kubectl`**: roll agent Deployment/RAG/scraper CronJobs as needed; confirm **`GET /metrics`** on each workload still scraped.
3. Grafana: re-import dashboards; validate **Explore** queries against staging Prometheus.
4. _(Optional)_ **`python3 scripts/check_spec_traceability.py`** when normative specs move for the same release.

---

## References

- **`docs/observability.md`** — metric catalog, scrape annotations, lifecycle architecture intro.
- **`docs/adrs/0014-observability-plugin-architecture.md`** — plugin tree, tool boundary, out-of-scope alerts/checkpointing.
- **`openspec/changes/observability-lifecycle-events/`** — Phase 1 OpenSpec draft; sibling promotion directories TBD when chart wiring lands.
