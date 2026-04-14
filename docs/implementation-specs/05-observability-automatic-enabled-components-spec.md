# Step 5: observability-automatic-enabled-components

`````
# Downstream LLM implementation brief: `observability-automatic-enabled-components`

## 0. Context (read first)

- **Linear checklist:** Tier **4** (step **5**) in `docs/openspec-implementation-order.md` — **after** `consolidate-naming` and **`consolidate-helm-tests`**, alongside `examples-distinct-values-readmes`; targets **component-neutral** scrape / `ServiceMonitor` / Grafana behavior and tests under post-move **`helm/tests/`**.
- **Upstream alignment (mandatory):**
  - Step **1** ([`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md)): library scrape + log toggles live under **`observability`** (not `o11y`); no checkpoints/wandb under that key.
  - Step **2** ([`02-consolidate-naming-spec.md`](02-consolidate-naming-spec.md)): example parent values under **`agent:`**; vendored path **`charts/declarative-agent-library-chart/templates/...`**; starter dashboard path **`grafana/dalc-overview.json`** (not `dalc-agent-overview.json`).
  - Step **3** ([`03-consolidate-helm-tests-spec.md`](03-consolidate-helm-tests-spec.md)): suites live in **`helm/tests/<example_underscore>_test.yaml`** with **`values:`** → **`../../examples/<dir>/values.yaml`**; CI **`helm unittest -f …`** from each **`examples/<chart>/`**.
  - Step **4** ([`04-examples-distinct-values-readmes-spec.md`](04-examples-distinct-values-readmes-spec.md)): every README-listed **`values*.yaml`** for multi-setup examples is loaded in unittest with matching assertions (**[DALC-REQ-HELM-UNITTEST-004]**).
- **Authoritative change bundle:** `openspec/changes/observability-automatic-enabled-components/` — `proposal.md`, `design.md`, `tasks.md`, delta specs under `specs/*/spec.md`. Treat **`cfha-*`** / **`examples/.../tests/`** mentions in those files as **stale**; implement against **`dalc-*`** capability folders and **`helm/tests/`** paths.
- **Non-goals (from `design.md`):** No `ServiceMonitor` for **CronJob** scraper pods (no `Service` today); no replacing Prometheus Operator with in-chart static scrape configs.

## 1. Goal

1. **Specs:** Generalize scrape + `ServiceMonitor` requirements so they apply to **every chart-managed workload** that exposes **`/metrics` via a `Service`**, when that workload is **enabled and deployed** — with explicit **negative** scenarios when an optional metrics **`Service`** is absent. Align prose and value paths with **post–step 1** **`observability.*`** (and **`agent.observability.*`** in examples), not legacy **`o11y`** strings in delta snippets.
2. **Helm unittest (`with-observability` example):** Refactor **`helm/tests/with_observability_test.yaml`** to **component-neutral** `it:` titles; prove **one `ServiceMonitor` document per deployed metrics `Service`** when multiple components are on; prove **zero** documents from the optional workload’s **`ServiceMonitor` template** when that workload is off while the **agent** monitor still renders when **`agent.observability.serviceMonitor.enabled`** (or equivalent) is true.
3. **Grafana:** Update **`grafana/README.md`** and **`grafana/dalc-overview.json`** so Prometheus scrape guidance is **generic** (enabled components / endpoints), optional component panels are **optional in UX** per **[DALC-REQ-O11Y-LOGS-003]**, and **[DALC-REQ-O11Y-LOGS-005]** is evidenced (no fixed “scrape both targets” / RAG-mandatory wording).
4. **Traceability:** Any new or materially changed **`### Requirement:`** **SHALL** lines keep stable **`[DALC-REQ-…]`** IDs; update **`docs/spec-test-traceability.md`** and **`#` / docstring** citations per **ADR 0003** / **DALC-VER-005**; **`python3 scripts/check_spec_traceability.py`** exits **0**.

## 2. Entities and interfaces

### 2.1 Helm values (example parent → library)

```yaml
# Pseudotype: fragment under agent: in examples/with-observability/values*.yaml
agent:
  observability:
    prometheusAnnotations: { enabled: bool }
    structuredLogs: { json: bool }
    serviceMonitor:
      enabled: bool
      interval: str
      scrapeTimeout: str
      extraLabels: { [str]: str }
  scrapers: { ... }   # gates optional RAG / metrics Service when jobs enabled
```

