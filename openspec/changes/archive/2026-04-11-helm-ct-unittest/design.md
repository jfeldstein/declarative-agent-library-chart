## Context

`this repository` ships a library chart under `helm/chart` and example app charts under `examples/*`. CI today runs `helm lint`, `helm dependency build`, `helm template`, and shell `grep -c` checks for CronJobs, `app.kubernetes.io/component: rag` (RAG workload on/off), scrape annotations, and ServiceMonitors. Other chart repositories may already use `ct` and `helm unittest`; this tree previously did not. The official [chart-testing](https://github.com/helm/chart-testing) project documents `ct lint` (yamllint, yamale schema, chart metadata) and the official [helm-unittest](https://github.com/helm-unittest/helm-unittest) plugin provides structured assertions on rendered manifests without a cluster.

## Goals / Non-Goals

**Goals:**

- Replace grep-based template assertions in `ci.sh` with **helm-unittest** suites that express the same intent (document counts, kinds, key paths) in maintainable YAML.
- Integrate **`ct lint`** for charts in this repository so lint rules and chart list discovery match common Helm repo practice.
- Keep CI runnable locally with clear messages when `ct` or the unittest plugin is absent (parity with current optional Helm block or stricter policy as implemented).
- Pin or document tool versions (Docker image tag for `ct`, helm-unittest release) to avoid flaky CI. As of 2026-04, upstream tags to reference in docs/CI are **chart-testing [v3.14.0](https://github.com/helm/chart-testing/releases)** (`quay.io/helmpack/chart-testing:v3.14.0`) and **helm-unittest [v1.0.3](https://github.com/helm-unittest/helm-unittest/releases)** (verify [releases](https://github.com/helm-unittest/helm-unittest/releases) before pinning and bump when upgrading).

**Non-Goals:**

- Replacing integration tests that need a real cluster (e.g. kind + PromQL) with `ct install` in this change, unless explicitly added later.
- Rewriting all Helm logic or values schemas beyond what tests require.
- Migrating unrelated projects’ Helm CI in one pass (optional note for ai-stack plugin URL only in tasks if desired).

## Decisions

1. **`ct` scope: lint-only in default CI**  
   **Rationale**: `ct install` needs Kubernetes and longer runs; current pipeline only needs static validation. **Alternative**: `ct lint-and-install` in a dedicated workflow—defer until cluster CI exists.

2. **Chart roots and `chart-dirs`**  
   **Rationale**: Point `ct` at `helm/chart` and `examples` (or explicit subdirs) so the library and examples are linted. Use `ct.yaml` `chart-dirs` and `excluded-charts` if any path must be skipped. **Alternative**: Single meta-chart folder—rejected; layout is already split.

3. **Dependencies before `ct` / unittest**  
   **Rationale**: Example charts use `file://` dependencies; `helm dependency build` must run before lint/template/unittest (already done in `ci.sh`). **Alternative**: vendor tarballs—unnecessary for this repo.

4. **helm-unittest layout**  
   **Rationale**: Place `tests/*_test.yaml` per chart per upstream convention; map each former grep check to one or more tests with `documentSelector` or `matchRegex` / `equal` on stable paths. **Alternative**: Single mega-suite at repo root—rejected; harder to own per chart.

5. **Installation path for unittest**  
   **Rationale**: Document official plugin install `https://github.com/helm-unittest/helm-unittest.git`; CI may use `helmunittest/helm-unittest` Docker image for reproducibility. **Alternative**: quintush fork (used in ai-stack)—avoid for new work per user request.

## Risks / Trade-offs

- **[Risk] Developer friction if `ct` not installed** → **Mitigation**: Document Homebrew/Docker one-liners from [chart-testing README](https://github.com/helm/chart-testing); mirror optional skip behavior until team standardizes.
- **[Risk] Unittest snapshots churn** → **Mitigation**: Prefer explicit asserts over snapshots for small structural checks; pin plugin version.
- **[Risk] `ct` lint stricter than `helm lint` alone** → **Mitigation**: Add `.yamllint` / schema config under repo or `.ct` if defaults fail; fix charts rather than disabling rules blindly.
- **[Trade-off] CI duration** → **Mitigation**: Run only changed charts in PR workflows later via `ct list-changed`; full run on main.

## Migration Plan

1. Add `ct.yaml` and unittest test files; keep existing `grep` checks until unittest + `ct lint` pass in parallel.
2. Switch `ci.sh` to `ct lint` + `helm unittest` and remove grep blocks.
3. If GitHub Actions exist for this project, align steps with `ci.sh`.

## Open Questions

- Whether to **require** `ct` whenever Helm is required, or keep a soft skip for minimal dev machines (proposal leans toward documented install + consistent CI).
