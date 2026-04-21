## ADDED Requirements

### Requirement: [DALC-REQ-CHART-RTV-005] Consumer observability plugin Helm surface

The Helm library chart SHALL expose an **additive**, **disabled-by-default** subtree under **`observability.plugins`** for wiring consumer observability plugins (entry-point allowlists and optional configuration references) consistent with **ADR 0014**’s single **`observability.plugins`** tree.

When **`consumerPlugins.enabled`** is false, rendered manifests SHALL NOT inject environment variables solely for consumer plugin enablement except where operators add unrelated **`extraEnv`** overrides.

#### Scenario: Operator enables consumer plugins with optional entry-point filter

- **WHEN** **`observability.plugins.consumerPlugins.enabled`** is **true** and **`entryPoints`** lists one or more entry-point names
- **THEN** rendered manifests SHALL expose those selections to the runtime via documented **`HOSTED_AGENT_*`** environment variables so the runtime’s allowlist matches operator intent

#### Scenario: Defaults remain off

- **WHEN** an operator applies chart defaults without overrides
- **THEN** **`observability.plugins.consumerPlugins.enabled`** SHALL default to **false** and SHALL not introduce new required Secrets for consumer plugins
