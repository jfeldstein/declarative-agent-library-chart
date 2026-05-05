"""Chat model resolution for the supervisor (``create_agent``)."""

from __future__ import annotations

import json
import os
from typing import Any, cast, override

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class FakeToolChatModel(SimpleChatModel):
    """Test double: supports ``bind_tools`` and scripted ``AIMessage`` turns."""

    responses: list[AIMessage]
    i: int = 0

    @property
    @override
    def _llm_type(self) -> str:
        return "dalc-fake-tool-chat"

    def bind_tools(self, tools: Any, **kwargs: Any) -> FakeToolChatModel:
        return self

    @override
    def _call(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError

    @override
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        response = self.responses[self.i]
        if self.i < len(self.responses) - 1:
            self.i += 1
        return ChatResult(generations=[ChatGeneration(message=response)])


def _to_langchain_model_spec(spec: str) -> str:
    """Normalise LiteLLM-style ``provider/model`` to LangChain ``provider:model``.

    LiteLLM uses ``openai/gpt-4o-mini``; LangChain ``init_chat_model`` expects
    ``openai:gpt-4o-mini``.  Both forms are accepted; the slash form is canonical
    for this chart (``[DALC-REQ-CHART-RTV-007]``).
    """
    if "/" in spec and ":" not in spec:
        provider, _, model = spec.partition("/")
        return f"{provider}:{model}"
    return spec


def resolve_chat_model() -> Any:
    """Return a chat model for the supervisor.

    Uses ``HOSTED_AGENT_CHAT_MODEL`` (LiteLLM-style ``openai/gpt-4o-mini`` or
    LangChain-style ``openai:gpt-4o-mini``) via
    :func:`langchain.chat_models.init_chat_model`. Install the matching provider
    package (e.g. ``langchain-openai``) when using a remote model.

    For tests, monkeypatch this function or set ``HOSTED_AGENT_FAKE_CHAT_SEQUENCE``
    to a JSON list of serialized turns (see :func:`fake_model_from_env`).
    """
    fake = fake_model_from_env()
    if fake is not None:
        return fake
    spec = os.environ.get("HOSTED_AGENT_CHAT_MODEL", "").strip()
    if not spec:
        msg = (
            "HOSTED_AGENT_CHAT_MODEL is required when subagents are configured "
            "(e.g. openai/gpt-4o-mini). Install the provider integration package."
        )
        raise ValueError(msg)
    return init_chat_model(_to_langchain_model_spec(spec))


def fake_model_from_env() -> FakeToolChatModel | None:
    raw = os.environ.get("HOSTED_AGENT_FAKE_CHAT_SEQUENCE", "").strip()
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, list):
        msg = "HOSTED_AGENT_FAKE_CHAT_SEQUENCE must be a JSON array"
        raise ValueError(msg)
    responses: list[AIMessage] = []
    for item in data:
        if isinstance(item, str):
            responses.append(AIMessage(content=item))
        elif isinstance(item, dict):
            responses.append(cast(AIMessage, AIMessage(**item)))
        else:
            msg = "Each element must be a string or AIMessage-shaped object"
            raise ValueError(msg)
    return FakeToolChatModel(responses=responses)
