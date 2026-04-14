## Context

Today `helm/chart/values.yaml` uses **`o11y`** for Prometheus annotations, JSON log format, and `ServiceMonitor`, and a separate **`observability`** object for Postgres URL, checkpoints, W&B, Slack feedback emoji map, ATIF export, shadow rollout tuning, and **`labelRegistry`**. The runtime Python package is still named `hosted_agents.observability` and includes both “product integrations” (W&B, checkpoints, Slack) and naming that collides with the chart’s intended meaning of *cluster* observability.

`labelRegistry` (values) renders to ConfigMap key `label-registry.json` and **`HOSTED_AGENT_LABEL_REGISTRY_JSON`**, consumed by `hosted_agents.observability.label_registry` as a **versioned human-feedback label taxonomy** (e.g. positive / negative / neutral), not Kubernetes labels and not the same env as `HOSTED_AGENT_OPERATIONAL_MAPPER_FLAGS_JSON`.

## Goals / Non-Goals

**Goals:**

- Reserve the Helm key **`observability`** exclusively for **Kubernetes/Prometheus** concerns (annotations, `ServiceMonitor`, structured log toggle).
- Model **checkpoints** and **wandb** as **first-class top-level values** with a clear migration from the old nested paths.
- Co-locate **Slack feedback** configuration under **`scrapers.slack.feedback`**.
- Remove **ATIF export** and **shadow** from the chart and runtime.
- Rename values keys so **`labelRegistry`** is discoverable (e.g. `feedbackLabelRegistry` under `scrapers.slack.feedback`) and document its purpose.

**Non-Goals:**

- Renaming the Python package `hosted_agents.observability` in this change (optional follow-up to reduce import confusion).
- Changing W&B or checkpoint **environment variable** names unless required for consistency (prefer keeping existing `HOSTED_AGENT_*` contracts).

## Decisions

1. **`o11y` → `observability` (Helm only)**  
   **Rationale**: Matches operator language for metrics/logs/scrape. **Alternative**: keep `o11y` to avoid churn—rejected because the user explicitly wants the word *observability* for this layer.

2. **Top-level `checkpoints` and `wandb`**  
   **Rationale**: These are independent product toggles, not “observability” in the Prometheus sense. **Alternative**: nest both under `runtime:`—rejected as less explicit for Helm consumers.

3. **`scrapers.slack.feedback` for Slack + label registry**  
   **Rationale**: Slack reaction ingestion is part of the scraper/slack surface; feedback emoji maps and the feedback label registry belong beside it. **Alternative**: top-level `slack:`—rejected to avoid duplicating the `scrapers` domain.

4. **Remove ATIF and shadow entirely**  
   **Rationale**: User request to delete features and simplify values. **Migration**: document removal in changelog; operators using shadow/ATIF must pin an older chart or reintroduce settings via `extraEnv` if they maintain a fork.

5. **ConfigMap keys**  
   **Rationale**: Remove `shadow-allow-tenants.json` from ConfigMap when shadow is removed; keep or rename `label-registry.json` to match the new values path (implementation detail in tasks).

## Risks / Trade-offs

- **[Risk] Breaking all existing values files** → Mitigation: clear migration table in README and one release note; optional short-lived compatibility shim in templates only if the project policy allows (default: **no** shim to keep templates simple).
- **[Risk] Spec IDs and helm-unittest comments** → Mitigation: update `docs/spec-test-traceability.md` and test YAML when promoting specs; run `python3 scripts/check_spec_traceability.py`.
- **[Risk] Confusion between Helm `observability` and Python `ObservabilitySettings`** → Mitigation: consider renaming the dataclass in a follow-up (`RuntimeIntegrationSettings` or split settings); document in this change’s tasks if in scope.

## Migration Plan

1. Inventory references to `o11y` and old `observability.*` in charts, examples, docs, and scripts.
2. Apply template and values renames; update example charts and unittest assertions.
3. Remove shadow/ATIF code paths and tests; delete obsolete docs sections.
4. Verify `helm unittest`, `ct lint` (if applicable), and Python tests for the runtime.

## Open Questions

- Whether to add a **temporary** Helm compatibility layer mapping deprecated keys—**default assumption: none** unless maintainers require it.
- Final name for the feedback label registry in values (`feedbackLabelRegistry` vs `labelRegistry` under `scrapers.slack.feedback`).
