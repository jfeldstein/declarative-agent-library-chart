# ADR 0012: CI parity as architectural / merge gate

## Status

Accepted

## Context

Pull-request automation in `.github/workflows/ci.yml` is the authoritative definition of what must pass before merge. Drift between “what runs in GitHub Actions” and “what people (or agents) run locally” causes avoidable rework, false confidence, and noisy CI.

The repo documents equivalent local commands in [`docs/local-ci.md`](../local-ci.md) and splits CI into **Python**, **Helm**, **Docs (ADR numbering)**, and **Spec traceability** jobs. Heavier checks (for example kind + Prometheus) exist on a separate schedule and are not part of the default PR gate.

## Decision

**Pull-request CI is canonical** for merge readiness. Contributors and automation agents **SHOULD** run the same stages locally as in `ci.yml`, using the commands in [`docs/local-ci.md`](../local-ci.md) (or exact equivalents) so results match the merge gate.

The merge gate **SHALL** include, in line with `ci.yml`:

- **`./scripts/check_adr_numbers.sh`** — unique ADR numbering (`docs` job).
- **`python3 scripts/check_spec_traceability.py`** — promoted OpenSpec specs ↔ traceability matrix (`traceability` job).
- **Python under `helm/src/` via `uv`**: `uv sync --all-groups`, **`ruff check hosted_agents tests`** (includes McCabe **`C901`** via `helm/src/pyproject.toml`), **`complexipy`** (cognitive complexity; same `pyproject.toml` config), **`pytest`** on `tests/` with coverage (including the **85%** floor enforced in CI; CI also uploads `coverage.xml`), and the **in-process RAG smoke** (`uv run python tests/integration/smoke_rag.py`).
- **Helm**: for each `examples/*` chart, `helm dependency build --skip-refresh` and **`helm unittest`** using the suite under `helm/tests/`; then **`ct lint --config ct.yaml --all`** (pinned tool versions as documented for parity with CI).

**Optional / non-default PR gate:** scheduled or manually triggered integration (for example kind + Prometheus via `RUN_KIND_O11Y_INTEGRATION=1` and the `@pytest.mark.integration` convention in `pyproject.toml`) **SHALL NOT** be required for every PR unless a future ADR or policy changes that; it remains documented for deeper verification tiers.

## Consequences

- Contributors **SHOULD** run full local parity (ADR check, traceability check, Python, Helm) before pushing or opening a PR, reducing surprise CI failures.
- Agents and other automated contributors **SHOULD** use the same sequence so their changes are merge-ready without relying on remote CI alone.
- When `ci.yml` or [`docs/local-ci.md`](../local-ci.md) changes, this ADR’s checklist should be reviewed so the documented merge gate stays aligned.
