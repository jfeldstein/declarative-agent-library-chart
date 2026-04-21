# Local CI (parity with GitHub Actions)

Canonical automation lives in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). From a clone of [github.com/jfeldstein/declarative-agent-library-chart](https://github.com/jfeldstein/declarative-agent-library-chart):

## Git hooks ([Lefthook](https://github.com/evilmartians/lefthook))

Optional local gates (not run in CI). Install the `lefthook` binary (e.g. `brew install lefthook`), sync Python deps (`uv sync --all-groups --project helm/src`), then from repo root:

```bash
lefthook install
```

- **pre-commit:** `ruff format` on staged `helm/src` `*.py` (Lefthook `stage_fixed` re-stages), then `ruff check` on those paths — sequential.
- **pre-push:** `ruff format --check` + full `ruff check` on `agent`/`tests`, then `complexipy` + `pytest` (coverage per `helm/src/pyproject.toml`), RAG smoke, spec traceability, ADR numbering — mirrors most of the Python + docs jobs; **Helm** (`helm unittest`, `ct lint`) is not in hooks (run manually or rely on Actions).

Per-repo overrides: `.lefthook-local.yml` (gitignored).

## Python (uv)

From repo root:

```bash
uv sync --all-groups --project helm/src
cd helm/src
uv run ruff format --check agent tests
uv run ruff check agent tests
uv run vulture agent
uv run complexipy
uv run pytest tests/ -v --tb=short --cov-report=term-missing
uv run python tests/integration/smoke_rag.py
```

## Helm

Install [Helm](https://helm.sh/) **3.20.2+**, [chart-testing](https://github.com/helm/chart-testing) (`ct`), and the [helm-unittest](https://github.com/helm-unittest/helm-unittest) plugin (**v1.0.3** matches CI). Then from repo root:

```bash
set -euo pipefail
for chart_dir in examples/*/; do
  chart=$(basename "$chart_dir")
  suite="${chart//-/_}_test.yaml"
  (cd "examples/$chart" && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/${suite}" .)
done
ct lint --config ct.yaml --all
```

## ADR numbering

Same as the `docs` job in CI:

```bash
./scripts/check_adr_numbers.sh
```

## Spec traceability

Same as the `traceability` job in CI:

```bash
python3 scripts/check_spec_traceability.py
```
