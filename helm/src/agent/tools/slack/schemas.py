"""Pydantic argument models for Slack MCP tools (no LangChain imports)."""

from __future__ import annotations

from pydantic import BaseModel


class SlackPostMessageArgs(BaseModel):
    text: str
    channel_id: str = ""
    channel: str = ""
    thread_ts: str = ""
    reply_to_ts: str = ""


class SlackReactionArgs(BaseModel):
    channel_id: str
    name: str
    timestamp: str = ""
    ts: str = ""


class SlackChatUpdateArgs(BaseModel):
    channel_id: str
    ts: str
    text: str


class SlackHistoryArgs(BaseModel):
    channel_id: str
    limit: int | None = None


class SlackRepliesArgs(BaseModel):
    channel_id: str
    thread_ts: str
    limit: int | None = None
