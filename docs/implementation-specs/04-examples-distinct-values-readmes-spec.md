# Step 4: examples-distinct-values-readmes

`````
# Downstream LLM implementation brief: `examples-distinct-values-readmes`

## 0. Context (read first)

- **Linear checklist:** Tier **4** in `docs/openspec-implementation-order.md` — **after** `consolidate-helm-tests` (step 3): one committed **values file per demonstrated setup**, **per-example README** index, and **helm-unittest** loads **each** documented file under **`helm/tests/`** with assertions that match the README.
- **Upstream alignment:** Re-read [`docs/implementation-specs/01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) (values shape: `observability` vs `o11y`, `checkpoints`, etc.), [`02-consolidate-naming-spec.md`](02-consolidate-naming-spec.md) (**as of `main` before step 2:** vendored library folder **`charts/declarative-agent-library/`**; **target:** **`charts/declarative-agent-library-chart/`** after rename; parent values **`agent:`**), and [`03-consolidate-helm-tests-spec.md`](03-consolidate-helm-tests-spec.md) (suite location, **`values:`** relative paths, **`helm/tests/checkpointing_test.yaml`**). **This brief’s “current tree” snapshot is the repo as of authoring;** if steps 1–3 merged on your branch, **grep and match their target layout** instead of stale names below.
- **Authoritative change bundle:** `openspec/changes/examples-distinct-values-readmes/` — `proposal.md`, `design.md`, `tasks.md`, delta specs under `specs/*/spec.md`. **Note:** proposal text may still say `cfha-*`; promoted capability folder is **`dalc-example-values-files`** and **`dalc-helm-unittest`** (see `openspec/specs/`).
- **Non-goals:** No change to **library** `helm/chart` default semantics; no replacement of kind/Prometheus integration tests; cardinality-aware (single-story examples stay single-file).

## 1. Goal

1. For any example that **documents more than one** materially distinct Helm values story, provide **one committed `values*.yaml` per story** and document every file in **`examples/<name>/README.md`** (purpose, distinguishing keys, default vs `-f` install).
2. For **`helm/tests/<example_underscore>_test.yaml`**, ensure **each README-listed values file** appears in at least one **`values:`** list (suite-level or **`it:`**-level) with **`it:`** assertions that match what the README claims for that file (**[DALC-REQ-HELM-UNITTEST-004]**).
3. Keep **test-to-spec traceability** (IDs on requirements, matrix rows, `#` / docstring citations per **ADR 0003** / **DALC-VER-005**).

## 2. Current repository layout (baseline for implementers — reconcile after steps 1–3)

### 2.1 Filesystem (examples + suites)

```text
examples/
  README.md                          # index of all examples; mentions with-observability extra file
  AGENTS.md
  hello-world/
    values.yaml                      # single story
  checkpointing/
    values.yaml                      # single story — **Helm contract (post–step 1):** **`<library-key>.checkpoints`** (e.g. `declarative-agent-library.checkpoints` before step 2 renames the parent key). **Not** `declarative-agent-library.observability.checkpoints`. *Pre–dedupe trees may still nest checkpoints under `observability` until step 1 merges.*
  with-scrapers/
    README.md                        # table: values.yaml, values.jira-only.yaml, values.slack-only.yaml
    values.yaml
    values.jira-only.yaml
    values.slack-only.yaml
  with-observability/
    values.yaml                      # default: o11y + jira job → RAG deployed
    values-o11y-no-rag.yaml          # fixture: o11y on, scrapers disabled → no RAG (unittest negative path)
    # (no README.md in this directory today — gap vs [DALC-REQ-EXAMPLE-VALUES-FILES-001] if “two setups” is in scope)

helm/tests/
  hello_world_test.yaml
  checkpointing_test.yaml            # checkpoint env from values.yaml (see step 1 path)
  with_scrapers_test.yaml            # suite values: default; per-it values: jira-only + slack-only files
  with_observability_test.yaml       # suite values: default; per-it values: values-o11y-no-rag.yaml
  chart/                             # optional nested content (present in repo)
```

