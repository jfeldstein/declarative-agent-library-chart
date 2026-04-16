"""RAG HTTP integration tests (two modes).

**BaseTen semantic retrieval** — exercises real Qwen3 0.6B embeddings when
``BASETEN_API_KEY`` is set. Cold 503 responses skip with a clear message.

**Local uvicorn server** — end-to-end HTTP against a real server process;
relationship / entity ingest and query assertions. Enable with::

    cd helm/src
    RUN_RAG_INTEGRATION=1 uv run pytest tests/integration/test_rag_http.py -v --no-cov

Use ``--no-cov`` when running only the local-server tests so the 85% coverage
gate still makes sense for the rest of the suite.

Pseudo-embedding unit coverage lives in ``tests/test_rag_app.py``.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Generator

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from hosted_agents.rag.app import create_app
from hosted_agents.rag.store import RAGStore, reset_store_for_tests

_HAS_BASETEN = bool(os.environ.get("BASETEN_API_KEY"))


def _skip_if_cold_start(exc: Exception) -> None:
    """Re-raise as pytest.skip when the BaseTen endpoint is still warming up (503)."""
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 503:
        pytest.skip(
            "BaseTen model returned 503 — endpoint is still cold-starting, retry later"
        )


@pytest.fixture
def client() -> TestClient:
    reset_store_for_tests()
    store = RAGStore()
    return TestClient(create_app(store=store))


@pytest.mark.skipif(
    not _HAS_BASETEN,
    reason="BASETEN_API_KEY not set — skipping BaseTen embedding integration tests",
)
class TestBasetenSemanticRetrieval:
    """Verify that real embeddings produce semantically meaningful rankings."""

    def test_semantically_similar_query_returns_relevant_hit(
        self, client: TestClient
    ) -> None:
        """Top result for a Paris/France query should mention Paris or France."""
        try:
            emb = client.post(
                "/v1/embed",
                json={
                    "scope": "geo_test",
                    "items": [
                        {
                            "text": "The capital of France is Paris, a city known for the Eiffel Tower.",
                            "metadata": {"topic": "geography"},
                        },
                        {
                            "text": "Python is a programming language favored for machine learning.",
                            "metadata": {"topic": "programming"},
                        },
                        {
                            "text": "Kubernetes orchestrates containerized workloads across a cluster.",
                            "metadata": {"topic": "infra"},
                        },
                    ],
                },
            )
        except httpx.HTTPStatusError as exc:
            _skip_if_cold_start(exc)
            raise

        assert emb.status_code == 200
        assert len(emb.json()["chunk_ids"]) == 3

        q = client.post(
            "/v1/query",
            json={
                "scope": "geo_test",
                "query": "What is the capital city of France?",
                "top_k": 3,
            },
        )
        assert q.status_code == 200
        hits = q.json()["hits"]
        assert hits
        top_text = hits[0]["text"].lower()
        assert "paris" in top_text or "france" in top_text, (
            f"Expected Paris/France in top hit, got: {hits[0]['text']!r}"
        )

    def test_unrelated_document_ranks_lower(self, client: TestClient) -> None:
        """ML-related query should rank the ML document above the infra document."""
        try:
            emb = client.post(
                "/v1/embed",
                json={
                    "scope": "rank_test",
                    "items": [
                        {
                            "text": "Kubernetes orchestrates containerized workloads across a cluster.",
                            "metadata": {"topic": "infra"},
                        },
                        {
                            "text": "Machine learning models require large datasets for training neural networks.",
                            "metadata": {"topic": "ml"},
                        },
                    ],
                },
            )
        except httpx.HTTPStatusError as exc:
            _skip_if_cold_start(exc)
            raise

        assert emb.status_code == 200

        q = client.post(
            "/v1/query",
            json={
                "scope": "rank_test",
                "query": "training neural networks with data",
                "top_k": 2,
            },
        )
        assert q.status_code == 200
        hits = q.json()["hits"]
        assert len(hits) == 2
        top_text = hits[0]["text"].lower()
        assert (
            "machine learning" in top_text
            or "neural" in top_text
            or "dataset" in top_text
        ), f"Expected ML document at top, got: {hits[0]['text']!r}"

    def test_semantic_not_lexical_match(self, client: TestClient) -> None:
        """Query with synonymous phrasing (no shared tokens) should still find the right doc."""
        try:
            emb = client.post(
                "/v1/embed",
                json={
                    "scope": "synonym_test",
                    "items": [
                        {
                            "text": "The physician examined the patient and prescribed medication.",
                            "metadata": {"domain": "medicine"},
                        },
                        {
                            "text": "The stock market closed higher after the Federal Reserve announcement.",
                            "metadata": {"domain": "finance"},
                        },
                    ],
                },
            )
        except httpx.HTTPStatusError as exc:
            _skip_if_cold_start(exc)
            raise

        assert emb.status_code == 200

        # Query uses "doctor" and "treatment" — no exact token overlap with "physician"/"medication"
        q = client.post(
            "/v1/query",
            json={
                "scope": "synonym_test",
                "query": "doctor gave treatment to sick person",
                "top_k": 2,
            },
        )
        assert q.status_code == 200
        hits = q.json()["hits"]
        assert hits
        top_text = hits[0]["text"].lower()
        assert (
            "physician" in top_text or "patient" in top_text or "medication" in top_text
        ), f"Expected medical document at top, got: {hits[0]['text']!r}"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def rag_base_url() -> Generator[str, None, None]:
    """Start a real uvicorn RAG server and yield its base URL."""
    reset_store_for_tests()
    store = RAGStore()
    app = create_app(store=store)

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server.started:
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("RAG server did not start within 5 seconds")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=3.0)


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("RUN_RAG_INTEGRATION") != "1",
    reason="Set RUN_RAG_INTEGRATION=1 to run the RAG HTTP integration test",
)
def test_rag_health_over_http(rag_base_url: str) -> None:
    r = httpx.get(f"{rag_base_url}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("RUN_RAG_INTEGRATION") != "1",
    reason="Set RUN_RAG_INTEGRATION=1 to run the RAG HTTP integration test",
)
def test_rag_ingest_with_relationship_attrs_and_query(rag_base_url: str) -> None:
    """POST documents (including relationship-attributed) and assert query returns them."""
    scope = "integration"

    # Ingest: two entity-tagged chunks + one depends_on relationship
    ingest = httpx.post(
        f"{rag_base_url}/v1/embed",
        json={
            "scope": scope,
            "items": [
                {
                    "text": "Service alpha handles authentication.",
                    "metadata": {"src": "arch-doc"},
                    "entity_id": "svc_alpha",
                },
                {
                    "text": "Service beta depends on service alpha for token validation.",
                    "metadata": {"src": "arch-doc"},
                    "entity_id": "svc_beta",
                },
            ],
            "entities": [
                {"id": "svc_alpha", "entity_type": "service"},
                {"id": "svc_beta", "entity_type": "service"},
            ],
            "relationships": [
                {
                    "source": "svc_beta",
                    "target": "svc_alpha",
                    "relationship_type": "depends_on",
                }
            ],
        },
    )
    assert ingest.status_code == 200
    body = ingest.json()
    assert len(body["chunk_ids"]) == 2
    assert body["entities_upserted"] == 2
    assert body["relationships_recorded"] == 1

    # Plain query: alpha doc must appear (most relevant to "authentication service")
    q = httpx.post(
        f"{rag_base_url}/v1/query",
        json={"scope": scope, "query": "authentication service", "top_k": 5},
    )
    assert q.status_code == 200
    hits = q.json()["hits"]
    assert hits, "expected at least one hit"
    assert any("alpha" in h["text"].lower() for h in hits), (
        f"expected svc_alpha doc in hits; got: {[h['text'] for h in hits]}"
    )

    # Relationship-expansion query: beta doc + depends_on edge must be returned
    qr = httpx.post(
        f"{rag_base_url}/v1/query",
        json={
            "scope": scope,
            "query": "token validation dependency",
            "top_k": 5,
            "expand_relationships": True,
            "max_hops": 1,
        },
    )
    assert qr.status_code == 200
    data = qr.json()

    hits = data["hits"]
    assert hits, "expected hits for relationship-attributed query"
    assert any(h["entity_id"] == "svc_beta" for h in hits), (
        f"expected relationship-attributed doc (svc_beta) in hits; "
        f"got entity_ids={[h['entity_id'] for h in hits]}"
    )

    related = data["related"]
    assert any(
        r["entity_id"] == "svc_beta"
        and r["neighbor_id"] == "svc_alpha"
        and r["relationship_type"] == "depends_on"
        for r in related
    ), f"expected svc_beta->svc_alpha depends_on edge in related; got: {related}"
