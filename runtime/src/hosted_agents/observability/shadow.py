"""Shadow rollout configuration (opt-in, bounded, non-mutating by default)."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ShadowSettings:
    variant_id: str
    skill_version: str | None
    model_id: str | None
    prompt_hash: str | None
    tool_allowlist: frozenset[str]
    full_mirror: bool

    @classmethod
    def from_env(cls) -> ShadowSettings | None:
        raw = os.environ.get("HOSTED_AGENT_SHADOW_VARIANT_JSON", "").strip()
        if not raw:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict):
            msg = "HOSTED_AGENT_SHADOW_VARIANT_JSON must be a JSON object"
            raise ValueError(msg)
        vid = str(data.get("shadow_variant_id") or data.get("variant_id") or "").strip()
        if not vid:
            return None
        allow = data.get("tool_allowlist") or []
        tools = frozenset(str(x) for x in allow) if isinstance(allow, list) else frozenset()
        return cls(
            variant_id=vid,
            skill_version=(str(data["skill_version"]) if data.get("skill_version") else None),
            model_id=(str(data["model_id"]) if data.get("model_id") else None),
            prompt_hash=(str(data["prompt_hash"]) if data.get("prompt_hash") else None),
            tool_allowlist=tools,
            full_mirror=bool(data.get("full_mirror")),
        )


def should_run_shadow(
    *,
    tenant_id: str | None,
    obs_enabled: bool,
    sample_rate: float,
    allow_tenants: frozenset[str],
) -> bool:
    if not obs_enabled or sample_rate <= 0:
        return False
    if allow_tenants and tenant_id and tenant_id not in allow_tenants:
        return False
    if sample_rate >= 1.0:
        return True
    h = hashlib.sha256((tenant_id or "default").encode()).hexdigest()
    bucket = int(h[:8], 16) / 0xFFFFFFFF
    return bucket < sample_rate
