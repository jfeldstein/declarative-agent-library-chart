# helm/tests/chart

Helm chart tests for the **Declarative Agent Library Chart** (`declarative-agent-library-chart`, alias `declarative-agent` in examples) live in the chart itself:

- [`../chart/templates/tests/test-trigger.yaml`](../chart/templates/tests/test-trigger.yaml) — `helm.sh/hook: test` Job that `POST`s `/api/v1/trigger` and asserts the body contains `Hello`.

Run after install (same namespace as the release):

```bash
helm test <release-name>
```
