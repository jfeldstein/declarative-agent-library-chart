# Step 2: consolidate-naming

`````
# Downstream LLM implementation brief: `consolidate-naming`

## 0. Context (read first)

- **Linear checklist:** Tier **2** in `docs/openspec-implementation-order.md` — **after** `dedupe-helm-values-observability` (tier 1) so Helm **value semantics** and keys (`observability`, `checkpoints`, `wandb`, `scrapers.slack.feedback`) are stable before a **BREAKING** rename of chart `name`, template **helpers**, parent **values key** (`agent` alias), **image.repository**, and **Grafana** filenames / product tags.
- **Must align with step 1:** Read `docs/implementation-specs/01-dedupe-helm-values-observability-spec.md`. Do **not** reintroduce `o11y` or nest checkpoints/wandb/feedback under `observability`. In examples, library tunables live under the **parent** key chosen here (`agent:`); full paths are e.g. **`agent.observability.*`**, **`agent.checkpoints.*`**, **`agent.image.*`** — not `declarative-agent-library.o11y.*` or deprecated overloads.
- **Authoritative change bundle:** `openspec/changes/consolidate-naming/` — `proposal.md`, `design.md`, `tasks.md`, delta specs under `specs/*/spec.md`.
- **Non-goals (explicit):** Do not rename **`[DALC-REQ-…]`** IDs or `openspec/specs/dalc-*` folder names; do not change Prometheus **metric base names** or HTTP routes except for **operator-visible** strings (titles, `service` log field, chart metadata).

## 1. Goal

**BREAKING** alignment to **DALC** / **declarative-agent-library-chart** naming:

1. Helm library chart **`Chart.yaml` `name`** → **`declarative-agent-library-chart`** (from `declarative-agent-library`).
2. **Helm helpers** and all `include "declarative-agent-library.*"` → **`declarative-agent-library-chart.*`** (match chart `name` convention).
3. Example application charts: dependency **`name: declarative-agent-library-chart`**, **`alias: agent`**, parent **`values.yaml`** nests under **`agent:`** (remove **`declarative-agent-library:`** root key).
4. Default **`image.repository`** segment → **`declarative-agent-library-chart`** (replace **`config-first-hosted-agents`**).
5. **`git mv`** `grafana/dalc-agent-overview.json` → **`grafana/dalc-overview.json`**; dashboard **`uid` / tags / titles**: product-facing **cfha** → **dalc** (do not alter **requirement ID** strings like `[DALC-REQ-…]`).
6. Runtime **`SERVICE_NAME`** (and equivalent OpenAPI / user-facing product labels) → **`declarative-agent-library-chart`** where they denoted the old product string.
7. Scripts/docs/README/**`docs/spec-test-traceability.md`** / integration values: update paths and **human-facing** job/cluster/release fragments (**cfha-** → **dalc-** where design applies).

After merge: promote deltas per OpenSpec workflow; **`python3 scripts/check_spec_traceability.py`** exits **0**.

## 2. Entities and interfaces

### 2.1 Helm chart package identity

```yaml
# helm/chart/Chart.yaml — fields (no bodies)
apiVersion: v2
name: str          # SHALL be declarative-agent-library-chart
description: str
type: str
version: str
appVersion: str
```

### 2.2 Parent ↔ subchart values merge (examples only)

```yaml
# examples/<example>/Chart.yaml — dependency entry (illustrative)
dependencies:
  - name: declarative-agent-library-chart
    version: str
    repository: str
    alias: agent
```

```yaml
# examples/<example>/values.yaml — pseudotype ExampleParentValues
agent:
  image: { repository: str, tag: str, pullPolicy: str }
  observability: { ... }      # post–step-1 scrape + structuredLogs + serviceMonitor
  checkpoints: { ... }        # post–step-1
  wandb: { ... }              # post–step-1
  scrapers: { ... }           # post–step-1; includes slack.feedback when used
  # ... other flat library keys unchanged in meaning
```

**Forbidden** in example parent values after this change: top-level key **`declarative-agent-library:`** for the library subchart (use **`agent:`** only).

### 2.3 Template helper contract (`helm/chart`)

```go-template
{{- define "declarative-agent-library-chart.name" -}}
{{- end -}}
{{- define "declarative-agent-library-chart.fullname" -}}
{{- end -}}
{{- define "declarative-agent-library-chart.chart" -}}
{{- end -}}
{{- define "declarative-agent-library-chart.labels" -}}
{{- end -}}
# ... all defines/includes that today use declarative-agent-library.* SHALL migrate
```

Library **`values.yaml`** remains **flat** at subchart root (no nested `agent` inside the library’s own defaults).

### 2.4 Helm unittest template paths (example charts)

Example charts vendor the dependency under `charts/<chart-name>-<version>.tgz` unpacked as **`charts/<dependency-chart-name>/`**. After rename, suite `template:` paths **SHALL** use:

```text
charts/declarative-agent-library-chart/templates/<file>.yaml
```

(not `charts/declarative-agent-library/...`).

### 2.5 Grafana artifact

```json
// grafana/dalc-overview.json — conceptual interface
{
  "uid": "string",
  "tags": ["string"],
  "title": "string",
  "panels": [ ... ]
}
```

**SHALL** exist at repo path **`grafana/dalc-overview.json`**. **`dalc-agent-overview.json`** SHALL NOT remain the documented import path.

### 2.6 Runtime logging / OpenAPI

```python
# helm/src/hosted_agents/o11y_logging.py
SERVICE_NAME: str  # SHALL equal declarative-agent-library-chart where used as product id for JSON log field `service`
```

```python
# FastAPI / OpenAPI — illustrative signatures only
def create_app(...) -> FastAPI: ...
# Titles/descriptions that intentionally branded CFHA for product SHALL move to DALC or full product name per proposal
```

## 3. Normative specs

### 3.1 Delta specs (implement / promote from this change)

| Path | Notes |
|------|--------|
| `openspec/changes/consolidate-naming/specs/dalc-library-chart-packaging/spec.md` | **ADDED** `[DALC-REQ-DALC-PKG-001]` … **`003`** (chart name, `agent` alias, image repo). |
| `openspec/changes/consolidate-naming/specs/dalc-agent-o11y-logs-dashboards/spec.md` | **MODIFIED** `[DALC-REQ-O11Y-LOGS-001]` (example `service` id), **`[DALC-REQ-O11Y-LOGS-003]`** (dashboard path **`grafana/dalc-overview.json`**). When promoting, capability folder stays **`dalc-agent-o11y-logs-dashboards`**; fix any stale reference to **`cfha-agent-o11y-scrape`** in prose to **`dalc-agent-o11y-scrape`**. |

### 3.2 Promoted specs to update on merge (naming + consistency with step 1)

| Path | Action |
|------|--------|
| `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | Apply MODIFIED blocks; ensure **`[DALC-REQ-O11Y-LOGS-001]`** example identifier and **`[DALC-REQ-O11Y-LOGS-003]`** dashboard path match implementation. |
| `openspec/specs/dalc-library-chart-packaging/spec.md` | **ADD** when capability is promoted (new file tree mirroring delta). |
| `openspec/specs/dalc-helm-unittest/spec.md` | If scenarios still mention **`o11y.serviceMonitor`**, they **must** read **`observability.serviceMonitor`** after step 1 — keep that; update any prose that names the old **values root key** or **charts/** path if needed. |
| `openspec/specs/dalc-agent-o11y-scrape/spec.md` | Step 1 owns **`o11y` → `observability`** for scrape flags; verify no contradiction when examples use **`agent.observability.*`**. |

### 3.3 Traceability matrix

Update **`docs/spec-test-traceability.md`**:

- **`[DALC-REQ-O11Y-LOGS-003]`** evidence: **`grafana/dalc-overview.json`** (replace `dalc-agent-overview.json`).
- Add rows for **`[DALC-REQ-DALC-PKG-001]`** … **`003`** with evidence (e.g. `helm/chart/Chart.yaml`, `examples/*/values.yaml`, `helm/chart/values.yaml`, unittest comments).

## 4. Tests and assertions (TDD; all must end green)

**Rule:** For each stage, **edit/add tests first** (red), then implementation (green). Test-writing is not a separate “stage”; each stage lists the tests that must pass before the stage is complete.

### 4.1 Helm unittest

**Suites:** `helm/tests/hello_world_test.yaml`, `with_scrapers_test.yaml`, `with_observability_test.yaml`, `checkpointing_test.yaml`.

| Assertion family | Expectation |
|------------------|-------------|
| **Template paths** | Every `template:` path under **`charts/declarative-agent-library-chart/templates/`** resolves after dependency update. |
| **Release names** | Where tests assert labels/metadata tied to `release.Name`, update only if implementation changes default release names or documented CI fixtures (**cfha-ci** → **dalc-ci** or equivalent per `design.md`). |
| **Behavioral SHALLs** | Preserve `[DALC-REQ-HELM-UNITTEST-001]` / **`004`** semantics: CronJob/RAG presence per example, scrape annotations + `ServiceMonitor` counts, checkpoint env wiring — but values loaded from examples **must** use **`agent:`** and **post–step-1** keys (`agent.observability`, not `o11y`). |
| **Traceability** | Keep/update `# Traceability: [ID]` headers per ADR 0003. |

