"""Stub scraper: no external integration; records a successful run and exposes /metrics."""

from __future__ import annotations

import os
import sys
import time

from hosted_agents.scrapers.metrics import observe_scraper_run, start_scraper_metrics_http


def run() -> None:
    t0 = time.perf_counter()
    integration = (
        os.environ.get("SCRAPER_INTEGRATION", "").strip()
        or os.environ.get("SCRAPER_NAME", "stub").strip()
        or "stub"
    )
    metrics_addr = os.environ.get("SCRAPER_METRICS_ADDR", "").strip()
    httpd = start_scraper_metrics_http(metrics_addr) if metrics_addr else None

    run_ok = False
    try:
        print("stub scraper", os.environ.get("SCRAPER_NAME", ""), file=sys.stdout)  # noqa: T201
        run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        if httpd is not None:
            grace = float(os.environ.get("SCRAPER_METRICS_GRACE_SECONDS", "15"))
            if grace > 0:
                time.sleep(grace)
            httpd.shutdown()


if __name__ == "__main__":
    run()
