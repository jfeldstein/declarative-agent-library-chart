"""Chat model spec normalisation (LiteLLM → LangChain format).

[DALC-REQ-CHART-RTV-007] The runtime accepts LiteLLM ``provider/model`` format and
converts it to LangChain ``provider:model`` before calling ``init_chat_model``.
"""

from __future__ import annotations

import pytest

from agent.chat_model import _to_langchain_model_spec


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # LiteLLM slash format → colon format
        ("openai/gpt-4o-mini", "openai:gpt-4o-mini"),
        ("anthropic/claude-3-5-haiku-latest", "anthropic:claude-3-5-haiku-latest"),
        ("cohere/command-r", "cohere:command-r"),
        # LangChain colon format → unchanged
        ("openai:gpt-4o-mini", "openai:gpt-4o-mini"),
        ("anthropic:claude-3-haiku-20240307", "anthropic:claude-3-haiku-20240307"),
        # Plain model name (no prefix) → unchanged
        ("gpt-4o-mini", "gpt-4o-mini"),
    ],
)
def test_to_langchain_model_spec(raw: str, expected: str) -> None:
    """[DALC-REQ-CHART-RTV-007] LiteLLM provider/model is normalised to provider:model."""
    assert _to_langchain_model_spec(raw) == expected
