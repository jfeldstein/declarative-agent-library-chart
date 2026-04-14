# Agent notes — `helm/tests/`

Helm **unittest** suites for **example application charts** live here. Each file corresponds to one example under `examples/<name>/`.

## Naming

- Example directory **`hello-world`** → suite file **`hello_world_test.yaml`** (hyphens in the chart folder become underscores in the suite filename, matching CI).

## Values wiring

Each suite MUST reference the example’s committed **`values.yaml`** with a path **relative to the suite file** (the suite lives under **`helm/tests/`**, so use **`../../examples/<dir>/values.yaml`**):

```yaml
values:
  - ../../examples/hello-world/values.yaml
```

Run **`helm unittest`** from **inside** `examples/<example-dir>/` with **`-f`** pointing at the suite file under this directory (see `.github/workflows/ci.yml` and the root `README.md`).

## Maintainer loop

The library chart is **values-driven**: meaningful surface area SHOULD appear in an **example** with unittest coverage. Adding a new example includes registering CI and adding `helm/tests/<suite>_test.yaml` with traceability `#` comments per **`docs/spec-test-traceability.md`** and **[DALC-VER-002]**.
