"""FastAPI application for POST /v1/embed, /v1/query, /v1/relate and GET /health."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from agent.rag.models import (
    EmbedRequest,
    EmbedResponse,
    QueryHit,
    QueryRequest,
    QueryResponse,
    RelatedEdge,
    RelateRequest,
    RelateResponse,
)
from agent.rag.o11y_middleware import RAGMetricsMiddleware
from agent.rag.store import RAGStore, get_store


def _register_rag_metrics_and_health(app: FastAPI) -> None:
    @app.get("/metrics")
    def get_metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}


def _register_rag_embed(app: FastAPI, rag_store: RAGStore) -> None:
    @app.post("/v1/embed", response_model=EmbedResponse)
    def embed(req: EmbedRequest) -> EmbedResponse:
        if not req.items and not req.entities and not req.relationships:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="at least one of items, entities, or relationships is required",
            )
        chunk_ids: list[str] = []
        if req.items:
            chunk_ids = rag_store.add_chunks(
                req.scope,
                [i.model_dump() for i in req.items],
            )
        if req.entities:
            rag_store.upsert_entities(req.scope, [e.model_dump() for e in req.entities])
        if req.relationships:
            rag_store.add_relationships(
                req.scope,
                [r.model_dump() for r in req.relationships],
            )
        return EmbedResponse(
            chunk_ids=chunk_ids,
            entities_upserted=len(req.entities),
            relationships_recorded=len(req.relationships),
        )


def _register_rag_relate(app: FastAPI, rag_store: RAGStore) -> None:
    @app.post("/v1/relate", response_model=RelateResponse)
    def relate(req: RelateRequest) -> RelateResponse:
        rag_store.add_relationships(
            req.scope,
            [r.model_dump() for r in req.relationships],
        )
        return RelateResponse(relationships_recorded=len(req.relationships))


def _register_rag_query(app: FastAPI, rag_store: RAGStore) -> None:
    @app.post("/v1/query", response_model=QueryResponse)
    def query(req: QueryRequest) -> QueryResponse:
        hits_raw, related_raw = rag_store.query(
            req.scope,
            req.query,
            top_k=req.top_k,
            expand_relationships=req.expand_relationships,
            relationship_types=req.relationship_types,
            max_hops=req.max_hops,
        )
        hits = [QueryHit(**h) for h in hits_raw]
        related = [RelatedEdge(**r) for r in related_raw]
        return QueryResponse(hits=hits, related=related)


def _register_rag_routes(app: FastAPI, rag_store: RAGStore) -> None:
    _register_rag_metrics_and_health(app)
    _register_rag_embed(app, rag_store)
    _register_rag_relate(app, rag_store)
    _register_rag_query(app, rag_store)


def create_app(*, store: RAGStore | None = None) -> FastAPI:
    """Build the RAG ASGI app. Tests may inject ``store``."""
    app = FastAPI(
        title="dalc-rag",
        version="0.1.0",
        description="Managed RAG HTTP service (POC). See docs/rag-http-api.md in repo root.",
    )
    app.add_middleware(RAGMetricsMiddleware)
    rag_store = store if store is not None else get_store()
    _register_rag_routes(app, rag_store)
    return app
