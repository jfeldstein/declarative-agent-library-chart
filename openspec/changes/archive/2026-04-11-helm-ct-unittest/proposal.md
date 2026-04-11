## Why

`ci.sh` validates Helm charts with `helm lint` and `helm template` output piped through `grep -c`, which counts substrings in flattened YAML rather than asserting on rendered documents. That pattern is brittle (ordering, multi-document noise, false positives) and scales poorly as charts grow. Adopting the community-standard [chart-testing](https://github.com/helm/chart-testing) (`ct`) and [helm-unittest](https://github.com/helm-unittest/helm-unittest) aligns local CI with how mature chart repos lint and test templates, and replaces ad-hoc greps with explicit, reviewable test suites.

## What Changes

- Add **chart-testing** (`ct`) configuration (e.g. `ct.yaml` / `ct.yml`) scoped to `this repository` chart directories (`helm/chart`, `examples/*`), including chart dependency build expectations where `ct` runs.
- Install or invoke **`ct lint`** (and optionally `ct lint-and-install` only if/when a cluster job exists—default scope is **lint-only** in CI to avoid requiring Kubernetes) instead of relying on grep-based template checks.
- Add **helm-unittest** suites under each chart (or a documented layout) that encode today’s grep assertions: for default `examples/hello-world`, zero `CronJob` manifests and zero `app.kubernetes.io/component: rag` labels; for `examples/with-scrapers`, at least one `CronJob` and at least one RAG component label; for `examples/with-observability`, Prometheus scrape annotations and ServiceMonitor counts matching current thresholds.
- Update **`ci.sh`** (and any GitHub Actions that mirror it) to run `ct` and `helm unittest`, removing the `grep -c` blocks once parity is proven.
- Document **local prerequisites**: `ct` binary or `quay.io/helmpack/chart-testing` image, Helm 3, and `helm plugin install https://github.com/helm-unittest/helm-unittest.git` (or pinned release), with clear skip/fail behavior when tools are missing.
- **Optional follow-up**: align `projects/ai-stack` helm-unittest plugin URL with the official **helm-unittest/helm-unittest** repo if still using a fork—out of scope unless tasks explicitly include it.

## Capabilities

### New Capabilities

- `cfha-chart-testing-ct`: Use Helm [chart-testing](https://github.com/helm/chart-testing) to lint charts in the config-first-hosted-agents tree (chart dirs, excluded paths, dependency handling, CI entrypoint).
- `cfha-helm-unittest`: Use [helm-unittest](https://github.com/helm-unittest/helm-unittest) for YAML-based assertions on rendered templates, replacing grep-based counts in `ci.sh`.

### Modified Capabilities

- _(none — no existing `openspec/specs/` entries define Helm CI behavior today.)_

## Impact

- **Primary**: `ci.sh`, new `ct` config file(s), new `tests/*_test.yaml` (or equivalent) under affected charts, `examples/*/Chart.lock` / dependency build flow as required by `ct`.
- **Tooling**: Developers and CI need `ct` and the helm-unittest plugin (or Docker equivalents); optional network for `helm dependency build` when charts pull remote deps.
- **Risk**: Low for behavior if unittest suites reproduce current grep thresholds; medium for CI time until caches or targeted chart lists are tuned.
