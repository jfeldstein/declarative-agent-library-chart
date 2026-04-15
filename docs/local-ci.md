# Local CI (parity with GitHub Actions)

Canonical automation lives in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). From a clone of [github.com/jfeldstein/declarative-agent-library-chart](https://github.com/jfeldstein/declarative-agent-library-chart):

## Python (uv)

From repo root:

```bash
uv sync --all-groups --project helm/src
cd helm/src
uv run ruff check hosted_agents tests
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
