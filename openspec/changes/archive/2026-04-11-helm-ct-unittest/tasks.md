## 1. Chart-testing (`ct`) configuration

- [x] 1.1 Add `ct.yaml` (or `ct.yml`) under `this repository` with `chart-dirs` for `helm/chart` and `examples` (or explicit example subcharts), matching layout from `ci.sh` today.
- [x] 1.2 Add optional `.yamllint` / `.ct` config only if `ct lint` fails on repository defaults; align with [chart-testing](https://github.com/helm/chart-testing) search paths.
- [x] 1.3 Verify `helm dependency build --skip-refresh` ordering remains before any `ct lint` or `helm unittest` invocation.

## 2. helm-unittest suites

- [x] 2.1 Add `tests/*_test.yaml` under `examples/hello-world` asserting zero `CronJob` documents and zero `app.kubernetes.io/component: rag` labels with default values (replaces the corresponding `grep -c` checks).
- [x] 2.2 Add unittest suite(s) under `examples/with-scrapers` asserting at least one `CronJob` and at least one RAG component label with default example values.
- [x] 2.3 Add unittest suite(s) under `examples/with-observability` asserting scrape annotations and exactly two `ServiceMonitor` resources (match prior `ci.sh` thresholds using `documentSelector` / path asserts as needed).
- [x] 2.4 Add unittest coverage for `helm/chart` if any invariant is testable standalone; otherwise document that library validation is via `ct lint` + example charts, and confirm no weaker checks than before.

## 3. CI script and documentation

- [x] 3.1 Update `ci.sh` to run `ct lint` (from repo root or chart root per `ct.yaml`) and `helm unittest` for each chart that has tests; remove obsolete `helm template | grep -c` blocks once parity is verified.
- [x] 3.2 Document installing `ct` (e.g. `brew install chart-testing` or pinned Docker `quay.io/helmpack/chart-testing:v3.14.0` — confirm [chart-testing releases](https://github.com/helm/chart-testing/releases) before freezing) and official [helm-unittest](https://github.com/helm-unittest/helm-unittest) (`helm plugin install https://github.com/helm-unittest/helm-unittest.git` or Docker `helmunittest/helm-unittest`, confirm [helm-unittest releases](https://github.com/helm-unittest/helm-unittest/releases) e.g. v1.0.3); define fail vs skip when binaries are missing.
- [x] 3.3 Run full local `ci.sh` and fix any chart or config issues until green.

## 4. Optional alignment

- [x] 4.1 If desired, update `projects/ai-stack/ci.sh` to install unittest from `helm-unittest/helm-unittest` instead of the quintush fork, and re-run that project’s Helm test step.
