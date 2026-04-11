"""Deterministic pseudo-embeddings for the RAG POC (no external model)."""

from __future__ import annotations

import hashlib
import math
import random

_DIM = 64


def embed_text(text: str, *, dim: int = _DIM) -> list[float]:
    """Return a unit L2-normalized vector derived from ``text`` (reproducible)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big")
    rng = random.Random(seed)
    vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Dot product of two unit vectors."""
    return sum(x * y for x, y in zip(a, b, strict=True))
