"""Pytest hooks for the hosted_agents runtime."""

from __future__ import annotations

import os

# Avoid LangSmith network noise during unit tests when LangChain/LangGraph is on the path.
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
