## Context

- **Bootstrap** (`agent.observability.bootstrap.build_event_bus`) builds a list of `(EventName, Subscriber)` via **pre-bus** registration, instantiates **`SyncEventBus`**, subscribes queued handlers, then calls **`attach_plugins_from_config`** for plugins that need an existing bus (Langfuse, W&B on agent only).
- **`wiring.py`** is today the **only** place that imports optional providers and connects them to **`ObservabilityPluginsConfig`**; library consumers who add sinks must fork it.
- **ADR 0014** defines the **`observability.plugins.*`** Helm tree (booleans default false, opt-in semantics). **ADR 0015** keeps **shared** Prometheus plugin code integration-neutral; **ADR 0011** governs cardinality and labels.
- **Tools** already use PEP 621 **`[project.entry-points."declarative_agent.tools"]`** (`helm/src/pyproject.toml`), establishing a precedent for discoverable extensions without editing core dispatch.

## Goals / Non-Goals

**Goals:**

- Allow **downstream distributions** (extra Python packages layered on the runtime image) to register **SyncEventBus** subscribers and optional attach logic **without forking** `wiring.py`.
- Keep **built-in** wiring centralized in **`wiring.py`** while adding a **single generic delegation** (loader) callable from **`enqueue_plugins_from_config`** / **`attach_plugins_from_config`** or immediately adjacent in bootstrap—so upstream merges stay mechanical.
- Preserve **disabled-by-default** behavior and **ADR 0014**: enabling consumer hooks **SHALL NOT** force unrelated provider credentials (Langfuse, W&B, …).
- Prefer **entry-point discovery** keyed to **installed distributions** over ConfigMap-supplied import strings (auditability, supply-chain alignment).
- Document lifecycle ordering, **agent vs scraper** (`ProcessKind`), and that the **RAG HTTP service** currently bootstraps via **`ensure_agent_observability`** (same singleton path as the main agent—not a third bus kind today).

**Non-Goals:**

- **Executing arbitrary code from Helm values** (e.g. raw `importlib.import_module` strings from ConfigMaps): **explicitly unsupported** in v1; operators install wheels that declare entry points.
- **Vendor-specific metric families inside the shared Prometheus plugin** as part of this change: remains governed by **ADR 0015**; consumer sinks live in **their** packages.
- **Sidecar-only observability** with **no** in-process bus subscription: remains a valid deployment pattern but **out of scope** for this hook API (document as alternative when bus access is unnecessary).
- **Changing** `EventName` contracts or synchronous delivery semantics.

## Decisions

### D1 — Discovery mechanism (recommended: PEP 621 entry points)

**Choice:** Introduce **`[project.entry-points."declarative_agent.observability_plugins"]`** (name finalized to match **`declarative_agent.tools`** style). Each entry names a **distribution-provided** registration object or callable.

**Alternatives considered:**

| Option | Why not primary |
|--------|------------------|
| Env var listing dotted import paths | High risk (arbitrary code), weak anchor to installed packages, harder ops review |
| Chart-only sidecars | Cannot subscribe to **in-process** `SyncEventBus`; fine as complement, not replacement |
| Auto-import all modules under a namespace | Implicit imports break lazy-loading goals and pytest isolation |