**Contract:** A **single** operator switch family (**`observability.prometheusAnnotations`**, **`observability.serviceMonitor`**) drives annotations and `ServiceMonitor` resources **per deployed metrics `Service`** — no separate per-workload Prometheus flag solely for one optional workload (**[DALC-REQ-O11Y-SCRAPE-004]** prose).

### 2.2 Template ↔ rendered resources (library chart)

```text
helm/chart/templates/servicemonitor.yaml          # agent ServiceMonitor (illustrative name)
helm/chart/templates/rag-servicemonitor.yaml      # optional RAG HTTP Service (when deployed)
# … future metrics Services follow same pattern
```

```yaml
# Conceptual: helm-unittest document assertions
# - template: charts/declarative-agent-library-chart/templates/servicemonitor.yaml
#   documentIndex / count when agent SM expected
# - template: charts/declarative-agent-library-chart/templates/rag-servicemonitor.yaml
#   count: 0 when RAG / optional metrics Service not deployed
```

### 2.3 Grafana starter dashboard

```json
// grafana/dalc-overview.json — conceptual only
{
  "uid": "string",
  "tags": ["string"],
  "title": "string",
  "templating": { "list": [ /* optional: variables for component / job */ ] },
  "rows": [ /* optional sections for agent vs optional metrics */ ]
}
```

**Contract:** Default import remains usable **agent-only**; sections for optional metrics **`Service`** targets are **optional or clearly dependency-labeled** per **`grafana/README.md`** (**[DALC-REQ-O11Y-LOGS-003]**).

## 3. Normative specs

### 3.1 Delta specs (merge / reconcile when applying this change)

| Path |
|------|
| `openspec/changes/observability-automatic-enabled-components/specs/dalc-agent-o11y-scrape/spec.md` |
| `openspec/changes/observability-automatic-enabled-components/specs/dalc-agent-o11y-logs-dashboards/spec.md` |
| `openspec/changes/observability-automatic-enabled-components/specs/dalc-helm-unittest/spec.md` |

**Note:** Delta bodies may still say **`o11y.*`**; when promoting or editing **`openspec/specs/`**, normalize scenario text to **`observability.*`** / **`agent.observability.*`** to match the merged **dedupe** + **naming** tree.

### 3.2 Promoted specs (full files to verify / update)

| Path | Requirement IDs (focus) |
|------|-------------------------|
| `openspec/specs/dalc-agent-o11y-scrape/spec.md` | **[DALC-REQ-O11Y-SCRAPE-004]**, **[DALC-REQ-O11Y-SCRAPE-005]** — per-component presence/absence of annotations and `ServiceMonitor` documents |
| `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` | **[DALC-REQ-O11Y-LOGS-003]**, **[DALC-REQ-O11Y-LOGS-005]** |
| `openspec/specs/dalc-helm-unittest/spec.md` | **[DALC-REQ-HELM-UNITTEST-001]** (with-observability scenarios), preserve **[004]** compatibility for documented **`values*.yaml`** |

## 4. Tests and assertions (TDD; all must end green)

**Rule:** For each stage, **extend or adjust `helm/tests/with_observability_test.yaml` (and values fixtures) first** so CI is **red**, then implement templates/docs/dashboard until green. Test-writing is not a separate “stage” from implementation.

### 4.1 Helm unittest — `helm/tests/with_observability_test.yaml`

| Scenario | Values fixture | Assertions |
|----------|----------------|------------|
| Multiple metrics **`Services`** deployed | Default (or explicit) **`examples/with-observability/values.yaml`** where agent + optional RAG **`Service`** deploy | **`prometheus.io/scrape`** expectations unchanged or strengthened vs prior threshold; **≥2** valid `ServiceMonitor` **documents** when **two** metrics services exist (**[DALC-REQ-HELM-UNITTEST-001]**, **[DALC-REQ-O11Y-SCRAPE-005]**); `it:` names **component-neutral** (not “RAG-only” centric) |
| Optional metrics **`Service`** absent, `ServiceMonitor` enabled | Same pattern as step 4 **`values-o11y-no-rag.yaml`** (or successor filename) — scrapers off / no RAG | **`rag-servicemonitor.yaml`** template: **zero** `ServiceMonitor` documents; **`servicemonitor.yaml`** (agent): **one** document when enabled (**[DALC-REQ-HELM-UNITTEST-001]** negative scenario, **[DALC-REQ-O11Y-SCRAPE-005]** third scenario) |
| Annotations absent for absent workload | Matching “no optional service” values | No scrape annotations on non-existent optional **`Service`**/Pods (**[DALC-REQ-O11Y-SCRAPE-004]** third scenario) |

