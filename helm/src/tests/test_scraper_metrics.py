"""Scraper metrics registry, address parsing, and run counter."""

from __future__ import annotations

import socket
import urllib.request

import pytest
from prometheus_client import generate_latest

from hosted_agents.scrapers.metrics import (
    SCRAPER_REGISTRY,
    observe_scraper_run,
    parse_scraper_metrics_addr,
    start_scraper_metrics_http,
)


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
def test_parse_scraper_metrics_addr(
    addr: str, expected_host: str, expected_port: int
) -> None:
    assert parse_scraper_metrics_addr(addr) == (expected_host, expected_port)


def test_parse_scraper_metrics_addr_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_scraper_metrics_addr("")
    with pytest.raises(ValueError, match="host:port"):
        parse_scraper_metrics_addr("no-port-here")
    with pytest.raises(ValueError, match="IPv6"):
        parse_scraper_metrics_addr("[::]")


def test_observe_scraper_run_records_metric() -> None:
    observe_scraper_run("unit-test", True, 0.01)
    text = generate_latest(SCRAPER_REGISTRY).decode()
    assert (
        'agent_runtime_scraper_runs_total{integration="unit-test",result="success"}' in text
    )


def test_scraper_metrics_http_server_exposes_registry() -> None:
    """Covers ``start_scraper_metrics_http`` / handler path on :data:`SCRAPER_REGISTRY`."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    _, port = sock.getsockname()
    sock.close()
    addr = f"127.0.0.1:{port}"
    observe_scraper_run("metrics-http", True, 0.001)
    httpd = start_scraper_metrics_http(addr)
    try:
        body = urllib.request.urlopen(f"http://{addr}/metrics", timeout=3).read()
        assert b"agent_runtime_scraper_runs_total" in body
    finally:
        httpd.shutdown()
