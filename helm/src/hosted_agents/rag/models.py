"""Pydantic models for the RAG HTTP API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EmbedItem(BaseModel):
    text: str = Field(..., min_length=1, max_length=1_000_000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    entity_id: str | None = Field(default=None, max_length=512)


class EntityUpsert(BaseModel):
    id: str = Field(..., min_length=1, max_length=512)
    entity_type: str | None = Field(default=None, max_length=256)


class RelationshipDecl(BaseModel):
    source: str = Field(..., min_length=1, max_length=512)
    target: str = Field(..., min_length=1, max_length=512)
    relationship_type: str = Field(..., min_length=1, max_length=256)


class EmbedRequest(BaseModel):
    scope: str = Field(default="default", min_length=1, max_length=256)
    items: list[EmbedItem] = Field(default_factory=list, max_length=500)
    entities: list[EntityUpsert] = Field(default_factory=list, max_length=2000)
    relationships: list[RelationshipDecl] = Field(default_factory=list, max_length=5000)


class EmbedResponse(BaseModel):
    chunk_ids: list[str]
    entities_upserted: int
    relationships_recorded: int


class RelateRequest(BaseModel):
    scope: str = Field(default="default", min_length=1, max_length=256)
    relationships: list[RelationshipDecl] = Field(..., min_length=1, max_length=5000)


class RelateResponse(BaseModel):
    relationships_recorded: int


class QueryRequest(BaseModel):
    scope: str = Field(default="default", min_length=1, max_length=256)
    query: str = Field(..., min_length=1, max_length=10_000)
    top_k: int = Field(default=5, ge=1, le=50)
    expand_relationships: bool = False
    relationship_types: list[str] | None = None
    max_hops: int = Field(default=1, ge=1, le=3)


class QueryHit(BaseModel):
    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]
    entity_id: str | None


class RelatedEdge(BaseModel):
    entity_id: str
    neighbor_id: str
    relationship_type: str


class QueryResponse(BaseModel):
    hits: list[QueryHit]
    related: list[RelatedEdge] = Field(default_factory=list)
