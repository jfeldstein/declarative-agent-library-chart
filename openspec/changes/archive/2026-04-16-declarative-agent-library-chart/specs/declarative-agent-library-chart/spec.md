## ADDED Requirements

### Requirement: Library chart identifier and description

The shared Helm library chart SHALL declare `name: declarative-agent-library` in `Chart.yaml` and SHALL include a `description` that identifies the chart as the **Declarative Agent Library Chart** (or equivalent wording that includes both “declarative” and “library” in plain language for operators).

#### Scenario: Chart metadata identifies the library

- **WHEN** a maintainer opens the library chart’s `Chart.yaml`
- **THEN** the `name` field SHALL be `declarative-agent-library` and the `description` SHALL convey that this chart is the declarative agent **library** consumed by parent application charts

### Requirement: Dependents use the new chart name

Every in-repository **application** chart that depends on the library SHALL list the dependency with `name: declarative-agent-library` matching the library chart `name`, and SHALL use Helm values nested under the key `declarative-agent-library` (or the documented alias if the design explicitly adds one — default is no alias).

#### Scenario: Example declares the renamed dependency

- **WHEN** a maintainer opens `examples/hello-world/Chart.yaml`
- **THEN** the dependency entry SHALL use `name: declarative-agent-library` and a `repository` path that resolves to the shared library chart directory

#### Scenario: Example values target the subchart key

- **WHEN** an operator configures hello-world via `values.yaml` for subchart settings
- **THEN** documented structure SHALL nest settings under `declarative-agent-library:` (not `hosted-agent:`)

### Requirement: Documentation uses declarative library naming

Project documentation that describes the shared Helm library (README, chart test docs, and inline comments meant for operators) SHALL refer to the **Declarative Agent Library Chart** or **declarative-agent-library** where a technical identifier is needed, and SHALL NOT present `hosted-agent` as the current chart name after this change ships.

#### Scenario: Reader finds consistent naming

- **WHEN** a contributor follows the primary README path for the Helm library
- **THEN** they SHALL see the declarative library naming aligned with `Chart.yaml` and SHALL not be instructed to use `hosted-agent` as the dependency or values key
