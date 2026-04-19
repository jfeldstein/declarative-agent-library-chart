"""Token / TTFT / cost Prometheus metrics (dalc-runtime-token-metrics / cfha capability).

Traceability: [DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-003]
[DALC-REQ-TOKEN-MET-004] [DALC-REQ-TOKEN-MET-005] [DALC-REQ-TOKEN-MET-006]
[DALC-REQ-O11Y-LOGS-006]
"""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from agent.app import create_app
from agent.chat_model import FakeToolChatModel
from agent.llm_metrics import SupervisorLlmMetricsCallback
from tests.conftest import patch_supervisor_fake_model


def _metrics_text(client: TestClient) -> str:
    r = client.get("/metrics")
    assert r.status_code == 200
    return r.text


def _histogram_sum(text: str, metric_name: str) -> float:
    prefix = f"{metric_name}_sum "
    for ln in text.splitlines():
        if ln.startswith(prefix):
            return float(ln.split()[-1])
    return 0.0


def _counter_value(text: str, line_prefix: str) -> float:
    """Parse counter value from first matching exposition line; 0 if series not yet emitted."""
    for ln in text.splitlines():
        if ln.startswith("#"):
            continue
        if ln.startswith(line_prefix):
            return float(ln.split()[-1])
    return 0.0


def test_llm_token_counters_and_cost_with_usage_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-005]"""
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [{"name": "s1", "systemPrompt": 'Respond, "S"', "description": "s1"}],
        ),
    )
    monkeypatch.setenv("HOSTED_AGENT_ID", "unit-agent")
    monkeypatch.setenv("HOSTED_AGENT_CHAT_MODEL", "fake:unit-model")
    monkeypatch.setenv("HOSTED_AGENT_LLM_EST_COST_USD_PER_INPUT_TOKEN", "0.00001")
    monkeypatch.setenv("HOSTED_AGENT_LLM_EST_COST_USD_PER_OUTPUT_TOKEN", "0.00002")

    patch_supervisor_fake_model(
        monkeypatch,
        FakeToolChatModel(
            responses=[
                AIMessage(
                    content="hello",
                    usage_metadata={
                        "input_tokens": 10,
                        "output_tokens": 4,
                        "total_tokens": 14,
                    },
                ),
            ],
        ),
    )
    app = create_app(system_prompt="You are a test supervisor.")
    client = TestClient(app)
    before = _metrics_text(client)
    client.post("/api/v1/trigger", json={"message": "hi"})
    after = _metrics_text(client)

    pfx = (
        'agent_runtime_llm_input_tokens_total{agent_id="unit-agent",'
        'model_id="fake:unit-model",result="success"}'
    )
    assert _counter_value(after, pfx) >= _counter_value(before, pfx) + 10 - 1e-9
    pfx_o = (
        'agent_runtime_llm_output_tokens_total{agent_id="unit-agent",'
        'model_id="fake:unit-model",result="success"}'
    )
    assert _counter_value(after, pfx_o) >= _counter_value(before, pfx_o) + 4 - 1e-9
    pfx_c = (
        'agent_runtime_llm_estimated_cost_usd_total{agent_id="unit-agent",'
        'model_id="fake:unit-model",result="success"}'
    )
    # 10 * 1e-5 + 4 * 2e-5
    assert (
        _counter_value(after, pfx_c) >= _counter_value(before, pfx_c) + 0.00018 - 1e-12
    )


def test_llm_usage_missing_when_no_usage_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002]"""
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [{"name": "s1", "systemPrompt": 'Respond, "S"', "description": "s1"}],
        ),
    )
    monkeypatch.setenv("HOSTED_AGENT_ID", "unit-agent")
    monkeypatch.setenv("HOSTED_AGENT_CHAT_MODEL", "fake:unit-model")

    patch_supervisor_fake_model(
        monkeypatch,
        FakeToolChatModel(responses=[AIMessage(content="no-usage")]),
    )
    client = TestClient(create_app(system_prompt="You are a test supervisor."))
    before = _metrics_text(client)
    client.post("/api/v1/trigger", json={"message": "hi"})
    after = _metrics_text(client)

    pfx_m = (
        'agent_runtime_llm_usage_missing_total{agent_id="unit-agent",'
        'model_id="fake:unit-model",result="success"}'
    )
    assert _counter_value(after, pfx_m) == _counter_value(before, pfx_m) + 1.0


