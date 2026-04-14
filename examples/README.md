# Examples (application charts)

These are **Helm application** charts. Each one depends on the **Declarative Agent Library** chart at `file://../../helm/chart` and supplies release-specific `values.yaml` under the subchart key **`declarative-agent-library`**.

For the shared library, runtime API, Skaffold/DevSpace, and kind walkthroughs, see the project [README](../README.md).

## Index

| Directory | Purpose |
|-----------|---------|
| [**hello-world**](hello-world/) | Smallest useful install: image, `systemPrompt`, default service on **8088**. Use this as the template for new apps. |
| [**with-observability**](with-observability/) | Same baseline plus **`o11y`**: `prometheus.io/*` annotations, optional **ServiceMonitor**, JSON logs via `HOSTED_AGENT_LOG_FORMAT`. See [docs/observability.md](../docs/observability.md). Extra **`values-o11y-no-rag.yaml`** fixture: o11y on without scraper jobs (no RAG) for template tests. |
| [**with-scrapers**](with-scrapers/) | **reference** scraper `CronJob` (hourly schedule); enabled job deploys **RAG**. Default **`values.yaml`** plus **`values.jira-only.yaml`** / **`values.slack-only.yaml`** for single-parent setups; see [with-scrapers/README.md](with-scrapers/README.md). CI asserts scraper + RAG rendering for each file via `helm/tests/with_scrapers_test.yaml`. |
| [**checkpointing**](checkpointing/) | **`observability.checkpoints.enabled: true`** with **memory** backend (library default remains checkpoints off). |

## Using an example

From the example directory (after cloning this repo):

```bash
helm dependency build --skip-refresh   # or helm dependency update when the library version changes
helm upgrade --install <release> . -n <namespace> --wait
```

Build/load the container image and port-forward as described in the main README (default agent image `config-first-hosted-agents:local` on kind).

## Adding a new example

1. Copy **hello-world** as a skeleton (Chart.yaml, `values.yaml`).
2. Change `Chart.yaml` **`name`** and `description` to match the capability you are demonstrating.
3. Adjust `values.yaml` only for that story; keep defaults easy to read.
4. Run `helm dependency build` (or `update`) and commit **Chart.lock**.
5. Register the chart in this README, in the parent [README](../README.md) layout table if appropriate, and extend [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (Helm job loops `examples/*/`) when CI should lint/template the new chart.
6. Add **`helm/tests/<suite>_test.yaml`** with `values:` pointing at this example’s **`values.yaml`**, and update **`docs/spec-test-traceability.md`** when new SHALL evidence is introduced.

See [AGENTS.md](AGENTS.md) and [helm/tests/AGENTS.md](../helm/tests/AGENTS.md) for unittest layout and automation conventions.

## Integration (kind + Prometheus + o11y)

The **with-observability** chart is covered by an opt-in script that deploys to kind, installs Prometheus, hits the trigger endpoint, and queries PromQL. See [docs/observability.md](../docs/observability.md#integration-test-kind--prometheus).
