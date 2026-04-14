## Why

This repository’s core product is the **library chart** (`helm/chart/`); the primary developer experience and integration surface is **values-driven**—operators and integrators learn and validate behavior through **`values.yaml`** under **`examples/`**. That makes two expectations first-class:

1. **Every meaningful component or configuration path** worth shipping SHOULD appear in at least one **example** chart so it stays documented, copy-pasteable, and linted by chart-testing.
2. **Every example** that demonstrates library behavior SHOULD have **solid helm-unittest** coverage so rendered manifests match those intentions (no silent regressions in templates or defaults).

Consolidation supports that pattern: unittest YAML today lives beside each example under `examples/<name>/tests/`, which splits “what values mean” (still in the example) from “what we assert about rendering” in a way that is easy to miss when adding examples or new library surface area. Centralizing suites under **`helm/tests/`** keeps example directories focused on installable chart assets (`Chart.yaml`, `values.yaml`, locks) while preserving **one suite per example**, wired to that example’s **`values.yaml`** via explicit **`values:`** entries—so the link between **documented values** and **asserted output** stays obvious and maintainable as the library grows.

## What Changes

- Move each `examples/<example-name>/tests/<example-name>_test.yaml` to `helm/tests/<example-name>_test.yaml` (kebab/snake naming preserved per file).
- Remove empty `examples/*/tests/` directories after the move.
- Each consolidated suite SHALL list `values:` pointing at `../examples/<example-name>/values.yaml` (paths relative to the suite file under `helm/tests/`), so templates still render in the context of the **example** chart when unittest is pointed at that chart.
- CI and local docs SHALL run `helm unittest` against each example chart using `-f` to select the matching file under `helm/tests/` (example charts no longer carry `tests/*_test.yaml` by default).
- Add discoverable maintainer docs: **`examples/AGENTS.md`** (supersedes **`examples/AGENT.md`** for the same role—migrate content and update links), **`helm/tests/AGENTS.md`**, and extend **`examples/README.md`** so future agents know where suites live, how values are referenced, and that **library surface area ↔ examples ↔ helm-unittest** is the expected maintainer loop for this repo.
- Update **test-to-spec traceability** evidence paths in **`docs/spec-test-traceability.md`** and any normative spec text that currently names **`examples/*/tests/`** as the location for Helm unittest ID comments.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- **`cfha-requirement-verification`**: **[CFHA-VER-002]** currently requires Helm unittest ID comments for suites under **`examples/*/tests/`**; update the SHALL to the new canonical path under **`helm/tests/`** (and keep the same comment rules).
- **`cfha-helm-unittest`**: **[CFHA-REQ-HELM-UNITTEST-003]** “Reproducible unittest invocation” scenario mentions charts that contain **`tests/`** suites; update to describe the supported pattern (example chart + **`helm unittest -f …`** against **`helm/tests/*_test.yaml`**) so the spec matches CI after consolidation.

## Impact

- **`.github/workflows/ci.yml`**: Helm job must pass `-f` globs or per-chart file paths when running unittest from each `examples/<name>/`.
- **`docs/spec-test-traceability.md`**, **`scripts/check_spec_traceability.py`**: Matrix evidence paths only (script has no hardcoded examples path beyond reading the matrix—verify).
- **`examples/README.md`**, **`examples/AGENT.md`** → **`examples/AGENTS.md`**: Documentation and cross-links.
- **Root / other READMEs** that mention unittest location (e.g. **`README.md`**, **`docs/development-log.md`**) as needed for parity with CI.
- **OpenSpec / ADR references** that mention `examples/*/tests/*.yaml` in prose (e.g. **`AGENTS.md`**, **`.cursor/rules/spec-traceability.mdc`**) should be aligned in the apply phase.
