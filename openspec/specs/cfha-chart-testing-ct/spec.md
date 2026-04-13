## ADDED Requirements

### Requirement: [CFHA-REQ-CHART-CT-001] Chart-testing discovers and lints CFHA Helm charts

The system SHALL run [Helm chart-testing](https://github.com/helm/chart-testing) (`ct`) against the Declarative Agent Library chart and all example application charts under `this repository`, using a committed configuration file (e.g. `ct.yaml`) that declares `chart-dirs` and any exclusions consistent with the repository layout.

#### Scenario: Lint passes on a clean tree

- **WHEN** a maintainer runs the documented `ct lint` command from `this repository` after `helm dependency build` has been run for charts that declare dependencies
- **THEN** `ct` completes successfully with exit code zero and reports no lint failures for the configured charts

#### Scenario: Invalid chart metadata fails lint

- **WHEN** a chart violates rules enforced by `ct lint` (for example invalid `Chart.yaml` or yamllint failures in chart files)
- **THEN** `ct lint` fails with a non-zero exit code and output that identifies the chart and the failing rule

### Requirement: [CFHA-REQ-CHART-CT-002] CI documents how to obtain chart-testing

The system SHALL document in implementation (e.g. `.github/workflows/ci.yml` comments or project README) at least one supported way to install or run `ct` (official binary, package manager, or `quay.io/helmpack/chart-testing` image) so CI and developers can reproduce the same lint behavior.

#### Scenario: Missing ct binary

- **WHEN** a maintainer runs the documented local `ct lint` steps on a machine without `ct` in `PATH`
- **THEN** the failure is obvious (for example `command not found`) and README or workflow documentation SHALL point to a supported install path consistent with the GitHub Actions Helm job
