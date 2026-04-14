## ADDED Requirements

### Requirement: [CFHA-REQ-DALC-PKG-001] Helm library chart name

The Declarative Agent Library **Helm** chart SHALL declare **`name: declarative-agent-library-chart`** in its **`Chart.yaml`**.

#### Scenario: Chart metadata identifies the library

- **WHEN** a maintainer runs `helm show chart` against `helm/chart`
- **THEN** the chart **name** field SHALL be `declarative-agent-library-chart`

### Requirement: [CFHA-REQ-DALC-PKG-002] Example charts nest library values under `agent`

Application charts under **`examples/`** that depend on the library SHALL declare the dependency with **`alias: agent`** so that parent **`values.yaml`** nests tunables under the top-level key **`agent`**.

#### Scenario: Hello-world uses the `agent` values key

- **WHEN** an operator reads `examples/hello-world/values.yaml`
- **THEN** library tunables SHALL appear under **`agent:`** (not under a deprecated dependency key)

### Requirement: [CFHA-REQ-DALC-PKG-003] Default image repository uses DALC name

The library chart’s default **`image.repository`** (and any documented equivalent for building/tagging the runtime image) SHALL use **`declarative-agent-library-chart`** as the repository name segment, replacing deprecated **`config-first-hosted-agents`**.

#### Scenario: Values default matches DALC repository name

- **WHEN** an operator inspects `helm/chart/values.yaml` without overrides
- **THEN** the default **`image.repository`** SHALL be `declarative-agent-library-chart`
