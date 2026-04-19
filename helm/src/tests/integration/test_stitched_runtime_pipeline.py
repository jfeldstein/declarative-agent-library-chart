"""Stitched integration: RAG ingest → query → agent RAG proxy → MCP trigger.

Starts a short-lived uvicorn **RAG** HTTP server using the shared ``get_store()`` singleton
so embed/query data is visible to the agent's ``HOSTED_AGENT_RAG_BASE_URL`` proxy calls.
"""

from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Generator

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from hosted_agents.app import create_app
from hosted_agents.rag.app import create_app as create_rag_app
from hosted_agents.rag.store import reset_store_for_tests


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def rag_http_base_url() -> Generator[str, None, None]:
    reset_store_for_tests()
    app = create_rag_app()
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server.started:
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("RAG uvicorn did not start within 5 seconds")
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=3.0)


@pytest.mark.integration
def test_stitched_embed_query_proxy_and_trigger_mcp(
    rag_http_base_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Embed (scraper-shaped) → query hits → /api/v1/rag/query proxy → sample.echo MCP."""
    monkeypatch.setenv("HOSTED_AGENT_RAG_BASE_URL", rag_http_base_url)
    monkeypatch.setenv(
        "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["sample.echo"])
    )

    scope = "stitched_demo"
    with httpx.Client(timeout=30.0) as h:
        emb = h.post(
            f"{rag_http_base_url}/v1/embed",
            json={
                "scope": scope,
                "items": [
                    {
                        "text": "Widget catalog SKU-99 ships in two business days.",
                        "metadata": {"source": "jira-scraper-shaped"},
                        "entity_id": "issue-42",
                    }
                ],
            },
        )
        assert emb.status_code == 200

        q_direct = h.post(
            f"{rag_http_base_url}/v1/query",
            json={
                "scope": scope,
                "query": "shipping time SKU-99",
                "top_k": 3,
            },
        )
        assert q_direct.status_code == 200
        assert q_direct.json()["hits"]

    agent = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(agent)

    proxied = client.post(
        "/api/v1/rag/query",
        json={
            "scope": scope,
            "query": "shipping time SKU-99",
            "top_k": 3,
        },
    )
    assert proxied.status_code == 200
    proxied_hits = proxied.json().get("hits") or []
    assert proxied_hits
    assert "SKU-99" in proxied_hits[0].get("text", "") or any(
        "SKU-99" in (hit.get("text") or "") for hit in proxied_hits
    )

    trig = client.post(
        "/api/v1/trigger",
        json={"tool": "sample.echo", "tool_arguments": {"message": "stitched-ok"}},
    )
    assert trig.status_code == 200
    assert trig.json()["result"]["echo"] == "stitched-ok"
