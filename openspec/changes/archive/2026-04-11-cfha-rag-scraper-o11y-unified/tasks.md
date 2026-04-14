## 1. Helm helpers and templates

- [x] 1.1 Add named template (e.g. `declarative-agent-library.anyScraperEnabled` / `ragFromScrapers`) true iff `scrapers.jobs` has any `enabled: true`
- [x] 1.2 Gate `rag-deployment.yaml`, `rag-service.yaml`, and `rag-servicemonitor.yaml` on that helper instead of `.Values.rag.enabled`
- [x] 1.3 Replace `.Values.rag.*` tunables with `.Values.scrapers.ragService.*` (replicaCount, service, resources) in RAG templates
- [x] 1.4 Replace RAG annotation condition with `o11y.prometheusAnnotations.enabled` (remove `rag.prometheusAnnotations` usage)
- [x] 1.5 Update `ragInternalBaseUrl` / `rag` helpers in `_helpers.tpl` to use scraper gate + `scrapers.ragService.service.port`

## 2. Values and schema

- [x] 2.1 Remove top-level `rag` from `helm/chart/values.yaml`; add `scrapers.ragService` defaults matching prior RAG defaults
- [x] 2.2 Update `values.schema.json`: drop `rag`; add `scrapers.ragService` properties; keep `scrapers.jobs` as today
- [x] 2.3 Update chart README / comments that mention `rag.enabled` or `rag.prometheusAnnotations`

## 3. Examples and CI

- [x] 3.1 Update `examples/with-observability`, `examples/with-scrapers`, and any other example `values.yaml` to use `scrapers.jobs` (≥1 enabled where RAG is needed) and `scrapers.ragService`; drop top-level `rag`
- [x] 3.2 Adjust `ci.sh` / `helm template` checks if manifest counts or grep patterns depended on `rag.enabled`
- [x] 3.3 Update `helm/src/tests/scripts/prometheus-kind-o11y-values.yaml` and `integration_kind_o11y_prometheus.sh` if values shape changed

## 4. Docs and observability artifacts

- [x] 4.1 Update `docs/observability.md` and `grafana/README.md` to describe unified `o11y.prometheusAnnotations` for agent + RAG
- [x] 4.2 Update `docs/development-log.md` when the change is applied

## 5. Spec sync on archive (apply follow-up)

- [x] 5.1 When archiving, merge `specs/cfha-rag-from-scrapers/spec.md` into `openspec/specs/` and apply `cfha-agent-o11y-scrape` delta to the canonical spec per project OpenSpec workflow
