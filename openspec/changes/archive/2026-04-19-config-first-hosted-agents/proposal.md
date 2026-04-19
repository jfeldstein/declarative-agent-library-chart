## Why

Teams want autonomous or reactive “hosted agent” experiences (Slack bots, onboarding helpers, incident scribes) without owning infra patterns, RAG pipelines, or orchestration frameworks like LangGraph. A **configuration-first** prototype in `this repository` lowers the bar: one YAML file expresses prompts, tool scopes (Slack, Jira, Drive, etc.), and centralized security posture, while a shared **Helm library chart** supplies reusable Kubernetes templates and values for the runtime, pre-rolled integrations, and room to grow. Application charts (for example `examples/hello-world`) depend on that library and are what operators install.

## What Changes

- Introduce a **project skeleton** under `this repository`: `helm/chart/` (**`type: library`** — not installable alone), `helm/src/` (runtime programs reading ConfigMap/env or pointers thereto), `helm/tests/<pkg>/` (mirrors `src` plus `chart` tests).
- Define a **draft configuration surface** (YAML) for `system-prompt`, `tools.slack` (channels, keyword searches, bot identity), `tools.jira` (projects and scoped actions), `tools.drive`, and placeholders for future tools—without requiring a working Slack App in v1.
- Ship a **minimal complete example** `examples/hello-world/` with `Chart.yaml` (**`type: application`**) depending on the library chart (`file://../../helm/chart`) and `values.yaml` containing only a `system-prompt` that yields a fixed greeting response.
- Expose a **generic HTTP trigger** from the library chart templates (e.g. `POST /api/v1/trigger`) that invokes the agent/runtime so other ingress paths (Slack webhooks, etc.) can map to the same code later.
- Document and automate **local success path**: create a kind cluster, deploy via Helm / Skaffold / DevSpace, `curl` the trigger URL and receive the configured greeting (e.g. `"Hello :wave:"`).
- Defer **Slack App creation and internet-reachable webhook proof** to a follow-up; first draft focuses on in-cluster trigger and config wiring.

## Capabilities

### New Capabilities

- `hosted-agent-template`: Shared **Helm library** chart, runtime layout (`helm/src`, `helm/tests`), generic `/api/v1/trigger` (or equivalent) that invokes the agent from config, and extension points for future webhook adapters (e.g. Slack) without mandating them in the first slice.
- `hello-world-example`: Minimal `examples/hello-world` **application** chart depending on the library chart, simplest `values.yaml`, and documented acceptance: kind + Helm/Skaffold/DevSpace deploy + `curl http://127.0.0.1:8088/api/v1/trigger` returns the agent response matching the configured prompt behavior.

### Modified Capabilities

- (none — no existing OpenSpec capability in `openspec/specs/` covers this prototype)

## Impact

- **Code / layout**: New tree at the repository root (Helm library chart under `helm/chart`, example application chart, optional small service docs in `helm/src`).
- **Tooling**: kind, Helm 3; Skaffold and/or DevSpace configs as specified for the hello-world path.
- **Dependencies**: Kubernetes cluster for local validation; no new org-wide services required for the hello-world slice.
- **Security / ops (future)**: Proposal encodes intent for centralized RBAC, CI, and scoped tool access; concrete enforcement lands in later tasks beyond the first “trigger + hello” milestone.
