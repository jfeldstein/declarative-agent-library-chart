## MODIFIED Requirements

### Requirement: [CFHA-REQ-HELM-UNITTEST-003] Official helm-unittest install path

The system SHALL reference the official helm-unittest installation method (`helm plugin install https://github.com/helm-unittest/helm-unittest.git` or a pinned release/binary) in developer or CI documentation used for this project.

#### Scenario: Reproducible unittest invocation

- **WHEN** a maintainer follows the documented install steps
- **THEN** `helm unittest` runs successfully for each example application chart when invoked from that chart’s directory with the documented **`-f`** path to the corresponding suite file under **`helm/tests/`**, using the example’s **`values.yaml`** via the suite’s **`values:`** list
