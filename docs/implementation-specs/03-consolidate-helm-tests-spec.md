# Step 3: consolidate-helm-tests

`````
# Downstream LLM implementation brief: `consolidate-helm-tests`

## 0. Context (read first)

- **Linear checklist:** Tier **3** in `docs/openspec-implementation-order.md` — centralize helm-unittest suites under **`helm/tests/`**; CI uses **`helm unittest -f …`** per example; **test-to-spec traceability** matrix evidence paths update. **`examples-distinct-values-readmes`** (step 4) and **`observability-automatic-enabled-components`** (step 5) assume this layout.
- **Upstream alignment:** After **`dedupe-helm-values-observability`** ([`docs/implementation-specs/01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md)) and **`consolidate-naming`** ([`docs/implementation-specs/02-consolidate-naming-spec.md`](02-consolidate-naming-spec.md)): example **`values.yaml`** use the post-dedupe keys (`agent.observability.*`, `agent.checkpoints.*`, …) and **`template:`** paths in suites reference the vendored subchart folder name from step 2 (**`charts/declarative-agent-library-chart/templates/...`**), not legacy `declarative-agent-library` or `o11y` keys.
- **Authoritative change bundle:** `openspec/changes/consolidate-helm-tests/` — `proposal.md`, `design.md`, `tasks.md`, delta specs under `specs/*/spec.md`.
- **Non-goals:** Do not move or merge **`helm/chart/templates/tests/`** (install-time `helm test` hooks). Do not add new examples or new assertion scenarios beyond relocation, **`values:`** wiring, CI/docs/spec/traceability updates.

## 1. Goal

1. **One suite file per covered example** at **`helm/tests/<example_basename>_test.yaml`**, where **`hello-world` → `hello_world_test.yaml`** (hyphens → underscores in the filename only).
2. **Remove** per-example **`examples/*/tests/`** trees after relocation.
3. Each suite **SHALL** declare **`values:`** loading that example’s committed **`values.yaml`** via a path **relative to the suite file** under **`helm/tests/`** (canonical form: **`../../examples/<example-dir>/values.yaml`** — resolves to repo root then `examples/`).
4. **CI and README** SHALL run **`helm unittest -f "../../helm/tests/${chart//-/_}_test.yaml" .`** from **`examples/<chart>/`** after **`helm dependency build --skip-refresh`** (same pattern for local parity).
5. **Traceability:** **`docs/spec-test-traceability.md`** and contributor rules cite **`helm/tests/*.yaml`** (not **`examples/*/tests/`**). Merge delta specs into **`openspec/specs/`** per project OpenSpec apply/archive conventions.

## 2. Entities and interfaces (signatures only; no bodies)

### 2.1 Filesystem layout

```text
helm/tests/
  AGENTS.md                    # maintainer contract (add/update)
  <example_underscore>_test.yaml
examples/<kebab-example>/
  Chart.yaml
  values.yaml
  Chart.lock
  # no tests/ subtree for helm-unittest after change
```

### 2.2 Suite document shape (helm-unittest)

```yaml
# File: helm/tests/<name>_test.yaml
# comments: # Traceability: [DALC-REQ-…] … per [DALC-VER-002]

values:
  - ../../examples/<example-dir>/values.yaml

suite: str
release:
  name: str
tests:
  - it: str
    template: charts/<dependency-chart-unpacked-name>/templates/<file>.yaml
    asserts: [ ... ]  # preserve existing assertions when moving
```

### 2.3 CI loop interface (conceptual)

```bash
# Pseudocode — parameters only
for chart_dir in examples/*/; do
  chart=$(basename "$chart_dir")
  suite="${chart//-/_}_test.yaml"
  ( cd "examples/$chart" && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/$suite" . )
done
```

### 2.4 Documentation surfaces

```markdown
# examples/AGENTS.md — SHALL exist; supersedes examples/AGENT.md
# sections: pointer to helm/tests/, adding examples + CI registration

# examples/README.md — link AGENTS.md; “adding an example” includes unittest file
```

### 2.5 Traceability script contract

```python
# scripts/check_spec_traceability.py — no code change required if matrix paths are correct;
# SHALL exit 0 when matrix evidence paths exist and IDs match promoted specs.
def main() -> None: ...
```

## 3. Normative specs

### 3.1 Delta specs (this change — merge into promoted)

| Path |
|------|
| `openspec/changes/consolidate-helm-tests/specs/dalc-requirement-verification/spec.md` |
| `openspec/changes/consolidate-helm-tests/specs/dalc-helm-unittest/spec.md` |

*(Note: `tasks.md` may mention `cfha-helm-unittest`; the repo folder is **`dalc-helm-unittest`**.)*

### 3.2 Promoted specs (full files to reconcile after apply)

| Path | Relevance |
|------|-----------|
| `openspec/specs/dalc-requirement-verification/spec.md` | **[DALC-VER-001]** … **[DALC-VER-005]** — step 3 materially updates prose for **[DALC-VER-002]** (Helm evidence under **`helm/tests/`**). |
| `openspec/specs/dalc-helm-unittest/spec.md` | **[DALC-REQ-HELM-UNITTEST-001]** … **[004]** — invocation scenario **[DALC-REQ-HELM-UNITTEST-003]** SHALL describe **`-f`** + **`values:`** relative paths. |

## 4. Spec scenarios and tests to satisfy (enumeration)

### 4.1 `[DALC-VER-002]` (promoted + delta)

