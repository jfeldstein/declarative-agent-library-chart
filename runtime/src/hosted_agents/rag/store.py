"""In-memory chunk index + entity graph for the RAG HTTP service."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from hosted_agents.rag.embeddings import cosine_similarity, embed_text


@dataclass
class StoredChunk:
    chunk_id: str
    scope: str
    text: str
    vector: list[float]
    metadata: dict[str, Any]
    entity_id: str | None


@dataclass
class GraphEdge:
    scope: str
    source: str
    target: str
    relationship_type: str


@dataclass
class RAGStore:
    """Thread-safe in-memory store (POC)."""

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _chunks: list[StoredChunk] = field(default_factory=list)
    _entities: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    _edges: list[GraphEdge] = field(default_factory=list)

    def upsert_entities(
        self,
        scope: str,
        entities: list[dict[str, Any]],
    ) -> None:
        with self._lock:
            for ent in entities:
                eid = str(ent["id"])
                row = {"entity_type": ent.get("entity_type")}
                self._entities[(scope, eid)] = {k: v for k, v in row.items() if v is not None}

    def add_relationships(
        self,
        scope: str,
        relationships: list[dict[str, Any]],
    ) -> None:
        with self._lock:
            for rel in relationships:
                self._edges.append(
                    GraphEdge(
                        scope=scope,
                        source=str(rel["source"]),
                        target=str(rel["target"]),
                        relationship_type=str(rel["relationship_type"]),
                    )
                )

    def add_chunks(
        self,
        scope: str,
        items: list[dict[str, Any]],
    ) -> list[str]:
        ids: list[str] = []
        with self._lock:
            for item in items:
                text = str(item["text"])
                meta = dict(item.get("metadata") or {})
                entity_id = item.get("entity_id")
                eid = str(entity_id) if entity_id is not None else None
                cid = str(uuid.uuid4())
                self._chunks.append(
                    StoredChunk(
                        chunk_id=cid,
                        scope=scope,
                        text=text,
                        vector=embed_text(text),
                        metadata=meta,
                        entity_id=eid,
                    )
                )
                ids.append(cid)
        return ids

    def query(
        self,
        scope: str,
        query: str,
        *,
        top_k: int,
        expand_relationships: bool,
        relationship_types: list[str] | None,
        max_hops: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        qv = embed_text(query)
        with self._lock:
            scoped = [c for c in self._chunks if c.scope == scope]
            edges_snapshot = list(self._edges)
        scored: list[tuple[float, StoredChunk]] = []
        for ch in scoped:
            scored.append((cosine_similarity(qv, ch.vector), ch))
        scored.sort(key=lambda t: t[0], reverse=True)
        top = scored[: max(1, top_k)]

        hits: list[dict[str, Any]] = []
        for score, ch in top:
            hits.append(
                {
                    "chunk_id": ch.chunk_id,
                    "score": score,
                    "text": ch.text,
                    "metadata": ch.metadata,
                    "entity_id": ch.entity_id,
                }
            )

        related: list[dict[str, Any]] = []
        if expand_relationships and max_hops >= 1:
            seeds: set[str] = set()
            for _, ch in top:
                if ch.entity_id:
                    seeds.add(ch.entity_id)
            allowed_types = None
            if relationship_types:
                allowed_types = set(relationship_types)
            for seed in seeds:
                related.extend(
                    self._neighbors(scope, seed, allowed_types, hops=max_hops, edges=edges_snapshot),
                )
        return hits, related

    def _neighbors(
        self,
        scope: str,
        entity_id: str,
        allowed_types: set[str] | None,
        *,
        hops: int,
        edges: list[GraphEdge],
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if hops < 1:
            return out
        frontier = {entity_id}
        seen_edges: set[tuple[str, str, str]] = set()
        for _ in range(hops):
            next_frontier: set[str] = set()
            for e in edges:
                if e.scope != scope:
                    continue
                if allowed_types is not None and e.relationship_type not in allowed_types:
                    continue
                if e.source in frontier:
                    key = (e.source, e.target, e.relationship_type)
                    if key not in seen_edges:
                        seen_edges.add(key)
                        out.append(
                            {
                                "entity_id": e.source,
                                "neighbor_id": e.target,
                                "relationship_type": e.relationship_type,
                            },
                        )
                    next_frontier.add(e.target)
                if e.target in frontier:
                    key = (e.target, e.source, e.relationship_type)
                    if key not in seen_edges:
                        seen_edges.add(key)
                        out.append(
                            {
                                "entity_id": e.target,
                                "neighbor_id": e.source,
                                "relationship_type": e.relationship_type,
                            },
                        )
                    next_frontier.add(e.source)
            frontier = next_frontier
            if not frontier:
                break
        return out


_GLOBAL: RAGStore | None = None
_GLOBAL_LOCK = threading.Lock()


def get_store() -> RAGStore:
    global _GLOBAL  # noqa: PLW0603
    with _GLOBAL_LOCK:
        if _GLOBAL is None:
            _GLOBAL = RAGStore()
        return _GLOBAL


def reset_store_for_tests() -> None:
    global _GLOBAL  # noqa: PLW0603
    with _GLOBAL_LOCK:
        _GLOBAL = RAGStore()
