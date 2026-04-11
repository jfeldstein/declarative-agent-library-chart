## ADDED Requirements

### Requirement: Repository layout for Helm library chart and tests

The prototype SHALL place shared artifacts under `helm/` such that:

- `helm/chart/Chart.yaml` names the reusable chart with `**type: library**` (consumed only as a dependency of **application** charts).
- `helm/chart/templates/*.yaml` contain Kubernetes resources parameterized by values (including Service, Deployment or equivalent workload, ConfigMap wiring).
- `helm/src/` contains or documents source for workloads deployed by those templates, reading configuration from environment variables and/or mounted ConfigMap data.
- `helm/tests/<pkg>/` mirrors packages under `helm/src/` and includes a `chart` (or chart-test) area for Helm chart tests consistent with the user’s stated structure.

#### Scenario: Contributor locates extension points

- **WHEN** a contributor opens `helm/`
- **THEN** they SHALL find `chart/`, `src/`, and `tests/` with the relationships above documented in the project README or change tasks

### Requirement: Generic HTTP trigger invokes the agent path

The library chart templates SHALL define a workload that exposes an HTTP route equivalent to `**POST /api/v1/trigger`** (path and method fixed in chart values or documented defaults) that invokes the same agent execution path used by future webhook adapters.

#### Scenario: Trigger request reaches workload

- **WHEN** a client sends `POST` to `/api/v1/trigger` on the service fronting the agent workload (including via documented port-forward or NodePort on host port **8088** for local dev)
- **THEN** the workload SHALL process the request and return an HTTP response with a body produced by the agent runtime (for hello-world, the body reflects the configured greeting behavior)

### Requirement: Configuration from values

The library chart SHALL accept Helm values (including at minimum `system-prompt` for the hello-world slice) and SHALL materialize them into ConfigMap and/or environment variables consumed by the runtime (under `helm/src` documentation or implementation path) without requiring operators to edit raw Kubernetes YAML for routine changes.

#### Scenario: Values-only customization

- **WHEN** a parent application chart supplies `values.yaml` with `system-prompt` set (under the subchart key for `hosted-agent` if nested)
- **THEN** the rendered manifests SHALL include configuration consumed by the runtime such that behavior changes without rebuilding the container image (unless implementation explicitly documents image-bound defaults)

### Requirement: Extension point for Slack and other webhooks

The design SHALL reserve a clear extension pattern (separate Deployment/container, Ingress path, or sidecar) so a future **Slack webhook listener** can forward events to the same agent invocation used by `/api/v1/trigger`, without being required for the first deliverable.

#### Scenario: Documented future path

- **WHEN** a reader follows design or README notes for webhook integration
- **THEN** they SHALL see where a Slack listener would attach (e.g. `/webhooks/slack`) and that it is **not** required for hello-world acceptance