| Scenario | Assertion for implementer |
|----------|---------------------------|
| Pytest evidence references IDs | Unchanged by this change unless matrix points at edited pytest files. |
| Helm unittest evidence references IDs | Every relocated **`helm/tests/*_test.yaml`** keeps or adds **`#`** comments (suite, **`it:`**, or top-of-file **`# Traceability:`**) containing each requirement ID string the matrix assigns to that file. |

### 4.2 `[DALC-REQ-HELM-UNITTEST-001]` scenarios (via suites)

| Scenario | Evidence file (after move) | What must stay true |
|----------|-------------------------|---------------------|
| hello-world: no CronJob | `helm/tests/hello_world_test.yaml` | No CronJob documents for default paths. |
| hello-world: no RAG label | same | Zero **`app.kubernetes.io/component: rag`**. |
| with-scrapers: CronJob | `helm/tests/with_scrapers_test.yaml` | ≥1 CronJob. |
| with-scrapers: RAG | same | ≥1 RAG component label. |
| with-observability: scrape + ServiceMonitors | `helm/tests/with_observability_test.yaml` | Multiple **`prometheus.io/scrape`**, one ServiceMonitor per deployed metrics Service, correct negative case when RAG disabled (per spec wording — align keys with post–step 1 **`observability.serviceMonitor`** / equivalent). |

### 4.3 `[DALC-REQ-HELM-UNITTEST-002]`

| Scenario | Check |
|----------|-------|
| No loss of coverage vs legacy grep | All assertions that existed in **`examples/*/tests/`** remain in the centralized suite; **`ct lint`** behavior unchanged. |

### 4.4 `[DALC-REQ-HELM-UNITTEST-003]`

| Scenario | Check |
|----------|-------|
| Reproducible unittest invocation | From each **`examples/<name>/`**, documented command with **`-f`** to **`helm/tests/<suite>.yaml`** succeeds; suite **`values:`** points at that example’s **`values.yaml`**. |

### 4.5 `[DALC-REQ-HELM-UNITTEST-004]` (if multi-setup example)

| Scenario | Check |
|----------|-------|
| Every documented setup file has unittest coverage | e.g. **`with_observability`**: each README-listed **`values*.yaml`** appears in at least one **`values:`** entry or **`it:`** override with matching assertions. |

### 4.6 `[DALC-VER-003]` matrix

| Check |
|-------|
| Exactly one row per promoted requirement ID; **Evidence** column lists **`helm/tests/...`** paths for Helm unittest rows updated in this change. |

### 4.7 Gates (commands)

```bash
# Per example (from repo root)
for d in examples/*/; do ( cd "$d" && helm dependency build --skip-refresh && chart=$(basename "$d" | tr -d '/') && helm unittest -f "../../helm/tests/${chart//-/_}_test.yaml" . ); done

python3 scripts/check_spec_traceability.py

ct lint --config ct.yaml --all
```

## 5. TDD-style execution (tests first, then wiring)

**Interpretation:** The “tests” are the **helm-unittest YAML** and the **CI command**. Red phase: point CI and suites at **`helm/tests/`** with **`values:`** before deleting old files, or copy suites first with **`values:`** and run unittest **before** deleting **`examples/*/tests/`** — either way, **do not delete** old suites until **`helm unittest -f`** passes from each example directory.

### Stage A — Suites + `values:` (fail then pass)

**Write first:** Create **`helm/tests/<suite>_test.yaml`** copies with top-level **`values: - ../../examples/<dir>/values.yaml`**, identical **`suite` / `release` / `tests`** bodies and traceability comments.

**Then:** Run **`helm unittest -f`** from each **`examples/<dir>/`** until all suites pass. **Then** delete **`examples/*/tests/*.yaml`** and empty **`tests/`** dirs.

### Stage B — CI + README

**Adjust first:** `.github/workflows/ci.yml` loop to use **`-f "../../helm/tests/${chart//-/_}_test.yaml"`** (or explicit list if an example intentionally has no suite — then document exception in **`helm/tests/AGENTS.md`** and CI).

**Then:** Update root **`README.md`** “Local parity” Helm section to match CI exactly.

### Stage C — Traceability + rules + promoted specs

**Write first:** Update **`docs/spec-test-traceability.md`** evidence column paths (**`examples/.../tests/` → `helm/tests/`**).

**Then:** Update **`.cursor/rules/spec-traceability.mdc`**, **`docs/AGENTS.md`** (and root **`AGENTS.md`** if it references old paths). Merge **`openspec/changes/consolidate-helm-tests/specs/**`** into **`openspec/specs/dalc-requirement-verification/spec.md`** and **`openspec/specs/dalc-helm-unittest/spec.md`**. Run **`python3 scripts/check_spec_traceability.py`** until exit **0**.

### Stage D — Discoverable docs

**Add/update:** **`helm/tests/AGENTS.md`**, **`examples/AGENTS.md`** (migrate from **`examples/AGENT.md`** if present), **`examples/README.md`**. **Delete** **`examples/AGENT.md`** after link migration.

## 6. Acceptance checklist

- [ ] No **`examples/*/tests/`** helm-unittest YAML remains (only **`helm/tests/`**).
- [ ] Every suite under **`helm/tests/`** lists correct **`values:`** for its example.
- [ ] **`helm unittest -f`** passes for every **`examples/*/`** chart the CI matrix includes.
- [ ] **`docs/spec-test-traceability.md`** evidence paths and promoted spec prose match **`helm/tests/`**.
- [ ] **`python3 scripts/check_spec_traceability.py`** exits **0**.
- [ ] **`ct lint --config ct.yaml --all`** passes if chart paths touched.

## 7. Commands summary

```bash
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/<suite_underscore>.yaml" .
python3 scripts/check_spec_traceability.py
ct lint --config ct.yaml --all
```

`````
