"""kind + Prometheus + with-observability: agent and RAG metrics visible in PromQL.

Deploys the example chart (agent + RAG via an enabled scraper job), Prometheus with two static scrape jobs,
asserts trigger counters and ``agent_runtime_rag_*`` after embed/query traffic.

Requires: docker, kind, kubectl, helm, curl; network to pull Helm chart + images.

Enable with::

    cd runtime
    RUN_KIND_O11Y_INTEGRATION=1 uv run pytest tests/integration/test_kind_o11y_prometheus.py -v --no-cov

Use ``--no-cov`` when running only this test so the 85% coverage gate still makes sense for the rest of the suite.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _cfha_root() -> Path:
    # .../runtime/tests/integration/<this file> -> project root
    return Path(__file__).resolve().parents[3]


@pytest.mark.skipif(
    os.environ.get("RUN_KIND_O11Y_INTEGRATION") != "1",
    reason="Set RUN_KIND_O11Y_INTEGRATION=1 to run kind + Prometheus integration",
)
def test_kind_o11y_prometheus_integration() -> None:
    root = _cfha_root()
    script = Path(__file__).resolve().parent.parent / "scripts" / "integration_kind_o11y_prometheus.sh"
    assert script.is_file(), f"missing {script}"

    env = os.environ.copy()
    env.setdefault("TRIGGER_COUNT", "5")

    proc = subprocess.run(
        [str(script)],
        cwd=str(root),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
    assert proc.returncode == 0, "integration_kind_o11y_prometheus.sh failed"
