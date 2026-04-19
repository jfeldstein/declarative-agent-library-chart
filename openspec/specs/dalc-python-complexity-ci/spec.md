## ADDED Requirements

### Requirement: [DALC-REQ-PYTHON-COMPLEXITY-CI-001] Ruff McCabe cyclomatic complexity is configured and enforced on default Python CI

The project SHALL enable Ruff rule **`C901`** (*complex-structure* / McCabe cyclomatic complexity) for the **`helm/src`** Python package and SHALL set **`[tool.ruff.lint.mccabe]`** `max-complexity` to a committed value. The default pull-request CI workflow SHALL run **`ruff check`** (or equivalent) such that **`C901`** violations cause a **non-zero** exit code for the same scope used for linting application code (at minimum paths under **`helm/src`** that cover **`agent`** and **`tests`**).

#### Scenario: CI fails when cyclomatic complexity exceeds the configured maximum

- **WHEN** a function in the linted scope exceeds the configured McCabe **`max-complexity`**
- **THEN** **`ruff check`** SHALL report **`C901`** and the Python CI lint step SHALL fail

#### Scenario: Configuration is committed with the source tree

- **WHEN** a maintainer inspects **`helm/src/pyproject.toml`** (or the repository’s canonical Ruff config for that package)
- **THEN** they SHALL find **`C901`** selected for linting and **`mccabe.max-complexity`** set to the project’s chosen threshold

### Requirement: [DALC-REQ-PYTHON-COMPLEXITY-CI-002] complexipy cognitive complexity is configured and enforced on default Python CI

The project SHALL run **complexipy** against the **`helm/src`** Python sources on the default pull-request CI path with a committed **`max-complexity-allowed`** threshold. Configuration SHALL live in **`pyproject.toml`** under **`[tool.complexipy]`** and/or equivalent committed CLI flags, with **`paths`** (and **`exclude`** if needed) consistent with the package layout. The CI step SHALL fail with a **non-zero** exit code when complexipy reports functions above the threshold (unless a documented **snapshot/baseline** workflow is intentionally used; if snapshots are used, the committed snapshot file and behavior SHALL be documented so regressions are still detected per complexipy’s snapshot semantics).

#### Scenario: CI fails when cognitive complexity exceeds the configured maximum

- **WHEN** a function’s cognitive complexity exceeds **`max-complexity-allowed`** under the configured **`paths`**
- **THEN** the complexipy CI step SHALL fail (or, if snapshot mode is enabled, SHALL fail according to the snapshot regression rules documented for this repository)

#### Scenario: Local runs match CI commands

- **WHEN** a contributor runs the documented **`uv`** commands from **`helm/src`**
- **THEN** they SHALL be able to reproduce Ruff **`C901`** and complexipy results consistent with CI for the same revision
