"""Scraper metrics registry, address parsing, and stub job."""

from __future__ import annotations

import pytest
from prometheus_client import generate_latest

from hosted_agents.scrapers import stub_job
from hosted_agents.scrapers.metrics import SCRAPER_REGISTRY, parse_scraper_metrics_addr


@pytest.mark.parametrize(
    ("addr", "expected_host", "expected_port"),
    [
        ("0.0.0.0:9091", "0.0.0.0", 9091),
        ("127.0.0.1:8080", "127.0.0.1", 8080),
        (":9091", "0.0.0.0", 9091),
        ("[::]:9091", "::", 9091),
        ("[::1]:9092", "::1", 9092),
    ],
)
def test_parse_scraper_metrics_addr(addr: str, expected_host: str, expected_port: int) -> None:
    assert parse_scraper_metrics_addr(addr) == (expected_host, expected_port)


def test_parse_scraper_metrics_addr_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_scraper_metrics_addr("")
    with pytest.raises(ValueError, match="host:port"):
        parse_scraper_metrics_addr("no-port-here")
    with pytest.raises(ValueError, match="IPv6"):
        parse_scraper_metrics_addr("[::]")


def test_stub_job_records_run_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCRAPER_METRICS_ADDR", raising=False)
    monkeypatch.setenv("SCRAPER_NAME", "customstub")
    monkeypatch.delenv("SCRAPER_INTEGRATION", raising=False)
    stub_job.run()
    text = generate_latest(SCRAPER_REGISTRY).decode()
    assert 'agent_runtime_scraper_runs_total{integration="customstub",result="success"}' in text
