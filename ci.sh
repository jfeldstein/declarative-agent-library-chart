#!/usr/bin/env bash
# Traceability: [CFHA-REQ-HELM-UNITTEST-003] [CFHA-REQ-CHART-CT-001] [CFHA-REQ-CHART-CT-002] [CFHA-VER-004]
set -euo pipefail

echo "=== CI: declarative-agent-library-chart ==="

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ ! -f "runtime/pyproject.toml" ]; then
  echo "error: run from this repository (missing runtime/pyproject.toml)" >&2
  exit 1
fi

if ! command -v uv &>/dev/null; then
  echo "error: uv is not installed (https://docs.astral.sh/uv/)" >&2
  exit 1
fi

uv sync --all-groups --project runtime

echo "==> ruff check"
(
  cd runtime
  uv run ruff check src tests
)

echo "==> pytest with coverage (fail under 85%)"
(
  cd runtime
  uv run pytest tests/ -v --tb=short
)

echo "==> RAG smoke (in-process)"
(
  cd runtime
  uv run python scripts/smoke_rag.py
)

# Helm charts: chart-testing (ct) + helm-unittest — see openspec change helm-ct-unittest
# Install:
#   - Helm 3: https://helm.sh/docs/intro/install/
#   - ct (chart-testing): https://github.com/helm/chart-testing — e.g. brew install chart-testing
#     or: docker run --rm -v "$(pwd):/work" -w /work quay.io/helmpack/chart-testing:v3.14.0 ct lint --config ct.yaml --all
#   - helm-unittest: https://github.com/helm-unittest/helm-unittest — e.g.
#       helm plugin install https://github.com/helm-unittest/helm-unittest.git
#     or Docker: https://github.com/helm-unittest/helm-unittest#docker-usage
if command -v helm &>/dev/null; then
  if ! command -v ct &>/dev/null; then
    echo "error: chart-testing (ct) not found. Install: brew install chart-testing" >&2
    echo "  See: https://github.com/helm/chart-testing/releases (pin e.g. v3.14.0 for Docker CI)" >&2
    exit 1
  fi
  if ! helm plugin list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx unittest; then
    echo "error: helm-unittest plugin not installed. Run:" >&2
    echo "  helm plugin install https://github.com/helm-unittest/helm-unittest.git" >&2
    echo "  Releases: https://github.com/helm-unittest/helm-unittest/releases" >&2
    exit 1
  fi

  echo "==> helm dependency build + unittest (examples)"
  for chart_dir in examples/*/; do
    chart=$(basename "$chart_dir")
    (
      cd "examples/$chart"
      helm dependency build --skip-refresh
      helm unittest .
    )
  done

  echo "==> ct lint (Helm chart-testing)"
  ct lint --config ct.yaml --all
else
  echo "==> helm not installed; skipping chart lint/unittest (install Helm + ct + helm-unittest to run charts CI)"
fi

echo "==> spec traceability (openspec/specs + docs/spec-test-traceability.md)"
python3 scripts/check_spec_traceability.py

echo "✓ CI passed"
