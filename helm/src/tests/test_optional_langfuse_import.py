"""Optional Langfuse dependency behavior.

The agent should start when Langfuse is disabled even if the SDK is not installed.
"""

from __future__ import annotations

import builtins

from agent.observability.events import SyncEventBus
from agent.observability.plugins.wiring import attach_plugins_from_config
from agent.observability.plugins_config import ObservabilityPluginsConfig


def test_attach_plugins_langfuse_disabled_does_not_import_langfuse(monkeypatch) -> None:
    """Langfuse wiring must be lazy when plugin disabled."""

    real_import = builtins.__import__

    def guarded_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "langfuse" or name.endswith(".langfuse_bridge"):
            raise AssertionError(f"unexpected import while langfuse disabled: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    cfg = ObservabilityPluginsConfig()
    assert cfg.langfuse.enabled is False
    attach_plugins_from_config("agent", cfg, SyncEventBus())