### 2.2 Parent values key and vendored chart folder (today vs post–steps 1–3)

```yaml
# Today (typical example parent values root)
declarative-agent-library:
  # library tunables…
```

```text
# As of main before step 2: unittest template: paths (representative)
charts/declarative-agent-library/templates/deployment.yaml
```

```yaml
# After step 2 (target — do not reintroduce deprecated roots)
agent:
  # library tunables…
```

```text
# After step 2 (target)
charts/declarative-agent-library-chart/templates/deployment.yaml
```

### 2.3 Values naming conventions observed

| Pattern | Example |
|---------|---------|
| Default | `values.yaml` |
| Dot + slug | `values.jira-only.yaml`, `values.slack-only.yaml` |
| Hyphen suffix | `values-o11y-no-rag.yaml` (legacy “fixture” naming; rename only with step 1 key renames + full reference grep) |

**Interface contract:** Pick **one** documented pattern per example (or document mixed patterns explicitly in `examples/README.md`) so README + CI + unittest paths stay grep-friendly.

## 3. Entities and interfaces

### 3.1 Example chart “values story”

```typescript
interface ExampleValuesStory {
  /** Committed path relative to examples/<name>/ */
  file: string; // e.g. "values.yaml" | "values.jira-only.yaml"
  /** Short intent for README table */
  intent: string;
  /** Install line uses default values.yaml or extra -f */
  installSnippet: string; // helm upgrade --install … [-f <file>]
}
```

### 3.2 Per-example README (normative shape)

```markdown
# Example: `<name>`
<!-- optional: Traceability: [DALC-REQ-EXAMPLE-VALUES-FILES-001] … -->
## Values files
| File | Use when |
| … | … |
## Install
… default …
… -f for alternates …
```

### 3.3 Helm-unittest suite fragment (per documented non-default file)

```yaml
# helm/tests/<example_underscore>_test.yaml
values:
  - ../../examples/<example-dir>/values.yaml

tests:
  - it: <setup-specific description>  # [DALC-REQ-HELM-UNITTEST-004] [DALC-REQ-EXAMPLE-VALUES-FILES-001]
    values:
      - ../../examples/<example-dir>/<non-default>.yaml
    template: charts/<subchart>/templates/<file>.yaml
    asserts: [ ... ]
```

**Contract:** Assertions **SHALL** match README promises (counts of CronJob/ConfigMap/RAG, ServiceMonitor presence/absence, annotation keys, etc.).

### 3.4 Traceability surfaces

```text
docs/spec-test-traceability.md       # rows for [DALC-REQ-EXAMPLE-VALUES-FILES-001|002], [DALC-REQ-HELM-UNITTEST-004]
openspec/specs/dalc-example-values-files/spec.md
openspec/specs/dalc-helm-unittest/spec.md   # §004
examples/<name>/README.md           # may carry HTML comment with IDs (see with-scrapers)
helm/tests/*.yaml                   # # Traceability: … and per-it # [DALC-REQ-…]
```

## 4. Normative specs and tests (enumerate; all must end green)

### 4.1 Promoted specs (implement / verify against)

| ID / doc | Path |
|----------|------|
| **[DALC-REQ-EXAMPLE-VALUES-FILES-001]** | `openspec/specs/dalc-example-values-files/spec.md` |
| **[DALC-REQ-EXAMPLE-VALUES-FILES-002]** | same |
| **[DALC-REQ-HELM-UNITTEST-004]** | `openspec/specs/dalc-helm-unittest/spec.md` |
| Related baseline | **[DALC-REQ-HELM-UNITTEST-001]** scenarios for with-scrapers / with-observability (do not weaken) |

### 4.2 Concrete assertions (current tree)

