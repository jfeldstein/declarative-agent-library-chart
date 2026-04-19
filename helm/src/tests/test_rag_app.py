"""Tests for the managed RAG HTTP service."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent.rag.app import create_app
from agent.rag.store import RAGStore, reset_store_for_tests


@pytest.fixture
def client() -> TestClient:
    reset_store_for_tests()
    store = RAGStore()
    return TestClient(create_app(store=store))


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_embed_and_query(client: TestClient) -> None:
    emb = client.post(
        "/v1/embed",
        json={
            "scope": "demo",
            "items": [
                {
                    "text": "The project codename is banana stand.",
                    "metadata": {"src": "doc1"},
                }
            ],
        },
    )
    assert emb.status_code == 200
    body = emb.json()
    assert len(body["chunk_ids"]) == 1

    q = client.post(
        "/v1/query",
        json={"scope": "demo", "query": "What is the codename?", "top_k": 3},
    )
    assert q.status_code == 200
    hits = q.json()["hits"]
    assert hits
    assert "banana" in hits[0]["text"].lower()


def test_embed_requires_payload(client: TestClient) -> None:
    r = client.post(
        "/v1/embed",
        json={"scope": "x", "items": [], "entities": [], "relationships": []},
    )
    assert r.status_code == 400


def test_relate_and_query_expansion(client: TestClient) -> None:
    scope = "graph"
    client.post(
        "/v1/embed",
        json={
            "scope": scope,
            "entities": [
                {"id": "e1", "entity_type": "issue"},
                {"id": "e2", "entity_type": "epic"},
            ],
            "relationships": [
                {"source": "e1", "target": "e2", "relationship_type": "belongs_to"}
            ],
            "items": [
                {
                    "text": "Issue 42 fixes login.",
                    "metadata": {},
                    "entity_id": "e1",
                },
            ],
        },
    )
    q = client.post(
        "/v1/query",
        json={
            "scope": scope,
            "query": "login fix",
            "top_k": 2,
            "expand_relationships": True,
            "max_hops": 1,
        },
    )
    assert q.status_code == 200
    data = q.json()
    rel = data["related"]
    assert rel
    assert any(
        r["entity_id"] == "e1"
        and r["neighbor_id"] == "e2"
        and r["relationship_type"] == "belongs_to"
        for r in rel
    )


def test_relate_endpoint(client: TestClient) -> None:
    client.post(
        "/v1/embed",
        json={
            "scope": "g2",
            "entities": [{"id": "a"}, {"id": "b"}],
            "items": [{"text": "hello world", "entity_id": "a"}],
        },
    )
    r = client.post(
        "/v1/relate",
        json={
            "scope": "g2",
            "relationships": [
                {"source": "a", "target": "b", "relationship_type": "links"}
            ],
        },
    )
    assert r.status_code == 200
    assert r.json()["relationships_recorded"] == 1
