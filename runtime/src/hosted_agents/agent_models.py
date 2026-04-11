"""HTTP request bodies for agent API routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TriggerBody(BaseModel):
    """JSON body for ``POST /api/v1/trigger`` (LangGraph pipeline)."""

    load_skill: str | None = Field(default=None, min_length=1, max_length=256)
    subagent: str | None = Field(default=None, min_length=1, max_length=256)
    tool: str | None = Field(default=None, min_length=1, max_length=256)
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    query: str | None = Field(default=None, max_length=10_000)
    scope: str = Field(default="default", min_length=1, max_length=256)
    top_k: int = Field(default=5, ge=1, le=50)
    expand_relationships: bool = False
    relationship_types: list[str] | None = None
    max_hops: int = Field(default=1, ge=1, le=3)


class RagQueryBody(BaseModel):
    scope: str = Field(default="default", min_length=1, max_length=256)
    query: str = Field(..., min_length=1, max_length=10_000)
    top_k: int = Field(default=5, ge=1, le=50)
    expand_relationships: bool = False
    relationship_types: list[str] | None = None
    max_hops: int = Field(default=1, ge=1, le=3)


class SkillLoadBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)


class ToolInvokeBody(BaseModel):
    tool: str = Field(..., min_length=1, max_length=256)
    arguments: dict[str, Any] = Field(default_factory=dict)


class SubagentInvokeBody(BaseModel):
    """JSON body for ``role: rag`` subagent invocations (optional for other roles)."""

    query: str | None = Field(default=None, max_length=10_000)
    scope: str = Field(default="default", min_length=1, max_length=256)
    top_k: int = Field(default=5, ge=1, le=50)
    expand_relationships: bool = False
    relationship_types: list[str] | None = None
    max_hops: int = Field(default=1, ge=1, le=3)
