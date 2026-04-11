"""HTTP request bodies for agent API routes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TriggerBody(BaseModel):
    """JSON body for ``POST /api/v1/trigger`` (LangGraph pipeline).

    Root ``systemPrompt`` (``HOSTED_AGENT_SYSTEM_PROMPT``) is the **supervisor**; configured
    subagents are exposed only as **tools** on that agent (see README). User input for the
    supervisor is ``message``.

    Legacy field ``subagent`` is rejected with **400** before this model is validated
    (see :mod:`hosted_agents.app`).
    """

    model_config = ConfigDict(extra="forbid")

    message: str | None = Field(default=None, max_length=50_000)
    load_skill: str | None = Field(default=None, min_length=1, max_length=256)
    tool: str | None = Field(default=None, min_length=1, max_length=256)
    tool_arguments: dict[str, Any] = Field(default_factory=dict)


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
