"""Prometheus metrics on the RAG HTTP service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from hosted_agents.rag.app import create_app
from hosted_agents.rag.store import RAGStore, reset_store_for_tests


def _metrics(client: TestClient) -> str:
    r = client.get("/metrics")
    assert r.status_code == 200
    return r.text


def test_rag_metrics_endpoint_lists_series() -> None:
    reset_store_for_tests()
    client = TestClient(create_app(store=RAGStore()))
    text = _metrics(client)
    assert "agent_runtime_rag_embed_requests_total" in text
    assert "agent_runtime_rag_query_requests_total" in text


def test_embed_success_updates_counters() -> None:
    reset_store_for_tests()
    client = TestClient(create_app(store=RAGStore()))
    before = _metrics(client)
    r = client.post(
        "/v1/embed",
        json={"scope": "m", "items": [{"text": "hello metrics world", "metadata": {}}]},
    )
    assert r.status_code == 200
    after = _metrics(client)
    assert after.count("agent_runtime_rag_embed_requests_total") >= before.count(
        "agent_runtime_rag_embed_requests_total",
    )
    assert 'agent_runtime_rag_embed_requests_total{result="success"}' in after


def test_query_client_error_updates_counter() -> None:
    reset_store_for_tests()
    client = TestClient(create_app(store=RAGStore()))
    r = client.post("/v1/query", json={"scope": "m", "query": ""})
    assert r.status_code == 422
    text = _metrics(client)
    assert 'agent_runtime_rag_query_requests_total{result="client_error"}' in text