**Invocation:** From each example chart directory, `helm unittest -f ../../helm/tests/<suite>.yaml .` (per `[DALC-REQ-HELM-UNITTEST-003]` / README).

### 4.2 Python (runtime `helm/src`)

```bash
cd helm/src && uv run pytest tests/ -v --tb=short
```

| Test / area | Expectation |
|-------------|-------------|
| `helm/src/tests/test_o11y_metrics.py` (e.g. `test_json_log_format_emits_message_key`) | JSON logs include **`service`** matching **`declarative-agent-library-chart`** when asserting static id (**`[DALC-REQ-O11Y-LOGS-001]`**). |
| `test_x_request_id_echo_and_generation` | Still satisfies **`[DALC-REQ-O11Y-LOGS-002]`** (no behavior change beyond correlation). |
| Integration | `RUN_KIND_O11Y_INTEGRATION=1`: `integration/test_kind_o11y_prometheus.py` green after **`integration_kind_o11y_prometheus.sh`** / **`prometheus-kind-o11y-values.yaml`** use **dalc-** job/cluster strings and **new image repo:tag** documented in README. |

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

### 4.4 Optional CI parity

`ct lint` / chart-testing if CI requires it; `helm lint` on touched charts.

## 5. Staged execution (each stage: tests listed pass at stage end)

