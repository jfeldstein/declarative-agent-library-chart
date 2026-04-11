"""Per-request context for the trigger pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from hosted_agents.agent_models import TriggerBody
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.runtime_config import RuntimeConfig


@dataclass(frozen=True)
class TriggerContext:
    cfg: RuntimeConfig
    body: TriggerBody | None
    system_prompt: str
    request_id: str
    thread_id: str
    run_id: str
    ephemeral: bool = False
    tenant_id: str | None = None
    observability: ObservabilitySettings | None = None
