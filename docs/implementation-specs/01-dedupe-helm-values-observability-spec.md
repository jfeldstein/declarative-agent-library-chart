# Step 1: dedupe-helm-values-observability

`````
# Downstream LLM implementation brief: `dedupe-helm-values-observability`

## 0. Context (read first)

- **Linear checklist:** Tier **1** in `docs/openspec-implementation-order.md` — this change defines where **checkpoints**, **wandb**, and Kubernetes **observability** (metrics/logs/scrape) live in Helm values before later changes (`postgres-agent-persistence`, `scraper-cursors-durable-store`, `consolidate-naming`, …).
- **Authoritative change bundle:** `openspec/changes/dedupe-helm-values-observability/` — `proposal.md`, `design.md`, `tasks.md`, and delta specs under `specs/*/spec.md`.
- **Default:** **no** Helm compatibility shim for deprecated keys unless a maintainer explicitly decides otherwise (`design.md` open question).

## 1. Goal

**BREAKING** Helm and chart contract reshaping:

1. Rename library-chart values key **`o11y` → `observability`** **only** for Prometheus annotations, structured JSON logs toggle, and `ServiceMonitor` settings.
2. Remove the overloaded top-level **`observability`** object; replace with **`checkpoints`** (including `postgresUrl`, `enabled`, `backend`), **`wandb`**, and **`scrapers.slack.feedback`** (emoji map + feedback label registry).
3. **Delete** ATIF export and shadow rollout features from **Helm values**, **templates**, **ConfigMap keys**, **runtime**, and **tests**.
4. Keep **runtime `HOSTED_AGENT_*` env names** unless strictly necessary to rename (per `design.md` — prefer stability).

After merge/archive: promoted specs under `openspec/specs/` and `docs/spec-test-traceability.md` must align with **ADR 0003** / **DALC-VER-005** (requirement IDs on `### Requirement:` lines, matrix rows, test comments).

## 2. Entities and interfaces

### 2.1 Helm values tree (library subchart root)

Target shape (illustrative keys only — wire exact nesting to match delta specs):

```yaml
# Pseudotype: LibraryChartValues
observability:
  prometheusAnnotations: { enabled: bool }
  structuredLogs: { json: bool }
  serviceMonitor:
    enabled: bool
    interval: str
    scrapeTimeout: str
    extraLabels: { [str]: str }

checkpoints:
  postgresUrl: str
  enabled: bool
  backend: str  # e.g. memory | postgres (per existing semantics)

wandb:
  enabled: bool
  project: str
  entity: str

scrapers:
  slack:
    feedback:
      enabled: bool
      emojiLabelMap: { [str]: str }
      # Exactly one of: labelRegistry | feedbackLabelRegistry — pick one name,
      # document it, and use consistently in templates + schema + docs.
```

**Forbidden** after this change (chart contract): `atifExport`, `shadow`, top-level `o11y`, and nesting `checkpoints` / `wandb` / `postgresUrl` under a key named `observability`.

### 2.2 Template ↔ values contract

Templates that **today** read `.Values.o11y.*` **SHALL** read `.Values.observability.*` for the same semantics:

- `helm/chart/templates/deployment.yaml` (pod annotations + `HOSTED_AGENT_LOG_FORMAT`)
- `helm/chart/templates/service.yaml`
- `helm/chart/templates/servicemonitor.yaml`
- `helm/chart/templates/rag-deployment.yaml`
- `helm/chart/templates/rag-service.yaml`
- `helm/chart/templates/rag-servicemonitor.yaml`
- `helm/chart/templates/scraper-cronjobs.yaml`

Templates that **today** read `.Values.observability.{postgresUrl,checkpoints,wandb,slackFeedback,atifExport,shadow,labelRegistry}` **SHALL** be rewired:

| Concern | New values path |
|--------|------------------|
| Postgres DSN for agent | `checkpoints.postgresUrl` → `HOSTED_AGENT_POSTGRES_URL` |
| Checkpoint flags | `checkpoints.enabled`, `checkpoints.backend` |
| W&B | `wandb.*` |
| Slack feedback + emoji map + label registry | `scrapers.slack.feedback.*` |
| ATIF / shadow | **removed** — no env, no ConfigMap keys |

### 2.3 ConfigMap data keys

Today (`helm/chart/templates/configmap.yaml`): `label-registry.json`, `slack-emoji-label-map.json`, `shadow-allow-tenants.json`.

**Required:**

- **Remove** `shadow-allow-tenants.json` entirely (and all volume/env references).
- Keep **human feedback** label taxonomy as JSON mounted/used as **`HOSTED_AGENT_LABEL_REGISTRY_JSON`**; source values move under `scrapers.slack.feedback` (implementation may rename the ConfigMap key for clarity, but then **update every consumer** consistently).

### 2.4 Runtime: settings and HTTP surface

Refactor toward a smaller frozen dataclass (name may stay `ObservabilitySettings` per `design.md` non-goal, or rename if you update all imports in one change).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ObservabilitySettings:
    checkpoints_enabled: bool
    checkpoint_backend: str
    checkpoint_postgres_url: str | None
    wandb_enabled: bool
    wandb_project: str | None
    wandb_entity: str | None
    slack_feedback_enabled: bool
    slack_emoji_map: dict[str, str]
    operational_mapper_flags: dict[str, bool]
    # Explicitly omit: atif_export_*, shadow_*

    @classmethod
    def from_env(cls) -> "ObservabilitySettings": ...
```

```python
# helm/src/hosted_agents/app.py — remove or replace exports that reference ATIF/shadow
def build_app(...) -> ...: ...
```

```python
# Example: remove ATIF route entirely (signature illustrative)
# @app.get("/api/v1/runtime/exports/atif")  -> deleted
```

Any **public JSON** payloads that today expose `atif_export_enabled` / `shadow_enabled` **SHALL** be updated or removed so clients do not see dead flags.

### 2.5 Shared utilities

If `hosted_agents.observability.wandb_trace` (or others) imports symbols from `atif.py` that are still needed (e.g. hashing helpers), **extract** those into a neutral module (e.g. `observability/tags.py`) **before** deleting `atif.py`, or inline minimal logic — **no** ATIF export surface may remain.

## 3. Spec files (normative)

### 3.1 Delta specs (this change — implement against these)

| Path |
|------|
| `openspec/changes/dedupe-helm-values-observability/specs/dalc-chart-runtime-values/spec.md` |
| `openspec/changes/dedupe-helm-values-observability/specs/dalc-agent-o11y-scrape/spec.md` |

Key requirement IDs introduced or modified there include **`[DALC-REQ-CHART-RTV-001]`** … **`004`**, **`[DALC-REQ-O11Y-SCRAPE-004]`** … **`006`**.

### 3.2 Promoted specs you must reconcile when merging to `openspec/specs/`

| Path | Why |
|------|-----|
| `openspec/specs/dalc-agent-o11y-scrape/spec.md` | Today still says `o11y.prometheusAnnotations` / generic ServiceMonitor wording — must match **`observability.*`** and add **`[DALC-REQ-O11Y-SCRAPE-006]`** if merging structured logs requirement from delta. |
| `openspec/specs/dalc-helm-unittest/spec.md` | Scenario text references **`o11y.serviceMonitor.enabled`** — update to **`observability.serviceMonitor.enabled`** (or equivalent) so spec matches tests. |
| `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | Cross-capability references; update body text if it names old Helm keys (`docs/observability.md` snippets). |

### 3.3 Related promoted specs (verify no stale value paths in prose)

| Path |
|------|
| `openspec/specs/dalc-rag-from-scrapers/spec.md` |
| `openspec/specs/dalc-example-values-files/spec.md` |

## 4. Tests and assertions (must end green)

Use **TDD**: for each stage below, **add or modify tests first** so they fail on the pre-refactor tree, then implement until the named commands pass.

### 4.1 Helm unittest (chart + examples)

**Suites / files:**

| File | Role |
|------|------|
| `helm/tests/hello_world_test.yaml` | Regression: no CronJob, no RAG label (`[DALC-REQ-HELM-UNITTEST-001]`). |
| `helm/tests/with_scrapers_test.yaml` | CronJob + RAG presence (`[DALC-REQ-HELM-UNITTEST-001]`, `[DALC-REQ-HELM-UNITTEST-004]`). |
| `helm/tests/with_observability_test.yaml` | Prometheus annotations on agent Service/Deployment, RAG when deployed, `ServiceMonitor` positive and negative RAG cases (`[DALC-REQ-O11Y-SCRAPE-004]`, `[DALC-REQ-O11Y-SCRAPE-005]`, `[DALC-REQ-HELM-UNITTEST-001]`). **Update** any inlined `values:` overrides and traceability header comments if requirement text moves. |
| `helm/tests/checkpointing_test.yaml` | Asserts `HOSTED_AGENT_CHECKPOINTS_ENABLED` / `HOSTED_AGENT_CHECKPOINT_BACKEND` from **new** values path (replace prose `observability.checkpoints` with `checkpoints`). |

**Concrete assertions to preserve or strengthen:**

- `with_observability_test.yaml`: `prometheus.io/scrape: "true"` on agent Deployment template, agent Service, RAG Deployment/Service when RAG deployed; `ServiceMonitor` documents for agent and RAG; **zero** RAG `ServiceMonitor` documents when using the no-RAG fixture values file.
- `checkpointing_test.yaml`: env contains `HOSTED_AGENT_CHECKPOINTS_ENABLED: "true"` and backend `memory` when example values enable in-memory checkpoints.

**Invocation:** from repo root, follow `README.md` / CI: run `helm unittest` for each example chart with the documented `-f` path under `helm/tests/` (see `[DALC-REQ-HELM-UNITTEST-003]`).

**Example values to update:**

- `examples/with-observability/values.yaml` — replace `o11y:` with `observability:` (new meaning).
- `examples/with-observability/values-o11y-no-rag.yaml` — same rename; consider renaming file to `values-observability-no-rag.yaml` **only if** you update **all** references (unittest `values:` blocks, `docs/spec-test-traceability.md`, grep).
- `examples/checkpointing/values.yaml` — move `observability.checkpoints` → top-level `checkpoints` under the library subchart key.

### 4.2 Python (runtime under `helm/src/`)

Run from `helm/src` after `uv sync` (see root `README.md`):

```bash
uv run pytest tests/ -v --tb=short
```

**Tests likely requiring edits (non-exhaustive — grep to complete):**

| Test path | Expectation |
|-----------|-------------|
| `helm/src/tests/test_postgres_env.py` | Construct `ObservabilitySettings.from_env()` after env contract changes; update any assumptions on removed fields. |
| `helm/src/tests/test_checkpoint_feedback_api.py` | Remove or replace **`test_atif_export_requires_flag_and_run_id`** and any shadow-specific cases; adjust fixtures that built `ObservabilitySettings` with ATIF/shadow. |
| `helm/src/tests/test_o11y_metrics.py` | Unchanged behavior for `/metrics` and logs **unless** settings wiring breaks imports. |
| `helm/src/tests/integration/test_kind_o11y_prometheus.py` | Must stay green when `RUN_KIND_O11Y_INTEGRATION=1` — update `helm/src/tests/scripts/integration_kind_o11y_prometheus.sh` **`--set`** paths from `declarative-agent-library.o11y.*` to `declarative-agent-library.observability.*`. |

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

Update **`docs/spec-test-traceability.md`** rows for:

- `[DALC-REQ-O11Y-SCRAPE-004]`, `[DALC-REQ-O11Y-SCRAPE-005]` (and `006` if promoted),
- new **`[DALC-REQ-CHART-RTV-*]`** rows pointing to helm unittest and/or pytest evidence,
- `[DALC-REQ-HELM-UNITTEST-001]` scenario text paths if example filenames change.

Add/adjust **`# Traceability: [ID]`** comments in modified helm unittest YAML and pytest docstrings per **ADR 0003**.

## 5. Staged execution (TDD; each stage names tests that pass)

### Stage 1 — Helm: failing contract tests, then green `helm unittest`

**Write/update first:** `helm/tests/checkpointing_test.yaml` (new values path), `helm/tests/with_observability_test.yaml` and example values so they reference **`observability.*`** / **`checkpoints.*`** / **`scrapers.slack.feedback.*`** — **expect red**.

**Then implement:** `helm/chart/values.yaml`, `helm/chart/values.schema.json`, all templates under `helm/chart/templates/`, and `examples/**` until:

- `helm unittest` passes for **`helm/tests/hello_world_test.yaml`**, **`with_scrapers_test.yaml`**, **`with_observability_test.yaml`**, **`checkpointing_test.yaml`** (and any `helm/tests/chart/*` suite if present).

### Stage 2 — Integration script / optional job

**Write/update first:** adjust `integration_kind_o11y_prometheus.sh` expectations if needed (dry-run).

**Then implement:** until **`helm/src/tests/integration/test_kind_o11y_prometheus.py::test_kind_o11y_prometheus_integration`** passes with `RUN_KIND_O11Y_INTEGRATION=1` on a machine with kind/helm prerequisites (if you cannot run locally, leave evidence in PR description — but **default branch** should keep script consistent with values).

### Stage 3 — Runtime ATIF/shadow removal

**Write/update first:** delete or xfailing pytest that asserted ATIF HTTP export and shadow behavior; add tests proving **`503`/missing route** for removed export if any public behavior remains intentionally.

**Then implement:** remove modules/routes (`app.py`, `observability/__init__.py`, `atif.py`, `shadow.py`, trigger graph branches), slim `ObservabilitySettings`, fix `wandb_trace` imports, until:

- `uv run pytest tests/ -v --tb=short` passes from `helm/src`.

### Stage 4 — Docs + OpenSpec promotion

**Implement:** `docs/runbook-checkpointing-wandb.md`, `docs/observability.md`, chart `README.md`, `grafana/README.md` only where Helm key names appear.

**Promote:** merge delta specs from `openspec/changes/dedupe-helm-values-observability/specs/` into `openspec/specs/` (or complete archive workflow per project OpenSpec), fix **`cfha-agent-o11y-logs-dashboards`** typo in delta body to **`dalc-agent-o11y-logs-dashboards`**.

**Verify:** `python3 scripts/check_spec_traceability.py` exits **0**.

## 6. Acceptance checklist

- [ ] No `o11y` key in published `helm/chart/values.yaml` or `values.schema.json`.
- [ ] No `observability.checkpoints`, `observability.wandb`, `observability.slackFeedback`, `observability.labelRegistry`, `observability.atifExport`, `observability.shadow` in values or schema.
- [ ] `observability` contains only cluster/Prometheus/log-toggle concerns per delta spec.
- [ ] `HOSTED_AGENT_POSTGRES_URL` sourced from `checkpoints.postgresUrl` when non-empty.
- [ ] Slack feedback + label registry only under `scrapers.slack.feedback`.
- [ ] ConfigMap excludes shadow JSON; docs describe feedback label registry purpose (`HOSTED_AGENT_LABEL_REGISTRY_JSON`).
- [ ] All tests in §4 green; traceability script green.

## 7. Commands summary

```bash
# Helm
helm unittest -f ../../helm/tests/<suite>.yaml .   # from each example chart dir; see README

# Python
cd helm/src && uv run pytest tests/ -v --tb=short

# Traceability
python3 scripts/check_spec_traceability.py
```

`````