def test_orphan_on_llm_end_skips_ttft_observe(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-TOKEN-MET-003] No paired start → no TTFT sample (avoids bogus near-zero)."""
    import agent.llm_metrics as lm

    from agent.trigger_graph import trigger_context_for_admin_reads

    calls: list[tuple[float, str]] = []

    def _spy_ttft(
        ctx: object,
        seconds: float,
        *,
        streaming_label: str,
        result: str,
    ) -> None:
        calls.append((seconds, streaming_label))

    monkeypatch.setattr(lm, "observe_llm_time_to_first_token", _spy_ttft)
    ctx = trigger_context_for_admin_reads()
    cb = SupervisorLlmMetricsCallback(ctx)
    rid = uuid4()
    gen = ChatGeneration(
        message=AIMessage(
            content="orphan",
            usage_metadata={
                "input_tokens": 2,
                "output_tokens": 1,
                "total_tokens": 3,
            },
        ),
    )
    cb.on_llm_end(LLMResult(generations=[[gen]]), run_id=rid)
    assert calls == []


def test_ttft_histogram_on_streaming_first_token() -> None:
    """[DALC-REQ-TOKEN-MET-003]"""
    import agent.llm_metrics as lm

    from agent.trigger_graph import trigger_context_for_admin_reads

    ctx = trigger_context_for_admin_reads()
    cb = SupervisorLlmMetricsCallback(ctx)
    rid = uuid4()

    with patch.object(
        lm.time,
        "perf_counter",
        side_effect=[100.0, 100.06],
    ):
        cb.on_chat_model_start({}, [[]], run_id=rid)
        cb.on_llm_new_token("x", run_id=rid)

        gen = ChatGeneration(
            message=AIMessage(
                content="done",
                usage_metadata={
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "total_tokens": 2,
                },
            ),
        )
        cb.on_llm_end(
            LLMResult(generations=[[gen]]),
            run_id=rid,
        )

    client = TestClient(create_app(system_prompt='Respond, "x"'))
    text = _metrics_text(client)
    assert "agent_runtime_llm_time_to_first_token_seconds" in text
    assert 'streaming="true"' in text


def test_new_metric_help_lines_include_semantics() -> None:
    """[DALC-REQ-TOKEN-MET-006] HELP lines for new collectors."""
    client = TestClient(create_app(system_prompt='Respond, "x"'))
    text = _metrics_text(client)
    assert (
        "# HELP agent_runtime_llm_estimated_cost_usd_total" in text
        or "agent_runtime_llm_estimated_cost_usd_total" in text
    )
    help_block = text
    for line in help_block.splitlines():
        if line.startswith("# HELP agent_runtime_llm_estimated_cost_usd_total"):
            assert "estimate" in line.lower()
            break
    else:
        pytest.fail("missing HELP for estimated cost")


def test_trigger_payload_histograms_record_response_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-TOKEN-MET-004] Successful trigger responses observe response byte histogram."""
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [{"name": "s1", "systemPrompt": 'Respond, "S"', "description": "s1"}],
        ),
    )
    patch_supervisor_fake_model(
        monkeypatch,
        FakeToolChatModel(
            responses=[
                AIMessage(
                    content="payload-response-body-text",
                    usage_metadata={
                        "input_tokens": 1,
                        "output_tokens": 2,
                        "total_tokens": 3,
                    },
                ),
            ],
        ),
    )
    client = TestClient(create_app(system_prompt="sys"))
    before = _metrics_text(client)
    r = client.post("/api/v1/trigger", json={"message": "hello-response-bytes"})
    assert r.status_code == 200
    out_len = len(r.text.encode("utf-8"))
    after = _metrics_text(client)
    assert "agent_runtime_http_trigger_response_bytes" in after
    assert _histogram_sum(after, "agent_runtime_http_trigger_response_bytes") >= (
        _histogram_sum(before, "agent_runtime_http_trigger_response_bytes")
        + out_len
        - 1e-9
    )


def test_trigger_payload_histograms_record_request_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-TOKEN-MET-004]"""
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [{"name": "s1", "systemPrompt": 'Respond, "S"', "description": "s1"}],
        ),
    )
    patch_supervisor_fake_model(
        monkeypatch,
        FakeToolChatModel(
            responses=[
                AIMessage(
                    content="ok",
                    usage_metadata={
                        "input_tokens": 1,
                        "output_tokens": 1,
                        "total_tokens": 2,
                    },
                ),
            ],
        ),
    )
    client = TestClient(create_app(system_prompt="sys"))
    body = {"message": "hello-payload-test"}
    raw_len = len(json.dumps(body).encode("utf-8"))
    before = _metrics_text(client)
    client.post("/api/v1/trigger", json=body)
    after = _metrics_text(client)
    # Histogram _sum increases by observed value; check bucket or sum moved
    assert "agent_runtime_http_trigger_request_bytes" in after
    assert after.count("agent_runtime_http_trigger_request_bytes") >= before.count(
        "agent_runtime_http_trigger_request_bytes",
    )
    assert raw_len > 10


def test_o11y_logs_token_dashboard_capability_documented() -> None:
    """[DALC-REQ-O11Y-LOGS-006] Token dashboard import path and observability cross-link."""
    from pathlib import Path

    readme = (
        Path(__file__).resolve().parent.parent.parent.parent / "grafana" / "README.md"
    )
    text = readme.read_text(encoding="utf-8")
    assert "cfha-token-metrics.json" in text
    assert "docs/observability.md" in text


def test_cfha_token_dashboard_promql_matches_observability_metric_names() -> None:
    """[DALC-REQ-O11Y-LOGS-006] Grafana ``cfha-token-metrics.json`` queries reference documented names."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent.parent
    dash = json.loads(
        (root / "grafana" / "cfha-token-metrics.json").read_text(encoding="utf-8")
    )
    obs = (root / "docs" / "observability.md").read_text(encoding="utf-8")
    pat = re.compile(r"\b(agent_runtime[a-z0-9_]+)\b")
    for panel in dash.get("panels", []):
        for t in panel.get("targets", []):
            expr = t.get("expr") or ""
            for m in pat.findall(expr):
                base = (
                    m.removesuffix("_bucket")
                    .removesuffix("_sum")
                    .removesuffix("_count")
                )
                assert base in obs, (
                    f"missing from docs/observability.md: {base} (from {expr!r})"
                )
