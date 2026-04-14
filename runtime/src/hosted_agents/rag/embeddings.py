"""Embeddings for the RAG service.

When ``BASETEN_API_KEY`` is set, uses the BaseTen Qwen3 0.6B embedding model
(OpenAI-compatible endpoint, called via httpx).  Otherwise falls back to
deterministic pseudo-embeddings so unit tests pass without external credentials.
"""

from __future__ import annotations

import hashlib
import math
import os
import random

import httpx

_DIM = 1024  # Qwen3 0.6B output dimension; also used for the pseudo-embedding fallback

_BASETEN_EMBED_URL = (
    "https://model-q04l65m3.api.baseten.co/environments/production/sync/v1/embeddings"
)
_BASETEN_MODEL_ID = "q04l65m3"

# Per-request timeout: BaseTen L4 cold starts are typically <60s.
# Using a generous 90s here so a freshly-scaled-up model still gets through.
_REQUEST_TIMEOUT = 90.0


def _pseudo_embed(text: str, *, dim: int) -> list[float]:
    """Return a unit L2-normalized vector derived from ``text`` (reproducible)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big")
    rng = random.Random(seed)
    vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _baseten_embed(text: str, api_key: str) -> list[float]:
    """Call BaseTen Qwen3 0.6B via the OpenAI-compatible embeddings REST endpoint.

    Uses ``httpx`` directly so no extra dependency is required beyond what the
    project already pins.
    """
    resp = httpx.post(
        _BASETEN_EMBED_URL,
        headers={"Authorization": f"Api-Key {api_key}"},
        json={"model": _BASETEN_MODEL_ID, "input": text},
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def embed_text(text: str, *, dim: int = _DIM) -> list[float]:
    """Return a unit L2-normalized embedding vector for ``text``.

    Uses the BaseTen Qwen3 0.6B model when ``BASETEN_API_KEY`` is set in the
    environment (``dim`` is ignored in that case — the model always returns
    1024-dimensional vectors).  Falls back to deterministic pseudo-embeddings
    when the key is absent so that tests can run without external credentials.
    """
    api_key = os.environ.get("BASETEN_API_KEY")
    if api_key:
        return _baseten_embed(text, api_key)
    return _pseudo_embed(text, dim=dim)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Dot product of two unit vectors."""
    return sum(x * y for x, y in zip(a, b, strict=True))
