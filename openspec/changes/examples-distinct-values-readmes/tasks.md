## 1. Prerequisite

- [ ] 1.1 Confirm **`openspec/changes/consolidate-helm-tests`** is applied (central **`helm/tests/`**, CI **`helm unittest -f`**, docs/traceability paths updated); do not start example splits on obsolete **`examples/*/tests/`** layout.

## 2. Specs and traceability

- [ ] 2.1 Promote **`cfha-example-values-files`** and **`cfha-helm-unittest`** deltas from this change into **`openspec/specs/`** per OpenSpec apply/archive conventions (preserve requirement IDs).
- [ ] 2.2 Update **`docs/spec-test-traceability.md`** with rows for **`[CFHA-REQ-EXAMPLE-VALUES-FILES-001]`**, **`[CFHA-REQ-EXAMPLE-VALUES-FILES-002]`**, and **`[CFHA-REQ-HELM-UNITTEST-004]`**; set evidence to planned **`helm/tests/`** paths and CI tier consistent with existing Helm unittest rows.
- [ ] 2.3 Run **`python3 scripts/check_spec_traceability.py`** and fix any gaps.

## 3. Example values files and READMEs

- [ ] 3.1 Choose at least one **multi-mode** example (see **`design.md`** — e.g. **`with-scrapers`**) and split **`values.yaml`** into **`values.yaml`** (default story) plus **`values.<setup>.yaml`** files per documented setup; move or deduplicate comments accordingly.
- [ ] 3.2 Add or update **`examples/<name>/README.md`** to index every values file, explain differences, and show **`helm upgrade --install`** with **`-f`** where needed.
- [ ] 3.3 Update top-level **`examples/README.md`** index row if the example’s story or install instructions change materially.

## 4. Helm unittest

- [ ] 4.1 Extend the matching suite under **`helm/tests/`** with a **`values:`** block (or equivalent) **per** documented values file; add **`it:`** cases with **`# [CFHA-REQ-HELM-UNITTEST-004]`** (and example-values IDs as appropriate) asserting setup-specific rendering.
- [ ] 4.2 From each **`examples/<name>/`**, run **`helm dependency build --skip-refresh`** then **`helm unittest -f`** against the consolidated suite file; all tests pass.

## 5. Verification

- [ ] 5.1 Run CI-equivalent checks: **`ct lint`**, Helm unittest loop, **`python3 scripts/check_spec_traceability.py`**, and any other steps from **`.github/workflows/ci.yml`** relevant to touched paths.
