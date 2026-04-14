## Why

The Helm library chart overloads the name **observability**: `o11y` holds Kubernetes/Prometheus-oriented settings while a second key, `observability`, mixes checkpoints, Postgres, W&B, Slack feedback, ATIF export, shadow rollouts, and a feedback label registry. That naming collision confuses operators and obscures which values affect cluster observability versus runtime product integrations. This change separates concerns and reserves **observability** for metrics/logs/scrape configuration only.

## What Changes

- **BREAKING**: Rename chart values key **`o11y`** → **`observability`** for Prometheus annotations, structured JSON logs, and `ServiceMonitor` (Kubernetes/Prometheus meaning only).
- **BREAKING**: Remove the existing top-level **`observability`** block as a grab-bag; replace with explicit top-level sections:
  - **`checkpoints`**: includes `postgresUrl` (and existing checkpoint enable/backend fields currently nested under the old `observability.checkpoints`).
  - **`wandb`**: project/entity/enable flags (currently under `observability.wandb`).
- **BREAKING**: Move Slack feedback settings from `observability.slackFeedback` to **`scrapers.slack.feedback`** (feedback is tied to scraper-driven ingestion; co-locating it with `scrapers` matches product semantics).
- **Remove** Helm values and chart wiring for **`atifExport`** and **`shadow`** (and delete related runtime code, tests, ConfigMap keys, and documentation).
- **Clarify** the object today exposed as `observability.labelRegistry`: it feeds **`HOSTED_AGENT_LABEL_REGISTRY_JSON`** and implements the **human feedback label taxonomy** (`helm/src/hosted_agents/observability/label_registry.py`), not Prometheus labels. The design proposes a clearer values name and placement (under Slack feedback or an explicit feedback subsection—see `design.md`).
- Update **`helm/chart/values.schema.json`**, example charts, helm-unittest suites, CI, and docs that reference the old keys.

## Capabilities

### New Capabilities

- `cfha-chart-runtime-values`: Normative Helm values shape for **checkpoints**, **wandb**, and **Slack feedback** (under `scrapers.slack.feedback`), including removal of ATIF/shadow from the chart contract.

### Modified Capabilities

- `cfha-agent-o11y-scrape`: Update normative Helm values paths from **`o11y.*`** to **`observability.*`** for Prometheus discovery and `ServiceMonitor` (requirements that today name `o11y.prometheusAnnotations` and `o11y.serviceMonitor`).

## Impact

- **Helm**: `templates/*.yaml`, `values.yaml`, `values.schema.json`, `examples/*`, `helm/tests/chart` and example `tests/`.
- **Runtime**: `hosted_agents/observability/` (ATIF export, shadow, settings, app/trigger wiring), tests under `helm/src/tests/`.
- **Docs**: `docs/runbook-checkpointing-wandb.md`, `docs/observability.md`, chart README, ADRs if they pin old value names.
- **Specs / traceability**: Delta specs under this change; after archive, promoted `openspec/specs/` and `docs/spec-test-traceability.md` per ADR 0003.
