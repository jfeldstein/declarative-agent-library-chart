## ADDED Requirements

### Requirement: [DALC-REQ-CUSTOM-O11Y-001] Consumer observability plugins discovered via PEP 621 entry points

The hosted agent runtime SHALL support registering optional **consumer observability plugins** through **`[project.entry-points."declarative_agent.observability_plugins"]`**, resolving **named** entry points from **installed distributions** only.

The runtime SHALL NOT treat unstructured Helm/ConfigMap strings as authoritative module paths for loading observability plugins in this capability’s default configuration.

#### Scenario: Disabled when allowlist empty

- **WHEN** **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS`** is unset or empty after parsing
- **THEN** the runtime SHALL NOT import entry-point modules solely for observability plugin discovery

#### Scenario: Enabled loads selected entry points

- **WHEN** the allowlist is non-empty
- **THEN** the runtime SHALL load each listed entry-point **name** that exists in the declared entry-point group from installed distributions

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-002] Hook lifecycle matches attach-only bus bootstrap

Consumer observability plugins SHALL integrate with **`build_event_bus`** by registering on the **post-bus** path only: **`attach_consumer_plugins`** runs after **`attach_plugins_from_config`** (built-in Prometheus, Langfuse, Weights & Biases when enabled).

Built-in wiring from **`agent.observability.plugins.wiring`** SHALL run **before** consumer **`attach`** hooks.

#### Scenario: Built-in attach runs before consumer attach

- **WHEN** **`build_event_bus`** runs with consumer plugins configured
- **THEN** the runtime SHALL call built-in **`attach_plugins_from_config`** before invoking consumer **`attach`** hooks

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-003] Process kind passed to hooks

Consumer observability hooks SHALL receive **`process_kind`** **`agent`** or **`scraper`** matching **`build_event_bus`** usage.

#### Scenario: Scraper process receives scraper kind

- **WHEN** **`ensure_scraper_observability`** constructs the bus
- **THEN** consumer hooks SHALL be invoked with **`process_kind`** equal to **`scraper`**

#### Scenario: Agent and RAG paths use agent kind

- **WHEN** **`ensure_agent_observability`** constructs the bus (including RAG HTTP service bootstrap that shares agent observability initialization)
- **THEN** consumer hooks SHALL be invoked with **`process_kind`** equal to **`agent`**

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-004] Opt-in configuration independent of unrelated plugins

Enabling consumer plugins via a non-empty entry-point allowlist SHALL NOT require Langfuse, Weights & Biases, Grafana, log-shipping, or Prometheus credentials when those integrations remain disabled.

#### Scenario: Minimal deploy unchanged

- **WHEN** the consumer plugin entry-point allowlist is empty (default)
- **THEN** the runtime SHALL NOT require additional Secrets or environment variables solely for consumer plugin wiring beyond existing minimal agent/scraper configuration

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-005] Failure isolation for broken consumer plugins

When consumer plugins are configured, the runtime SHALL catch exceptions from individual entry-point loads or hook invocations, emit a structured diagnostic, and continue startup (**no fail-fast strict mode**).

---

### Requirement: [DALC-REQ-CUSTOM-O11Y-006] Shared Prometheus plugin remains integration-agnostic

This capability SHALL NOT require adding integration-specific metric families inside **`agent.observability.plugins.prometheus`** as part of consumer plugin support; **ADR 0015** continues to govern shared Prometheus neutrality.

#### Scenario: Consumer metrics stay in consumer code

- **WHEN** a consumer observability plugin exposes Prometheus metrics
- **THEN** those metric families SHALL be registered from consumer-owned modules rather than by extending shared integration-specific APIs inside **`agent.observability.plugins.prometheus`**
