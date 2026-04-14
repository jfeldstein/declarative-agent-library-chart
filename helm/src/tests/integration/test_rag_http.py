"""Integration tests for the RAG HTTP service using real BaseTen Qwen3 0.6B embeddings.

These tests run only when ``BASETEN_API_KEY`` is present in the environment.
If the BaseTen endpoint returns 503 (model cold-starting / still deploying) the
individual test is skipped with a clear message rather than failing hard.

The existing pseudo-embedding tests in ``tests/test_rag_app.py`` continue to
pass without the key.
"""

from __future__ import annotations

import os

import httpx
import pytest
from fastapi.testclient import TestClient

from hosted_agents.rag.app import create_app
from hosted_agents.rag.store import RAGStore, reset_store_for_tests

_HAS_BASETEN = bool(os.environ.get("BASETEN_API_KEY"))

pytestmark = pytest.mark.skipif(
    not _HAS_BASETEN,
    reason="BASETEN_API_KEY not set — skipping BaseTen embedding integration tests",
)


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
            "physician" in top_text
            or "patient" in top_text
            or "medication" in top_text
        ), f"Expected medical document at top, got: {hits[0]['text']!r}"