**Invocation (repo root pattern):**

```bash
cd examples/with-observability && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/with_observability_test.yaml" .
```

Repeat full example loop from **`03`** / CI if any shared assertion changes.

### 4.2 Python / integration

- **Default:** No runtime code change required; if **`helm/src/tests/scripts/prometheus-kind-o11y-values.yaml`** or integration shell still implies “always two targets,” align wording / **`--set`** paths with **`agent.observability.*`** and generic multi-target language.

```bash
cd helm/src && uv run pytest tests/ -v --tb=short   # if any pytest or script touched
```

### 4.3 Spec traceability gate

```bash
python3 scripts/check_spec_traceability.py
```

## 5. Staged execution (each stage ends with listed tests green)

### Stage A — Specs + matrix (red via traceability or spec edits first)

**Tests first:** None new until Stage B — optionally update matrix rows first to fail **`check_spec_traceability.py`** if new IDs land.

**Implement:** Merge delta **`specs/**`** into **`openspec/specs/dalc-agent-o11y-scrape/spec.md`**, **`dalc-agent-o11y-logs-dashboards/spec.md`**, **`dalc-helm-unittest/spec.md`**; fix **`o11y` → `observability`** in promoted text where deltas lag; update **`docs/spec-test-traceability.md`**.

**Green when:** **`python3 scripts/check_spec_traceability.py`** exits **0**.

### Stage B — Helm unittest + example values

**Tests first:** Edit **`helm/tests/with_observability_test.yaml`** (and **`examples/with-observability/**`** values if needed) for multi-`ServiceMonitor` + zero-doc optional template case — **red** until templates match.

**Implement:** Adjust **`helm/chart/templates/*servicemonitor*.yaml`** / related only if behavior gaps vs specs; keep **one SM per metrics `Service` when deployed**.

**Green when:** **`helm unittest -f "../../helm/tests/with_observability_test.yaml"`** from **`examples/with-observability/`** passes; full per-example unittest loop passes if required by CI.

### Stage C — Grafana README + `dalc-overview.json`

**Tests first:** None automated for JSON — manual smoke per **`design.md`**.

**Implement:** **`grafana/README.md`** generic scrape targets (**[DALC-REQ-O11Y-LOGS-005]**); **`grafana/dalc-overview.json`** optional UX for optional metrics sections (**[DALC-REQ-O11Y-LOGS-003]**).

**Green when:** Import steps in README still valid; **`check_spec_traceability.py`** still **0** if matrix cites dashboard path.

### Stage D — Docs + changelog

**Implement:** Short **`docs/development-log.md`** entry if this repo logs there; fix any **`docs/observability.md`** / root **README** snippets that still say “scrape both” or RAG-only **ServiceMonitor** story.

**Green when:** Grep shows no user-facing “both targets” mandate; CI parity commands from prior stages still pass.

## 6. Acceptance checklist

- [ ] Promoted **`openspec/specs/dalc-agent-o11y-scrape/spec.md`**, **`dalc-agent-o11y-logs-dashboards/spec.md`**, **`dalc-helm-unittest/spec.md`** match merged deltas and **post–steps 1–2** value path vocabulary.
- [ ] **`helm/tests/with_observability_test.yaml`** uses **component-neutral** test names; covers **multi-`ServiceMonitor`** and **zero optional-template `ServiceMonitor`** with **`agent.observability.serviceMonitor.enabled`** true.
- [ ] **`grafana/README.md`** describes scraping **all enabled** chart metrics endpoints without implying a fixed optional component count (**[DALC-REQ-O11Y-LOGS-005]**).
- [ ] **`grafana/dalc-overview.json`** agent-only default is usable; optional metrics sections are optional per README (**[DALC-REQ-O11Y-LOGS-003]**).
- [ ] **`docs/spec-test-traceability.md`** and test **`#`** comments cite correct IDs/paths; **`python3 scripts/check_spec_traceability.py`** passes.
- [ ] No reintroduction of per-workload-only Prometheus values flags forbidden by **[DALC-REQ-O11Y-SCRAPE-004]**.

## 7. Commands summary

```bash
cd examples/with-observability && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/with_observability_test.yaml" .

for d in examples/*/; do ( cd "$d" && helm dependency build --skip-refresh && chart=$(basename "$d" | tr -d '/') && helm unittest -f "../../helm/tests/${chart//-/_}_test.yaml" . ); done

python3 scripts/check_spec_traceability.py

cd helm/src && uv run pytest tests/ -v --tb=short   # if Python touched
```

`````
