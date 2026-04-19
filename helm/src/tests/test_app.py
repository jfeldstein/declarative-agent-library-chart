"""Tests for HTTP trigger app."""

import pytest
from fastapi.testclient import TestClient

from agent.app import create_app


def test_post_trigger_uses_injected_prompt() -> None:
    app = create_app(system_prompt='Respond, "Hello :wave:"')
    client = TestClient(app)
    response = client.post("/api/v1/trigger")
    assert response.status_code == 200
    assert response.text == "Hello :wave:"


def test_post_trigger_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from agent.env import SYSTEM_PROMPT_ENV_KEY

    monkeypatch.setenv(SYSTEM_PROMPT_ENV_KEY, 'Respond, "from env"')
    app = create_app()
    client = TestClient(app)
    response = client.post("/api/v1/trigger")
    assert response.status_code == 200
    assert response.text == "from env"


def test_post_trigger_bad_prompt_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    from agent.env import SYSTEM_PROMPT_ENV_KEY

    monkeypatch.setenv(SYSTEM_PROMPT_ENV_KEY, "   ")
    app = create_app()
    client = TestClient(app)
    response = client.post("/api/v1/trigger")
    assert response.status_code == 400
