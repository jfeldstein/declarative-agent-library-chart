## 1. Suites and values wiring

- [ ] 1.1 Create `helm/tests/` and add one suite file per relocated example (`hello_world_test.yaml`, `with_observability_test.yaml`, `with_scrapers_test.yaml`, `checkpointing_test.yaml`), preserving existing `suite:`, `release:`, `tests:`, `template:`, and `# Traceability:` content.
- [ ] 1.2 At the top of each suite (after comments), add `values:` with `- ../examples/<example-dir>/values.yaml` using the correct `<example-dir>` for that chart.
- [ ] 1.3 Remove `examples/*/tests/` directories and their YAML files after confirming paths.

## 2. CI and local parity

- [ ] 2.1 Update `.github/workflows/ci.yml` Helm job: after `cd "examples/$chart"` and `helm dependency build --skip-refresh`, run `helm unittest -f "../../helm/tests/${chart//-/_}_test.yaml" .` (or equivalent) so unittest loads the centralized suite while the chart context stays the example.
- [ ] 2.2 Update root `README.md` (and any “Local parity” Helm commands) so contributors run the same `-f` pattern.

## 3. Spec–test traceability and promoted specs

- [ ] 3.1 Replace every **`examples/.../tests/..._test.yaml`** evidence path in `docs/spec-test-traceability.md` with the matching `helm/tests/...` path; extend rows if a suite evidences requirements but was missing from the matrix (e.g. checkpointing).
- [ ] 3.2 Update `.cursor/rules/spec-traceability.mdc` and `docs/AGENTS.md` prose that refers to `examples/*/tests/` for Helm unittest to `helm/tests/`.
- [ ] 3.3 Merge this change’s deltas into promoted specs: apply `openspec/changes/consolidate-helm-tests/specs/cfha-requirement-verification/spec.md` and `.../cfha-helm-unittest/spec.md` to `openspec/specs/<capability>/spec.md` per OpenSpec archive/apply conventions (IDs unchanged on modified requirements).

## 4. Discoverable documentation

- [ ] 4.1 Add `helm/tests/AGENTS.md` describing directory purpose, naming rule (`hello-world` → `hello_world_test.yaml`), `values:` convention, CI `helm unittest -f` invocation, and that the library chart is values-driven—**examples + unittest** are how we keep template behavior honest.
- [ ] 4.2 Add `examples/AGENTS.md` by migrating content from `examples/AGENT.md`, adding a short section: Helm unittest suites live under `helm/tests/`; new examples need a suite file + CI registration; new or notable library components SHOULD land in an example with unittest coverage.
- [ ] 4.3 Update `examples/README.md` (link to `AGENTS.md`, “Adding a new example” step for unittest location).
- [ ] 4.4 Delete `examples/AGENT.md` after links are updated.

## 5. Verification

- [ ] 5.1 From repo root: for each `examples/*/`, `cd` there, `helm dependency build --skip-refresh`, then `helm unittest -f` against the matching `helm/tests/*_test.yaml`; all pass.
- [ ] 5.2 Run `python3 scripts/check_spec_traceability.py` (exit 0).
- [ ] 5.3 Run `ct lint --config ct.yaml --all` if touched paths affect chart metadata (expect unchanged behavior).
