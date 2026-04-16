## Why

Python in `helm/src` is growing; without automated complexity limits, deeply nested or branch-heavy code can merge unnoticed and raise maintenance cost. Enforcing **cyclomatic complexity via Ruff** (structural branch count) together with **[complexipy](https://github.com/rohaquinlop/complexipy)** (cognitive complexity, human-readability) in CI catches regressions early and complements each other (Ruff’s `PLR0912` vs. complexipy’s cognitive model).

## What Changes

- Add **Ruff** enforcement of **McCabe cyclomatic complexity** (**`C901`**, [`complex-structure`](https://docs.astral.sh/ruff/rules/complex-structure/)) via **`[tool.ruff.lint]`** `extend-select` and **`[tool.ruff.lint.mccabe]`** `max-complexity`; ensure the **Python CI job** runs `ruff check` with those settings committed in `helm/src/pyproject.toml`.
- Add **`complexipy`** as a dev dependency (or CI-only install) and a **CI step** that runs it against the same Python package paths as Ruff (e.g. `hosted_agents`, `tests` as appropriate), with thresholds and excludes aligned in `[tool.complexipy]` in `pyproject.toml` where practical.
- Document **threshold strategy** (initial values, snapshot/baseline optional follow-up) in design; avoid **BREAKING** churn for contributors by tuning limits or using complexipy snapshots if the baseline is noisy.

## Capabilities

### New Capabilities

- `dalc-python-complexity-ci`: Normative requirements for **Ruff cyclomatic complexity** and **complexipy cognitive complexity** checks in CI for the chart’s Python sources under `helm/src`, including configuration location, scope (paths), and failure semantics (non-zero exit on violations).

### Modified Capabilities

- (none) — no existing promoted spec’s **SHALL** behavior is redefined; this introduces a new capability spec for Python CI quality gates.

## Impact

- **CI**: `.github/workflows/ci.yml` (Python job): additional step(s) and/or tightened Ruff invocation.
- **Dependencies**: `helm/src/pyproject.toml` — `complexipy` (likely dev dependency group); Ruff configuration extended.
- **Developers**: Local `uv run ruff check` and `complexipy` must pass before merge; may require refactors or inline ignores where justified.
