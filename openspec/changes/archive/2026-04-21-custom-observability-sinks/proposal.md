## Status (promotion)

**Promoted 2026-04-21.** Canonical requirements live in **`openspec/specs/dalc-custom-observability-plugins/spec.md`** and **`openspec/specs/dalc-chart-runtime-values/spec.md`** (**`[DALC-REQ-CHART-RTV-005]`**). Shipped behavior uses **attach-only** consumer hooks, a **non-empty entry-point name list** for discovery, and **[ADR 0017](../../../../docs/adrs/0017-gate-at-call-site-for-optional-capabilities.md)** for built-in plugin gating; this folder is archived for history.

---

## Why

Consumers of the Declarative Agent **library chart** who need additional **observability sinks** (subscribers on `SyncEventBus`, optional metrics surfaces, or future OTLP bridges) today must **fork or patch** `agent.observability.plugins.wiring`—the only composition root that wires built-in plugins—because there is no supported extension point. That blocks upgrades and violates the intent of **ADR 0014** (single Helm tree `observability.plugins.*`, opt-in semantics) and **ADR 0015** / **ADR 0011** neutrality (shared plugins stay vendor-agnostic; cardinality and PII rules stay centralized). This change introduces a **first-class, disabled-by-default** mechanism to register **installed-distribution** hooks without modifying upstream wiring.

## What Changes

- **Runtime**: Discover and invoke **optional consumer observability hooks** (mirroring the existing **`declarative_agent.tools`** entry-point pattern in `helm/src/pyproject.toml`) so third-party wheels can subscribe during the same lifecycle phases as built-ins: **pre-bus queue** (`enqueue_*`) and **post-bus attach** (`attach_*`), per `bootstrap.build_event_bus`.
- **Configuration**: Additive, **opt-in** fields under **`ObservabilityPluginsConfig`** / env (and matching Helm values), without requiring unrelated integration credentials when a hook is off.
- **Chart**: Minimal **additive** keys under **`observability.plugins`** (or a dedicated subtree such as **`externalHooks`**) plus schema updates; existing deployments remain valid with zero behavioral change when hooks are absent.
- **Examples**: An **`examples/*`** chart (or extension of an existing example) demonstrates registering a **no-op or trivial** consumer plugin via entry points—proving the pattern without pulling vendor SDKs into core.
- **Documentation**: Cross-links to ADR 0014 / 0015, Langfuse/trace PII docs, and explicit **non-goals** (no arbitrary code execution from ConfigMap strings).

## Capabilities

### New Capabilities

- `dalc-custom-observability-plugins`: Extension discovery (PEP 621 entry-point group), hook API contract, lifecycle ordering relative to `enqueue_plugins_from_config` / `attach_plugins_from_config`, process-kind matrix (`agent` vs `scraper`; RAG service posture called out), failure modes (fail-fast vs log-and-disable), security constraints (prefer entry points over raw import paths), compatibility with ADR 0014 opt-in semantics and ADR 0015 neutral metrics rules for code living in **shared** Prometheus paths.

### Modified Capabilities

- `dalc-chart-runtime-values`: **Additive** Helm contract for wiring env (and optional opaque JSON / Secret-backed config keys) that enable listed entry-point groups or named hooks without breaking existing **`observability.plugins.*`** behavior.

## Impact

- **Python**: `agent.observability.bootstrap`, `plugins_config.py`, new small loader module(s); **`wiring.py`** remains the built-in composition root but **delegates** to a generic “invoke registered hooks” step so consumers need not fork it.
- **Packaging**: New **`[project.entry-points."declarative_agent.observability_plugins"]`** (exact group name finalized in design) documented alongside **`declarative_agent.tools`**.
- **Helm**: `helm/chart/values.yaml`, `values.schema.json`, templates for env injection when hooks are enabled.
- **Tests**: Pytest for discovery, disabled default, misconfiguration; optional Helm unittest for values→env.
- **Security / ops**: Arbitrary string import paths are **out of scope** as a supported mechanism; entry points tied to **installed packages** are the recommended path.
