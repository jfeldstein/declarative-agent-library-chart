"""In-memory chunk index + entity graph for the RAG HTTP service."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from agent.rag.embeddings import cosine_similarity, embed_text


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
                self._entities[(scope, eid)] = {
                    k: v for k, v in row.items() if v is not None
                }

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

    def _vector_search_top(
        self, scope: str, query: str, top_k: int
    ) -> tuple[list[dict[str, Any]], list[tuple[float, StoredChunk]], list[GraphEdge]]:
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
        return hits, top, edges_snapshot

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
        hits, top, edges_snapshot = self._vector_search_top(scope, query, top_k)
        related: list[dict[str, Any]] = []
        if not expand_relationships or max_hops < 1:
            return hits, related
        seeds: set[str] = set()
        for _, ch in top:
            if ch.entity_id:
                seeds.add(ch.entity_id)
        allowed_types = set(relationship_types) if relationship_types else None
        for seed in seeds:
            related.extend(
                self._neighbors(
                    scope, seed, allowed_types, hops=max_hops, edges=edges_snapshot
                ),
            )
        return hits, related

    @staticmethod
    def _append_neighbor_edge(
        entity_id: str,
        neighbor_id: str,
        relationship_type: str,
        seen_edges: set[tuple[str, str, str]],
        out: list[dict[str, Any]],
    ) -> None:
        key = (entity_id, neighbor_id, relationship_type)
        if key in seen_edges:
            return
        seen_edges.add(key)
        out.append(
            {
                "entity_id": entity_id,
                "neighbor_id": neighbor_id,
                "relationship_type": relationship_type,
            },
        )

    @staticmethod
    def _neighbor_frontier_step(
        edges: list[GraphEdge],
        scope: str,
        frontier: set[str],
        allowed_types: set[str] | None,
        seen_edges: set[tuple[str, str, str]],
        out: list[dict[str, Any]],
    ) -> set[str]:
        next_frontier: set[str] = set()
        for e in edges:
            if e.scope != scope:
                continue
            if allowed_types is not None and e.relationship_type not in allowed_types:
                continue
            if e.source in frontier:
                RAGStore._append_neighbor_edge(
                    e.source, e.target, e.relationship_type, seen_edges, out
                )
                next_frontier.add(e.target)
            if e.target in frontier:
                RAGStore._append_neighbor_edge(
                    e.target, e.source, e.relationship_type, seen_edges, out
                )
                next_frontier.add(e.source)
        return next_frontier

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
            frontier = self._neighbor_frontier_step(
                edges, scope, frontier, allowed_types, seen_edges, out
            )
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
