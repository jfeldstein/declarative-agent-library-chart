## ADDED Requirements

### Requirement: [CFHA-REQ-EXAMPLE-VALUES-FILES-001] Distinct values files for distinct demonstrated setups

For each example application chart under **`examples/`** that is intended to demonstrate **more than one** materially distinct user-facing configuration (for example different optional components, toggles, or integration modes), the repository SHALL provide **one committed values file per demonstrated setup** and SHALL list and describe **each** file in **`examples/<name>/README.md`** (purpose, distinguishing keys, and when a user should choose that setup).

#### Scenario: Multiple setups are discoverable from the example README

- **WHEN** an example’s documentation describes more than one supported configuration story for that chart
- **THEN** each such story SHALL correspond to a dedicated `values*.yaml` file in that example directory and the README SHALL name the file and summarize its intent

### Requirement: [CFHA-REQ-EXAMPLE-VALUES-FILES-002] Default install path stays documented

Each example chart SHALL identify a **default** values entrypoint (conventionally **`values.yaml`**) in its README as the primary **getting started** path, and SHALL document how to use **additional** values files with `helm upgrade --install` (for example **`-f`** flags) when a non-default setup is chosen.

#### Scenario: Quick start references the default file

- **WHEN** a reader follows the example README’s primary quick-start instructions
- **THEN** those instructions SHALL use the documented default values file unless the README explicitly standardizes a different primary filename
