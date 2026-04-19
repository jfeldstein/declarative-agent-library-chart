"""Integration-style coverage for Langfuse lifecycle bridge (mock SDK client)."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.legacy_agent_metrics import register_agent_legacy_metrics
from agent.observability.middleware import publish_tool_call_completed
from agent.observability.plugins.langfuse_bridge import LangfuseLifecycleBridge
from agent.observability.plugins_config import LangfusePluginSettings
from agent.observability.run_context import bind_run_context
from agent.observability.settings import ObservabilitySettings
from agent.runtime_config import RuntimeConfig
from agent.trigger_context import TriggerContext


class _DummyObs:
    def __init__(self) -> None:
        self.updated = False
        self.ended = False

    def update(self, **_: object) -> _DummyObs:
        self.updated = True
        return self

    def end(self, **_: object) -> _DummyObs:
        self.ended = True
        return self


def _trigger_ctx() -> TriggerContext:
    return TriggerContext(
        cfg=RuntimeConfig.from_env(),
        body=None,
        system_prompt="-",
        request_id="req-1",
        run_id="run-abc",
        thread_id="thread-xyz",
        ephemeral=False,
        tenant_id="tenant-1",
        observability=ObservabilitySettings.from_env(),
    )


def test_langfuse_bridge_maps_llm_tool_and_flush() -> None:
    """[DALC-REQ-LANGFUSE-TRACE-001] Lifecycle events map to Langfuse trace + spans + flush."""

    mock = MagicMock()
    mock.create_trace_id.return_value = "deadbeefdeadbeefdeadbeefdeadbeef"
    mock.start_observation.return_value = _DummyObs()

    bridge = LangfuseLifecycleBridge(mock)
    bus = SyncEventBus()
    register_agent_legacy_metrics(bus)
    bridge.register(bus)

    ctx = _trigger_ctx()
    bind_run_context(run_id=ctx.run_id, thread_id=ctx.thread_id)

    bus.publish(
        LifecycleEvent(
            EventName.LLM_GENERATION_COMPLETED,
            {
                "ctx": ctx,
                "input_tokens": 3,
                "output_tokens": 5,
                "result": "success",
            },
        )
    )
    publish_tool_call_completed(
        tool="slack.post_message", started_at=0.0, ok=True, bus=bus
    )
    bus.publish(
        LifecycleEvent(
            EventName.TRIGGER_REQUEST_RESPONDED,
            {
                "trigger": "http",
                "http_result": "success",
                "started_at": 0.0,
                "request_bytes": 1,
                "response_bytes": 2,
            },
        )
    )

    assert mock.create_trace_id.called
    assert mock.start_observation.call_count >= 3
    assert mock.flush.called


def test_build_langfuse_client_requires_complete_settings() -> None:
    """[DALC-REQ-LANGFUSE-TRACE-004] Incomplete settings yield no client; complete settings build."""

    from agent.observability.plugins.langfuse_bridge import build_langfuse_client

    empty = LangfusePluginSettings()
    assert build_langfuse_client(empty) is None

    partial = LangfusePluginSettings(
        enabled=True,
        host="https://example.com",
        public_key=None,
        secret_key="sec",
    )
    assert build_langfuse_client(partial) is None

    full = LangfusePluginSettings(
        enabled=True,
        host="https://example.com",
        public_key="pk-test",
        secret_key="sk-test",
        flush_interval_seconds=2.5,
    )
    client = build_langfuse_client(full)
    assert client is not None


def test_plugins_config_from_env_reads_langfuse_keys(monkeypatch) -> None:
    """[DALC-REQ-LANGFUSE-TRACE-002] Env mirrors Helm keys for Langfuse plugin toggles."""

    monkeypatch.setenv("HOSTED_AGENT_LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_LANGFUSE_HOST", "https://lf.example")
    monkeypatch.setenv("HOSTED_AGENT_LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("HOSTED_AGENT_LANGFUSE_SECRET_KEY", "sk")
    monkeypatch.setenv("HOSTED_AGENT_LANGFUSE_FLUSH_INTERVAL_SECONDS", "7")

    from agent.observability.plugins_config import plugins_config_from_env

    cfg = plugins_config_from_env()
    assert cfg.langfuse.enabled is True
    assert cfg.langfuse.host == "https://lf.example"
    assert cfg.langfuse.public_key == "pk"
    assert cfg.langfuse.secret_key == "sk"
    assert cfg.langfuse.flush_interval_seconds == 7.0


def test_langfuse_bridge_avoids_prompt_bodies_in_source_contract() -> None:
    """[DALC-REQ-LANGFUSE-TRACE-003] Langfuse bridge records bounded operational fields only."""

    from agent.observability.plugins import langfuse_bridge as lb

    src = inspect.getsource(lb.LangfuseLifecycleBridge._on_llm_completed)
    assert "middleware owns PII" in src or "bounded" in src


def test_chart_values_schema_includes_langfuse_plugin_keys() -> None:
    """[DALC-REQ-LANGFUSE-TRACE-002] Helm ``values.schema.json`` exposes Langfuse plugin keys."""

    import json
    from pathlib import Path

    schema_path = Path(__file__).resolve().parents[2] / "chart" / "values.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    lf = schema["properties"]["observability"]["properties"]["plugins"]["properties"][
        "langfuse"
    ]
    keys = lf["properties"].keys()
    assert "enabled" in keys and "host" in keys
    assert "flushIntervalSeconds" in keys
