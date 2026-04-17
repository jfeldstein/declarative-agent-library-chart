## 1. Project scaffold

- [x] 1.1 Create the repository root with `README.md` describing Helm library chart vs examples, kind prerequisite, and the `curl` acceptance command.
- [ ] 1.2 Add `helm/chart/Chart.yaml` and `helm/chart/templates/` with a Service + workload on port **8088**. *(**Shipped:** templates + Service + workload on **8088**. **`Chart.yaml` `type`:** cannot be Helm **`library`** without breaking manifest rendering when used as a dependency — see comment in **`helm/chart/Chart.yaml`** and **`cfha-helm-library`** task **1.2**.)*
- [x] 1.3 Add `helm/src/` with a minimal HTTP server implementing **`POST /api/v1/trigger`** that reads `system-prompt` from env/ConfigMap and returns a response body matching hello-world behavior (e.g. greeting with **Hello** and wave). *(Runtime source: `helm/src/hosted_agents/`; `helm/src/README.md` documents mapping.)*
- [x] 1.4 Add container build artifacts (e.g. `helm/Dockerfile`; build from repository root) and wire image repo/tag via Helm values with sensible defaults for local dev.

## 2. Helm wiring and example chart

- [x] 2.1 Render ConfigMap and/or env from values (at minimum `system-prompt`) so operators do not edit raw Pod YAML for routine changes.
- [x] 2.2 Add `examples/hello-world/Chart.yaml` (**`type: application`**) declaring the **library** chart as a **dependency** (`file://../../helm/chart`) and `examples/hello-world/values.yaml` with the minimal `system-prompt` block from the proposal.
- [x] 2.3 Document `helm dependency update` + `helm install` for kind; verify install succeeds without Slack/Jira/Drive secrets.

## 3. Dev loops and verification

- [x] 3.1 Add **Skaffold** and/or **DevSpace** config for hello-world (whichever is claimed in README) so iterative deploy works against kind.
- [x] 3.2 Add **`helm/tests/`** for **helm-unittest** suites (loaded per example via **`-f ../../helm/tests/...`**) plus **`helm test`** hook job under **`helm/chart/templates/tests/`**. *(Not a directory mirror of **`helm/src/`**—suites are consolidated next to **`helm/chart`**.)*
- [x] 3.3 Run end-to-end manual check: kind cluster → deploy → `curl http://127.0.0.1:8088/api/v1/trigger` → response matches expected greeting; capture exact steps in README.

## 4. Future-facing config (non-blocking for hello-world)

- [x] 4.1 Add a **draft** `values.schema.json` or documented YAML comments for `tools.slack`, `tools.jira`, `tools.drive` matching the proposal shape; runtime may ignore unused keys in v1.
- [x] 4.2 Note in README the reserved webhook extension (e.g. future `/webhooks/slack`) and that Slack App setup is explicitly out of scope for this slice.
