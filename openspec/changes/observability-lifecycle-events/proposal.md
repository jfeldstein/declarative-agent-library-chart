## Why

Hosted agent observability is fragmented across tool modules, triggers, LLM callbacks, and scrapers with direct Prometheus calls. A **vendor-agnostic lifecycle event bus** with optional plugins unifies emission sites, bounds labels/redaction at the middleware boundary, and unlocks parallel provider work (Prometheus, Langfuse, W&B, Grafana, log shipping).

## What Changes

- **Phase 1 (this change series):** Introduce `SyncEventBus`, stable `EventName` vocabulary, publish helpers under `agent.observability.middleware`, and **legacy subscribers** that mirror existing `agent_runtime_*` metrics so behavior and tests stay unchanged.
- **Helm:** Scaffold `observability.plugins.*` (all disabled by default) so parallel chart/agent work does not conflict on the values root.
- **Normative delta:** Draft capability `dalc-observability-lifecycle-events` under `specs/` (promotion to `openspec/specs/` follows the usual gate).

## Capabilities

### New Capabilities

- `dalc-observability-lifecycle-events` — event vocabulary, middleware ownership, agent vs scraper bus instances, graceful degradation when plugins are absent.

### Modified Capabilities

- (Promotion step later) specs that reference metric names will move in Phase 2 (`dalc_*` Prometheus plugin).

## Impact

- **Python:** New packages `agent.observability.events`, `agent.observability.middleware`, bootstrap + legacy metric bridges.
- **Tests:** Existing pytest and traceability checks remain green; new unit tests cover the bus and legacy wiring.
- **Helm:** Default render unchanged when all plugin toggles are false.
