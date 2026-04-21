## ADDED Requirements

### Requirement: [DALC-REQ-CUSTOM-O11Y-001] Consumer observability plugins discovered via PEP 621 entry points

The hosted agent runtime SHALL support registering optional **consumer observability plugins** through a dedicated PEP 621 entry-point group (mirroring the existing **`declarative_agent.tools`** pattern), such as **`declarative_agent.observability_plugins`**, resolving **named** entry points from **installed distributions** only.

The runtime SHALL NOT treat unstructured Helm/ConfigMap strings as authoritative module paths for loading observability plugins in this capability’s default configuration.

#### Scenario: Disabled by default

- **WHEN** consumer observability plugins are not enabled in **`ObservabilityPluginsConfig`**
- **THEN** the runtime SHALL NOT import entry-point modules solely for observability plugin discovery

#### Scenario: Enabled loads installed entry points

- **WHEN** consumer observability plugins are enabled and an optional allowlist is empty or unset
- **THEN** the runtime SHALL load every entry point registered under the declared entry-point group from installed distributions

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-002] Hook lifecycle matches enqueue-then-attach bus bootstrap

Consumer observability plugins SHALL integrate with **`build_event_bus`** using two phases consistent with **`enqueue_plugins_from_config`** and **`attach_plugins_from_config`**:

1. **Enqueue phase** — before **`SyncEventBus()`** is constructed, consumer hooks MAY register **`(EventName, Subscriber)`** pairs through the same callback shape used for built-in **pre-bus** subscriptions.
2. **Attach phase** — after the bus is constructed and queued subscriptions are applied, consumer hooks MAY receive the **`SyncEventBus`** instance for additional **`subscribe`** calls or post-bus initialization.

Built-in wiring from **`agent.observability.plugins.wiring`** SHALL run **before** consumer hooks within each phase (enqueue built-ins, then consumer enqueue; attach built-ins, then consumer attach).

#### Scenario: Built-in enqueue runs before consumer enqueue

- **WHEN** **`build_event_bus`** runs with consumer observability plugins enabled
- **THEN** the runtime SHALL call built-in **`enqueue_plugins_from_config`** before invoking consumer enqueue hooks so **`SyncEventBus.publish`** invokes handlers in registration order with built-in enqueue registrations applied first

#### Scenario: Built-in attach runs before consumer attach

- **WHEN** **`build_event_bus`** runs with consumer observability plugins enabled
- **THEN** the runtime SHALL call built-in **`attach_plugins_from_config`** before invoking consumer attach hooks

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-003] Process kind passed to hooks

Consumer observability hooks SHALL receive the active **`process_kind`** discriminator **`agent`** or **`scraper`** matching **`build_event_bus`** usage so implementations can skip work or avoid heavy imports per process.

#### Scenario: Scraper process receives scraper kind

- **WHEN** **`ensure_scraper_observability`** constructs the bus
- **THEN** consumer hooks SHALL be invoked with **`process_kind`** equal to **`scraper`**

#### Scenario: Agent and RAG paths use agent kind

- **WHEN** **`ensure_agent_observability`** constructs the bus (including RAG HTTP service bootstrap that shares agent observability initialization)
- **THEN** consumer hooks SHALL be invoked with **`process_kind`** equal to **`agent`**

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-004] Opt-in configuration independent of unrelated plugins

Enabling consumer observability plugins SHALL NOT require Langfuse, Weights & Biases, Grafana, log-shipping, or Prometheus plugin credentials or Secrets when those integrations remain disabled per **ADR 0014** opt-in semantics.

#### Scenario: Minimal deploy unchanged

- **WHEN** consumer observability plugins are disabled (default)
- **THEN** the runtime SHALL NOT require additional Secrets or environment variables solely for consumer plugin wiring beyond existing minimal agent/scraper configuration

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-005] Failure handling for broken consumer plugins

When consumer observability plugins are enabled, the runtime SHALL isolate failures from individual entry-point modules such that a single faulty consumer plugin does not prevent service startup unless the operator enables an explicit **strict** failure mode via environment configuration.

In the default (non-strict) mode, the runtime SHALL log a structured diagnostic and skip the failing entry point.

#### Scenario: Strict mode fails closed

- **WHEN** strict failure mode is enabled and an entry point raises during registration
- **THEN** process startup SHALL fail with a non-zero exit consistent with other fatal bootstrap errors

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-006] Shared Prometheus plugin remains integration-agnostic

This capability SHALL NOT require adding integration-specific metric families or helper names to **`agent.observability.plugins.prometheus`** as part of consumer plugin support; **ADR 0015** continues to govern shared Prometheus plugin neutrality.

Custom metrics emitted from consumer packages SHALL remain outside shared plugin modules unless a future change explicitly promotes them with separate review.

#### Scenario: Consumer metrics stay in consumer code

- **WHEN** a consumer observability plugin exposes Prometheus metrics
- **THEN** those metric families SHALL be registered from consumer-owned modules rather than by extending shared integration-specific APIs inside **`agent.observability.plugins.prometheus`**