### Stage A — Chart rename + helpers + library defaults

**Tests first:** Update **failing** unittest `template:` paths to `charts/declarative-agent-library-chart/...` and fix any hard-coded helper strings in asserts if present; run unittest → **red**.

**Implement:** `helm/chart/Chart.yaml`, `_helpers.tpl`, all templates’ `include`/`define`, `helm/chart/values.yaml` default `image.repository`, `values.schema.json` titles/strings.

**Green when:** `helm unittest` passes for suites pointing at examples **after** Stage B values migration **or** temporarily inline minimal `agent:` fixtures that already validate helper rename (prefer migrating examples early if faster).

### Stage B — Examples: alias `agent`, values move, Chart.lock

**Tests first:** Adjust suites’ `values:` to `../../examples/.../values.yaml` expecting **`agent:`** — red until files migrated.

**Implement:** Each `examples/*/Chart.yaml` (dependency name + alias), `helm dependency update`, each `values*.yaml` under **`agent:`**, optional `examples/AGENTS.md` / README snippets.

**Green when:** All four `helm/tests/*.yaml` suites green against updated examples.

### Stage C — Grafana + docs + traceability paths

**Tests first:** None new if only assets/docs — but update any test or script that **glob**’s dashboard path; matrix row change can make **`check_spec_traceability`** fail first → use that as red gate.

**Implement:** `git mv` dashboard JSON, edit `uid`/tags/titles, `grafana/README.md`, `docs/observability.md`, root `README.md` (docker tag, import path, values snippets with **`agent:`** and **`declarative-agent-library-chart:local`** or documented tag).

**Green when:** `python3 scripts/check_spec_traceability.py` green; manual grep shows **`dalc-agent-overview.json`** removed from active docs/matrix.

### Stage D — Runtime + scripts + OpenAPI strings

**Tests first:** Update pytest expected **`service`** field to new constant — red.

**Implement:** `o11y_logging.py`, OpenAPI titles, `helm/src/tests/scripts/*`, shell integration scripts, `skaffold.yaml` / `devspace.yaml` if in scope (product image names).

**Green when:** `uv run pytest tests/ -v --tb=short` green; optional kind integration green where machine supports it.

### Stage E — OpenSpec promotion + final sweep

**Implement:** Archive/promote per project OpenSpec skill; merge **`dalc-library-chart-packaging`** into `openspec/specs/`; merge MODIFIED **`dalc-agent-o11y-logs-dashboards`**; ensure promoted **`dalc-helm-unittest`** scenario uses **`observability.serviceMonitor.enabled`** (step 1), not `o11y`.

**Green when:** `python3 scripts/check_spec_traceability.py` green; `rg` for **`config-first-hosted-agents`**, **`declarative-agent-library:`** (parent values root), **`charts/declarative-agent-library/templates`**, **`dalc-agent-overview.json`**, stale helper prefix — **zero** in active code paths or documented with explicit maintainer exception (patches/history only).

## 6. Acceptance checklist

- [ ] `helm show chart helm/chart` → **name** `declarative-agent-library-chart`.
- [ ] No `define "declarative-agent-library.` / no `include "declarative-agent-library.` in `helm/chart`.
- [ ] All examples use **`agent:`** + **`alias: agent`**; no `declarative-agent-library:` values root for the library.
- [ ] Default image repository segment is **`declarative-agent-library-chart`**.
- [ ] `grafana/dalc-overview.json` exists; `grafana/dalc-agent-overview.json` does not.
- [ ] JSON logs / tests use **`service: declarative-agent-library-chart`** (or documented equivalent).
- [ ] Example + unittest Helm paths use **post–step-1** value keys under **`agent.`** (`observability`, `checkpoints`, …).
- [ ] `python3 scripts/check_spec_traceability.py` passes; CI-equivalent helm tests pass.

## 7. Commands summary

```bash
# Examples: refresh vendor tree
helm dependency update examples/hello-world
# repeat per example

# Helm unittest (from example chart dir)
helm unittest -f ../../helm/tests/hello_world_test.yaml .

# Python
cd helm/src && uv run pytest tests/ -v --tb=short

# Traceability
python3 scripts/check_spec_traceability.py
```
`````
