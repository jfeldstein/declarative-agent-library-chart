## Why

The shared CFHA chart is currently an **application** chart under `template/chart/`, which implies it can be installed as a standalone release. Helm’s **library** chart type matches the actual intent: reusable templates and values that are always consumed through a parent **application** chart (for example `examples/hello-world`). Renaming `template/` to `helm/` also aligns the directory name with what it contains (Helm packaging) and avoids confusion with “Helm templates” as a generic term.

## What Changes

- Rename `template/` to `helm/` (chart, `src/` pointer, chart tests docs).
- Set the shared chart’s `Chart.yaml` **`type: library`** (and keep it versioned for dependency resolution).
- Update **application** consumers (e.g. `examples/hello-world`) so `Chart.yaml` / `Chart.lock` point at `file://../../helm/chart` and continue to render the same workload via the library dependency.
- Update **documentation**, **CI** (`ci.sh`), **.dockerignore**, and any path references that still say `template/`.

## Capabilities

### New Capabilities

- `cfha-helm-library`: Shared Helm **library** chart under `helm/`, repository layout (`helm/chart`, `helm/src`, `helm/tests/chart`), and the same functional requirements as today (values → ConfigMap/env, `POST /api/v1/trigger`, extension points) expressed for a non-installable library consumed by parent charts.
- `cfha-hello-world-example`: Minimal example **application** chart that depends on the library chart via `file://../../helm/chart`, `helm dependency update`, and unchanged hello-world acceptance (kind + `curl` on **8088**).

### Modified Capabilities

- (none — requirements live in this change’s new specs; root `openspec/specs/` has no prior CFHA capability to delta.)

## Impact

- **Helm**: Example charts remain `type: application`; only the shared chart becomes `type: library`. CI continues to `helm lint` / `helm template` via the example (or equivalent application wrapper).
