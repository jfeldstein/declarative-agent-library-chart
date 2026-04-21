# ADR 0017: Gate optional capabilities at the call site; registrations must act or raise

## Status

Accepted

## Context

Optional runtime capabilities (observability plugins, HTTP routes, background workers) are controlled by **configuration toggles** (`enabled` flags, Helm values, env). Two styles of gating have appeared in code:

1. **Call-site gating** — `if cfg.feature.enabled: register_feature(...)` so the registration path runs only when the operator chose the feature.
2. **Registration-time gating** — `register_feature(...)` always runs, but internally returns early or no-ops when configuration is “off” or incomplete (e.g. build helper returns `None`, register checks `None` and returns).

Style (2) makes control flow harder to read: readers must open every `register_*` to learn when work happens, and **silent no-ops** can hide operator mistakes (feature enabled in Helm but secrets missing).

This ADR is **not** specific to plugins: it applies to any optional capability wired from config in application bootstrap or similar composition roots.

## Decision

1. **Primary gate at the call site**  
   Callers that own configuration (composition root, wiring module, `create_app`, etc.) **SHALL** use explicit **`if settings.enabled:`** (or equivalent) before invoking a **`register_*`**, **`attach_*`**, **`start_*`**, or other side-effecting setup whose sole purpose is to enable that capability.

2. **`register_*` / `attach_*` SHALL act when invoked**  
   Once the call-site gate passes, the registration function **SHALL** perform its wiring (subscribe, add route, bind handler). It **SHALL NOT** silently no-op because “the feature is off”—that condition is expressed by **not calling** the function.

3. **Input validation inside setup**  
   When a registration path needs to validate **inputs** (credentials shape, required URLs, mutual consistency of options), validation **MAY** live inside a dedicated builder or inside `register_*`, but **SHALL** surface failure with a **raised exception** (`ValueError`, `ConfigurationError`, etc.) with an operator-actionable message—not a silent return.

4. **Optional discovery helpers**  
   Helpers that **probe** configuration without committing to wiring (e.g. “return a client or `None` for tests or diagnostics”) **MAY** continue to return `None` when the feature is disabled or inputs are incomplete, provided **bootstrap paths** do not rely on that pattern after the operator has set **`enabled: true`**. After **`enabled`**, use a **strict** builder (or `register_*` that raises) so misconfiguration fails at startup.

## Consequences

- **Positive:** Wiring modules read as a checklist of what is active; failures are loud when operators enable a feature without required secrets.
- **Positive:** Fewer dual sources of truth (“disabled” both in `if` and inside `register`).
- **Negative:** Call sites must stay in sync when new toggles are added; reviewers should verify an explicit gate exists.
- **Related:** Observability plugin composition in **`agent.observability.plugins.wiring`** follows this ADR; see also [ADR 0014](0014-observability-plugin-architecture.md) for the Helm tree and bus shape.