**Whitelist:** Optional env **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS`** (exact name TBD in implementation) listing **entry-point names** to load when the master toggle is on; empty means **all** entries in the group (still requires master enable—see D4).

### D2 — Hook API shape

**Choice:** Each entry point resolves to an object implementing a small **protocol** (or duck-typing contract) with two optional hooks—mirroring **`enqueue_plugins_from_config`** / **`attach_plugins_from_config`**:

1. **`enqueue(process_kind, cfg, enqueue_subscription)`** — `enqueue_subscription` matches **`Callable[[EventName, Subscriber], None]`** used today; runs **before** `SyncEventBus()` exists; use for Prometheus-style subscribers that register metrics collectors **before** first scrape-related setup (same pattern as `enqueue_prometheus_subscriptions`).
2. **`attach(process_kind, cfg, bus)`** — runs **after** the bus exists and **after** queued subscriptions are installed; use for bridges that need **`SyncEventBus.subscribe`** directly or post-bus initialization.

Both hooks receive **`process_kind: Literal["agent","scraper"]`** and parsed **`ObservabilityPluginsConfig`** (possibly extended with an **opaque** dict or JSON-backed blob for consumer-specific keys—see D3).

**Order:** Invoke **built-in** `enqueue_plugins_from_config` **first**, then **consumer** enqueue hooks (deterministic baseline, then extensions). Same for attach: **built-ins** then **consumers**.

**Alternatives:** Single callable `(phase, …)` enum—rejected as unnecessarily awkward for callers familiar with **`wiring.py`**.

### D3 — Configuration surface

**Choice:** Extend **`ObservabilityPluginsConfig`** with an **additive** subtree, e.g. **`consumer_plugins: ConsumerPluginsSettings`** containing at minimum:

- **`enabled: bool`** (default **False**).
- **`entry_point_allowlist: tuple[str, …]`** optional mirror of env whitelist (parsed from env in **`plugins_config_from_env`**).
- **`extra: Mapping[str, str]`** or **`json_config: str | None`** for **versioned** opaque JSON from env—**only when** a deployment needs structured config without new top-level Helm keys; chart may map a **Secret** key or **`extraEnv`** pattern.

**Helm:** Add **`observability.plugins.consumerPlugins`** (camelCase in YAML) with **`enabled`**, optional **`entryPoints[]`** (names), optional **`configJsonSecret`** / inline **`configJson`** for advanced demos—**all absent / false** in defaults.

**Validation:** Strict JSON schema optional in later phase; v1 may parse leniently with **log-and-disable** for malformed opaque config.

### D4 — Failure modes

**Choice (default):** **Log structured warning + skip** failing entry points so a broken optional wheel does not brick the agent (**aligns with opt-in “additive” posture**). Provide **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_STRICT=true`** (or similar) for environments that prefer **fail-fast** startup.

**Alternatives:** Always fail-fast—rejected as hostile to optional telemetry in dev clusters.

### D5 — Lazy imports / scraper isolation

**Choice:** The **loader** only **`importlib.metadata.entry_points()`** resolves and imports **selected** entry-point **modules** when **`consumer_plugins.enabled`** is true. Entry-point implementations **SHOULD** lazy-import heavy SDKs inside **`attach`** / **`enqueue`** bodies. Document in **runtime guidance** (not enforced by type system).

**RAG:** Uses **`ensure_agent_observability`** → **`process_kind="agent"`**; scraper CronJobs use **`"scraper"`**. Hooks that are agent-only **SHOULD** no-op when `process_kind == "scraper"` without importing heavy deps.

### D6 — Relationship to ADR 0015

**Choice:** Consumer packages **may** emit custom metrics from their own modules; code **merged into** `agent.observability.plugins.prometheus` remains subject to **ADR 0015** (no new vendor-specific families in shared plugin). Review checklist: if a metric belongs in **shared** exporter, keep labels consistent with **`dalc_tool_calls_*`** and **`tool`** catalog ids.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Entry-point collisions / double registration | Document namespacing; optional allowlist only loads vetted names |
| Import-time side effects in third-party plugins | Strict / tests in example; document “no work at import time” |
| `values.schema.json` uses **`additionalProperties: false`** under **`plugins`** | Any new Helm key must be **explicitly** listed in schema (not a free-form bag) |
| Opaque JSON config hides PII mistakes | Docs cross-link Langfuse/trace redaction docs; urge bounded fields |

## Migration Plan

1. **Ship loader disabled by default** — zero behavior change for existing releases.
2. **Enable** in a consumer chart by setting **`observability.plugins.consumerPlugins.enabled=true`**, installing a wheel with entry points, and optionally setting allowlist env via template.
3. **Rollback** — disable flag; remove bad wheel; no data migration.

## Open Questions

- Exact env var names for master toggle / allowlist / strict mode (keep **`HOSTED_AGENT_OBSERVABILITY_*`** prefix consistency with **`plugins_config_from_env`**).
- Whether **`consumerPlugins`** should live under **`observability.plugins`** vs top-level **`observability.consumerPlugins`** — **prefer nested under `plugins`** for ADR 0014 alignment (single tree).
