## ADDED Requirements

### Requirement: [DALC-REQ-HELM-UNITTEST-004] Helm-unittest covers each documented multi-setup values file

For any **`examples/<name>/`** chart whose **README documents two or more** distinct values files as separate setups (per **`cfha-example-values-files`**), the repository SHALL run helm-unittest (suites under **`helm/tests/`** following repository conventions) such that **each** documented values file is loaded in **at least one** test case or suite `values:` block, and assertions SHALL validate behavior specific to that setup (for example presence or absence of workloads, labels, or annotations described for that file).

#### Scenario: Every documented setup file has unittest coverage

- **WHEN** an example README lists multiple values files as distinct setups
- **THEN** the matching `helm/tests/` suite SHALL include coverage that targets each listed file (or equivalent inlined values) with at least one `it:` (or equivalent) whose expectations match that setup’s description

#### Scenario: Single-file examples do not require extra values files

- **WHEN** an example documents only one values story
- **THEN** this requirement SHALL NOT require additional values files beyond what **`cfha-example-values-files`** and existing **`cfha-helm-unittest`** requirements already impose
