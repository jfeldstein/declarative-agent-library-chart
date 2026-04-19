#!/usr/bin/env python3
"""In-process smoke: embed fixture text, query, assert hit; graph expansion with two entities."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agent.rag.app import create_app
from agent.rag.store import RAGStore, reset_store_for_tests


def main() -> None:
    reset_store_for_tests()
    store = RAGStore()
    client = TestClient(create_app(store=store))

    assert client.get("/health").json() == {"status": "ok"}

    emb = client.post(
        "/v1/embed",
        json={
            "scope": "smoke",
            "entities": [
                {"id": "e1", "entity_type": "issue"},
                {"id": "e2", "entity_type": "epic"},
            ],
            "relationships": [
                {"source": "e1", "target": "e2", "relationship_type": "belongs_to"},
            ],
            "items": [
                {
                    "text": "Smoke fixture: banana stand inventory mismatch.",
                    "metadata": {"fixture": True},
                    "entity_id": "e1",
                },
            ],
        },
    )
    emb.raise_for_status()

    q = client.post(
        "/v1/query",
        json={
            "scope": "smoke",
            "query": "banana inventory",
            "top_k": 3,
            "expand_relationships": True,
            "max_hops": 1,
        },
    )
    q.raise_for_status()
    body = q.json()
    assert body["hits"], "expected at least one hit"
    assert "banana" in body["hits"][0]["text"].lower()
    rel = body["related"]
    assert rel, "expected relationship expansion"
    assert any(
        r["entity_id"] == "e1"
        and r["neighbor_id"] == "e2"
        and r["relationship_type"] == "belongs_to"
        for r in rel
    ), rel

    print("smoke_rag: ok")  # noqa: T201


if __name__ == "__main__":
    main()
