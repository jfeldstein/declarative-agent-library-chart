## Context

The library chart already centralizes Prometheus annotations under `o11y.prometheusAnnotations` and optional `ServiceMonitor`s under `o11y.serviceMonitor`. Today, specs and examples name **agent** and **RAG** explicitly; `examples/with-observability` enables scrapers so RAG deploys, and tests speak in RAG-specific terms. `grafana/README.md` tells operators Prometheus must scrape **both** targets, which reads as RAG-centric when only the agent runs. The starter dashboard JSON includes RAG panels in the same file as agent panels.

## Goals / Non-Goals

**Goals:**

- Express observability as **automatic for every enabled metrics-exporting component**: same values switches drive annotations and `ServiceMonitor` resources per deployed `Service`, with tests proving presence and absence.
- Make **helm-unittest** assert **multiple** enabled components (multiple `ServiceMonitor`s when multiple metric services exist) and **at least one** case where an optional component is off → **no** `ServiceMonitor` for that template.
- Make **Grafana** docs and artifacts **scale with components**: documentation avoids implying a fixed “pair” of targets; dashboard UX does not suggest RAG is always present (e.g. optional rows, variables, or clearly labeled sections with operator guidance).

**Non-Goals:**

- Adding `ServiceMonitor` resources for **CronJob** scraper pods (no `Service` today); future work can extend the same pattern if scrape targets change.
- Replacing Prometheus Operator with static scrape configs in product code—docs may still reference both as today.

## Decisions

1. **Spec deltas vs new capability**  
   **Decision:** Use **MODIFIED** requirements under existing `cfha-agent-o11y-scrape`, `cfha-agent-o11y-logs-dashboards`, and `cfha-helm-unittest` rather than a new top-level capability, so traceability IDs stay stable where possible and archive merges stay straightforward.

2. **Helm unittest structure**  
   **Decision:** Extend `examples/with-observability/tests/with_observability_test.yaml` with value fixtures or additional `it` blocks so one suite proves **agent + optional service** monitors when both deploy, and another proves **optional service absent** → `rag-servicemonitor.yaml` renders **zero documents** (existing `hello-world` already covers RAG SM absent; we still add an explicit **with-observability** negative path per user request).  
   **Alternative considered:** Separate example chart only for matrix tests—rejected to avoid chart sprawl; parent chart values overrides in unittest are enough.

3. **Grafana dashboard**  
   **Decision:** Prefer **Grafana row + variable** or **documented “optional section”** so operators without RAG do not see empty or misleading RAG panels; exact mechanism chosen at implementation (repeatable rows, dashboard links, or collapsible rows with filter variable).  
   **Alternative considered:** Multiple JSON dashboards per component—possible later; single import remains simpler if variable/row approach works.

4. **README wording**  
   **Decision:** Replace “scrape **both** targets” with language tied to **each enabled `Service`/scrape endpoint** produced by values, referencing `examples/with-observability` and static scrape examples without naming only RAG.

## Risks / Trade-offs

- **[Risk] Spec text becomes abstract** → **Mitigation:** Keep concrete examples (agent, scraper-gated RAG) in scenarios while stating the general rule.
- **[Risk] Dashboard variables add import friction** → **Mitigation:** Defaults preserve current single-file import; document variable defaults in README.
- **[Risk] Traceability churn** → **Mitigation:** Update `docs/spec-test-traceability.md` and test comments in the same change as spec edits; run `scripts/check_spec_traceability.py`.

## Migration Plan

1. Land spec deltas and implementation in lockstep: chart behavior should already match most of the generalized wording; focus on tests, README, and dashboard JSON/docs.
2. No data migration; Helm upgrades are values-compatible.
3. Rollback: revert commit; no schema migration.

## Open Questions

- Whether to introduce a **named “metrics components”** list in `values.yaml` for documentation-only vs code-generated ServiceMonitors—defer unless implementation needs it.
- Exact Grafana mechanism (variable vs multiple dashboards) can be finalized during `/opsx:apply` based on JSON maintainability.