| Example | Values files | README location | Unittest file | Coverage note |
|---------|--------------|-----------------|---------------|----------------|
| with-scrapers | `values.yaml`, `values.jira-only.yaml`, `values.slack-only.yaml` | `examples/with-scrapers/README.md` | `helm/tests/with_scrapers_test.yaml` | Default suite `values:` + per-`it:` `values:` for jira-only and slack-only; ConfigMap/CronJob/RAG counts match README. |
| with-observability | `values.yaml`, `values-o11y-no-rag.yaml` | **Only** named in `examples/README.md` today | `helm/tests/with_observability_test.yaml` | Both files loaded; **add `examples/with-observability/README.md`** indexing both if you treat this as a multi-setup example per **[DALC-REQ-EXAMPLE-VALUES-FILES-001]**. |
| hello-world | `values.yaml` only | (inline / parent index) | `helm/tests/hello_world_test.yaml` | Single story — no extra files required. |
| checkpointing | `values.yaml` only | (parent index) | `helm/tests/checkpointing_test.yaml` | Single story — no extra files required. |

### 4.3 Gates (commands)

```bash
# From repo root — same shape as step 3 / CI (.github/workflows/ci.yml uses --skip-refresh)
for d in examples/*/; do
  ( cd "$d" && helm dependency build --skip-refresh && chart=$(basename "$d" | tr -d '/') && helm unittest -f "../../helm/tests/${chart//-/_}_test.yaml" . )
done

python3 scripts/check_spec_traceability.py
ct lint --config ct.yaml --all
```

**Canonical commands:** [`docs/implementation-specs/README.md`](README.md) when present, else root **`README.md`**.

## 5. TDD-style execution (tests first where behavior changes)

**Rule:** If you add or split values files or README claims, **extend `helm/tests/` first** (or adjust assertions concurrently) so CI fails until templates + values match the documented story.

### Stage A — Close README / spec gaps (example: with-observability)

**Write first:** `examples/with-observability/README.md` with **Values files** table (default vs no-RAG fixture), **Install** with `-f values-o11y-no-rag.yaml`, and traceability comment if used as matrix evidence.

**Then:** Confirm `helm/tests/with_observability_test.yaml` already references both files; add **`it:`** / comments tying **[DALC-REQ-HELM-UNITTEST-004]** to README-listed files if matrix requires explicit comment on new README path.

**Green when:** unittest loop + `check_spec_traceability.py` pass; README claims match assertions.

### Stage B — Multi-mode examples beyond current set

**Write first:** New `values*.yaml` + failing **`it:`** blocks for the new file.

**Then:** Split values, update README + `examples/README.md` index row, extend suite **`values:`** entries.

**Green when:** §4.3 gates pass.

### Stage C — OpenSpec / matrix hygiene

**Implement:** If delta specs under `openspec/changes/examples-distinct-values-readmes/specs/` are not yet merged, promote per project OpenSpec workflow; fix **`cfha-*`** → **`dalc-*`** in human-readable proposal text when editing.

**Green when:** `python3 scripts/check_spec_traceability.py` exits **0**.

## 6. Acceptance checklist

- [ ] Every example with **two or more** documented values setups has **`examples/<name>/README.md`** listing each **`values*.yaml`** and how to install with **`-f`** (**[DALC-REQ-EXAMPLE-VALUES-FILES-001]**, **[002]**).
- [ ] Matching **`helm/tests/<suite>_test.yaml`** loads **each** listed file in ≥1 **`values:`** block with setup-specific assertions (**[DALC-REQ-HELM-UNITTEST-004]**).
- [ ] Single-file examples remain single-file unless product intentionally adds a second story.
- [ ] `docs/spec-test-traceability.md` evidence paths and `#` / README traceability comments align with **ADR 0003**.
- [ ] §4.3 commands all succeed.

## 7. Commands summary

```bash
cd examples/<example> && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/${chart//-/_}_test.yaml" .
python3 scripts/check_spec_traceability.py
ct lint --config ct.yaml --all
```

**Canonical commands:** [`docs/implementation-specs/README.md`](README.md) when present, else root **`README.md`**.
`````
