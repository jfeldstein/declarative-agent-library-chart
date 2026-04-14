## ADDED Requirements

### Requirement: Helm directory layout

The prototype SHALL place shared Helm-related artifacts under `helm/` such that:

- `helm/chart/Chart.yaml` declares the reusable chart with **`type: library`** and a non-zero chart version suitable for dependency resolution.
- `helm/chart/templates/*.yaml` contain Kubernetes resources parameterized by values (including Service, workload, ConfigMap wiring) that render when the chart is included as a dependency of an **application** chart.
- `helm/src/` documents or contains pointers to workload source consumed by those templates (consistent with the repo’s existing “implementation lives under `runtime/`” pattern if applicable).
- `helm/tests/<pkg>/` includes chart-test documentation or hooks consistent with the project README.

#### Scenario: Contributor locates Helm packaging

- **WHEN** a contributor opens `helm/`
- **THEN** they SHALL find `chart/`, `src/`, and `tests/` and README text describing their roles without referring to a top-level `template/` directory for this layout

### Requirement: Library chart is not a standalone install target

The shared chart SHALL NOT be documented or automated as a direct `helm install` target; documentation and CI SHALL treat an **application** chart (for example under `examples/`) as the install/template entry point that depends on the library.

#### Scenario: CI validates via application chart

- **WHEN** CI runs Helm lint or template for the prototype
- **THEN** it SHALL execute against an application chart that lists the library as a dependency (not against installing the library chart in isolation)

### Requirement: Generic HTTP trigger invokes the agent path

The library chart’s templates SHALL define a workload that exposes an HTTP route equivalent to **`POST /api/v1/trigger`** (path and method per chart defaults or documented values) that invokes the same agent execution path intended for future webhook adapters.

#### Scenario: Trigger request reaches workload

- **WHEN** a client sends `POST` to `/api/v1/trigger` on the service fronting the agent workload (including via documented port-forward or NodePort on host port **8088** for local dev)
- **THEN** the workload SHALL process the request and return an HTTP response with a body produced by the agent runtime (for hello-world, the body reflects the configured greeting behavior)

### Requirement: Configuration from values

The library chart SHALL accept Helm values (including at minimum `system-prompt` for the hello-world slice) and SHALL materialize them into ConfigMap and/or environment variables consumed by the runtime without requiring operators to edit raw Kubernetes YAML for routine changes.

#### Scenario: Values-only customization

- **WHEN** a parent application chart supplies `values.yaml` with `system-prompt` set (under the subchart values key matching the dependency name)
- **THEN** the rendered manifests SHALL include configuration consumed by the runtime such that behavior changes without rebuilding the container image (unless implementation explicitly documents image-bound defaults)

### Requirement: Extension point for Slack and other webhooks

The design SHALL reserve a clear extension pattern so a future **Slack webhook listener** can forward events to the same agent invocation used by `/api/v1/trigger`, without being required for the first deliverable.

#### Scenario: Documented future path

- **WHEN** a reader follows design or README notes for webhook integration
- **THEN** they SHALL see where a Slack listener would attach (for example `/webhooks/slack`) and that it is **not** required for hello-world acceptance
