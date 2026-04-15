# Agent notes — `examples/`

Guidance for assistants and maintainers working under **`examples/`**.

## Scope

- Each subdirectory is a **standalone Helm application chart** (type `application`) that vendors **`declarative-agent-library`** from `../../helm/chart`.
- Values for the library live under the key **`declarative-agent-library:`** in each example’s `values.yaml` (matches the dependency `name` in `Chart.yaml`).

## Helm unittest suites

- Suites are **not** colocated under `examples/*/tests/`. They live under **`helm/tests/`** (one `*_test.yaml` per covered example). Each suite’s **`values:`** block references this directory’s **`values.yaml`** using a path relative to the suite file (see [helm/tests/AGENTS.md](../helm/tests/AGENTS.md)).
- When you add or change an example that CI validates, add or update the matching suite under **`helm/tests/`**, extend **`.github/workflows/ci.yml`** if the chart is new, and update **`docs/spec-test-traceability.md`** when requirements are evidenced there.

## Keep `hello-world` minimal

- **hello-world** should stay the smallest copy-paste starting point: image + `systemPrompt` (+ whatever the docs promise as “minimal”).
- **Do not** add optional feature demos (Kubernetes observability values, RAG, scrapers, etc.) to hello-world’s default `values.yaml` just to show a capability.
- For new capabilities, add **`examples/<short-name>/`** with its own `Chart.yaml`, `values.yaml`, and committed **`Chart.lock`**, and document it in [README.md](README.md).
- **with-scrapers** is the place for RAG + scraper `CronJob` defaults (validated by [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)); keep **hello-world** free of scraper/RAG demos in `values.yaml`.

## When you touch examples

1. Run **`helm dependency build --skip-refresh`** (or `update` if the library digest changed) from the example directory and commit **`Chart.lock`** when it changes.
2. **`charts/*.tgz`** are **gitignored**; run **`helm dependency build`** before `helm unittest` / install (CI does this each run).
3. If CI should validate the chart: extend [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (and matching local Helm commands in the root [README](../README.md)).
4. Update [README.md](README.md) and, when relevant, the layout table in the project [README](../README.md).

## Cross-links

- Observability (metrics, logs, Grafana): [docs/observability.md](../docs/observability.md), [grafana/README.md](../grafana/README.md).
- RAG HTTP contract: [docs/rag-http-api.md](../docs/rag-http-api.md).
- Unittest layout: [helm/tests/AGENTS.md](../helm/tests/AGENTS.md).
