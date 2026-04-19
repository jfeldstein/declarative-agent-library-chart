## 1. Specification

- [x] 1.1 Delta spec draft for `dalc-observability-lifecycle-events` (`specs/dalc-observability-lifecycle-events/spec.md`).
- [x] 1.2 Design artifact with event vocabulary, legacy→`dalc_*` metric mapping table, and Helm plugin scaffold notes.

## 2. Implementation

- [x] 2.1 `agent.observability.events` (`EventName`, `LifecycleEvent`, `SyncEventBus`).
- [x] 2.2 `agent.observability.middleware` publish helpers; `bootstrap` for agent vs scraper buses.
- [x] 2.3 Legacy Prometheus subscribers delegating to existing `agent.metrics` / `agent.rag.metrics` / `agent.scrapers.metrics`.
- [x] 2.4 Refactor call sites (app, triggers, `trigger_steps`, LLM callback, RAG middleware, scrapers, subagent exec); remove inline Slack tool metric calls from `support.py`.
- [x] 2.5 Helm `observability.plugins` scaffold in `values.yaml` + `values.schema.json`.

## 3. Verification

- [x] 3.1 `uv run pytest` (helm/src).
- [x] 3.2 `python3 scripts/check_spec_traceability.py`.

## 4. Promotion (follow-up, when ready)

- [ ] 4.1 Merge delta into `openspec/specs/dalc-observability-lifecycle-events/spec.md`, matrix rows, test docstrings per ADR 0003.
