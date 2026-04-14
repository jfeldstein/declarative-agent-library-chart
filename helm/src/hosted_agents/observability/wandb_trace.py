"""Weights & Biases trace adapter (optional dependency; mock-friendly)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from hosted_agents.observability.atif import hash_tag_value
from hosted_agents.observability.settings import ObservabilitySettings


@dataclass
class WandbTraceSession:
    """Records intended W&B calls for tests; uses ``wandb`` when installed and enabled."""

    settings: ObservabilitySettings
    run_name: str
    tags: dict[str, str] = field(default_factory=dict)
    _wandb_run: Any = None
    recorded_logs: list[dict[str, Any]] = field(default_factory=list)
    recorded_spans: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.settings.wandb_enabled:
            return
        try:
            import wandb
        except ImportError:
            return
        tags = {k: v for k, v in self.tags.items() if v}
        self._wandb_run = wandb.init(
            project=self.settings.wandb_project or "hosted-agents",
            entity=self.settings.wandb_entity,
            name=self.run_name,
            tags=[f"{k}={v}" for k, v in tags.items()][:64],
            reinit=True,
        )

    def log_tool_span(
        self,
        *,
        tool_call_id: str,
        tool_name: str,
        duration_s: float,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "duration_s": duration_s,
            **(extra or {}),
        }
        self.recorded_spans.append(payload)
        if self._wandb_run is None:
            return
        self._wandb_run.log({f"tool/{tool_call_id}/latency": duration_s})

    def log_feedback(
        self,
        *,
        tool_call_id: str,
        checkpoint_id: str | None,
        feedback_label: str,
        feedback_source: str,
    ) -> None:
        row = {
            "feedback/tool_call_id": tool_call_id,
            "feedback_label": feedback_label,
            "feedback_source": feedback_source,
            "checkpoint_id": checkpoint_id,
            "ts": time.time(),
        }
        self.recorded_logs.append(row)
        if self._wandb_run is None:
            return
        key = f"feedback/{tool_call_id}"
        self._wandb_run.log({key: row})

    def finish(self) -> None:
        if self._wandb_run is not None:
            self._wandb_run.finish()

    @staticmethod
    def mandatory_tags(
        *,
        agent_id: str | None,
        environment: str | None,
        skill_id: str | None,
        skill_version: str | None,
        model_id: str | None,
        prompt_hash: str | None,
        rollout_arm: str,
        thread_id: str,
        request_correlation_id: str | None = None,
        shadow_variant_id: str | None = None,
    ) -> dict[str, str]:
        """Return tag dict with cardinality controls (hash long free text)."""

        def tagify(key: str, val: str | None) -> tuple[str, str] | None:
            if not val:
                return None
            if len(val) > 128:
                return key, hash_tag_value(val)
            return key, val

        out: dict[str, str] = {}
        entries: list[tuple[str, str] | None] = [
            tagify("agent_id", agent_id),
            tagify("environment", environment),
            tagify("skill_id", skill_id),
            tagify("skill_version", skill_version),
            tagify("model_id", model_id),
            tagify("prompt_hash", prompt_hash),
            ("rollout_arm", rollout_arm),
            tagify("thread_id", thread_id),
            tagify("request_correlation_id", request_correlation_id),
            tagify("shadow_variant_id", shadow_variant_id),
        ]
        for ent in entries:
            if ent is None:
                continue
            k, v = ent
            if v:
                out[k] = v
        return out
