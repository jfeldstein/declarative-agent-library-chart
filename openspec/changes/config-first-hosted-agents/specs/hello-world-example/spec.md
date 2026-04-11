## ADDED Requirements

### Requirement: Hello-world example chart

The repository SHALL include `examples/hello-world/Chart.yaml` of **`type: application`** that declares the **Helm library** chart (`hosted-agent`) as a **Helm dependency** with `repository: file://../../helm/chart` (or equivalent) and `values.yaml` containing at minimum:

```yaml
system-prompt: |
  Respond, "Hello :wave:"
```

(or semantically equivalent structure if nested under a values key for the subchart, provided the documented `curl` check still applies).

#### Scenario: Example declares dependency

- **WHEN** a maintainer opens `examples/hello-world/Chart.yaml`
- **THEN** it SHALL reference the shared library chart such that `helm dependency update` can resolve it for local installs

### Requirement: Minimal values surface

The hello-world example SHALL be deployable with only the `system-prompt` (and any mandatory chart defaults such as image repository/tag if not defaulted in the parent or library chart) without Slack, Jira, or Drive credentials.

#### Scenario: No third-party credentials for hello-world

- **WHEN** an operator deploys hello-world per documented steps
- **THEN** deployment SHALL succeed on a fresh kind cluster without creating a Slack App or external OAuth configuration

### Requirement: Local acceptance with kind and curl

Documentation and/or automation SHALL define success as:

1. Create a **kind** cluster.
2. Deploy hello-world using **Helm**, and/or **Skaffold**, and/or **DevSpace** (all paths that are claimed supported MUST be documented).
3. Execute:

   `curl http://127.0.0.1:8088/api/v1/trigger`

   (or the documented equivalent if port mapping differs, but **8088** is the named target).

4. The response body SHALL include content consistent with the configured `system-prompt` behavior (e.g. a greeting containing **Hello** and the wave emoji **:wave:** or **👋** as rendered in the actual response format).

#### Scenario: Operator verifies greeting

- **WHEN** the operator runs the documented deploy and `curl` command against `127.0.0.1:8088`
- **THEN** they SHALL receive a successful HTTP response whose body reflects the hello-world agent output as specified above
