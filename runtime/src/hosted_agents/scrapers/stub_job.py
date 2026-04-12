"""Stub scraper: no external integration; records a successful run and exposes /metrics."""

from __future__ import annotations

import os
import time

from hosted_agents.scrapers.metrics import (
    maybe_start_scraper_metrics_http,
    observe_scraper_run,
    stop_scraper_metrics_http,
)


def _integration_label() -> str:
    override = os.environ.get("SCRAPER_INTEGRATION", "").strip()
    if override:
        return override
    name = os.environ.get("SCRAPER_NAME", "stub").strip()
    return name or "stub"


def run() -> None:
    t0 = time.perf_counter()
    integration = _integration_label()
    httpd = maybe_start_scraper_metrics_http()

    run_ok = False
    try:
        print("stub scraper", os.environ.get("SCRAPER_NAME", ""))  # noqa: T201
        run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        stop_scraper_metrics_http(httpd)


if __name__ == "__main__":
    run()
