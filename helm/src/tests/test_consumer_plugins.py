"""Tests for distribution-provided observability plugins (entry-point discovery)."""

from __future__ import annotations

import types
from importlib.metadata import EntryPoint
from unittest.mock import patch

import pytest

from agent.observability.bootstrap import build_event_bus, reset_observability_for_tests
from agent.observability.plugins import noop_consumer_plugin
from agent.observability.plugins.consumer_plugins import (
    OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP,
)
from agent.observability.plugins_config import (
    ConsumerPluginsSettings,
    LangfusePluginSettings,
    ObservabilityPluginsConfig,
    PluginToggle,
)


@pytest.fixture(autouse=True)
def _reset_bus() -> None:
    reset_observability_for_tests()
    yield
    reset_observability_for_tests()


def _cfg(
    *,
    prometheus_enabled: bool = False,
    consumer_plugins: ConsumerPluginsSettings | None = None,
) -> ObservabilityPluginsConfig:
    return ObservabilityPluginsConfig(
        prometheus=PluginToggle(enabled=prometheus_enabled),
        langfuse=LangfusePluginSettings(),
        wandb=PluginToggle(enabled=False),
        grafana=PluginToggle(enabled=False),
        log_shipping=PluginToggle(enabled=False),
        consumer_plugins=consumer_plugins or ConsumerPluginsSettings(),
    )


class _FakeEntryPointGroups:
    def __init__(self, eps: list[EntryPoint]) -> None:
        self._eps = eps

    def select(self, *, group: str) -> list[EntryPoint]:
        del group
        return list(self._eps)


def test_builtin_attach_runs_before_consumer_attach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-CUSTOM-O11Y-002] Built-in attach wiring runs before consumer attach hooks."""

    phases: list[str] = []

    monkeypatch.setattr(
        "agent.observability.bootstrap.attach_plugins_from_config",
        lambda proc, cfg, bus: phases.append("attach_builtin"),
    )
    monkeypatch.setattr(
        "agent.observability.bootstrap.attach_consumer_plugins",
        lambda proc, cfg, bus: phases.append("attach_consumer"),
    )

    build_event_bus(
        "agent",
        _cfg(
            consumer_plugins=ConsumerPluginsSettings(
                entry_point_allowlist=("noop-consumer",),
            ),
        ),
    )

    assert phases == ["attach_builtin", "attach_consumer"]


def test_disabled_does_not_query_entry_points() -> None:
    """[DALC-REQ-CUSTOM-O11Y-001] When allowlist is empty, skip metadata discovery."""

    def _boom() -> None:
        raise AssertionError("entry_points should not be queried when disabled")

    with patch("agent.observability.plugins.consumer_plugins.entry_points", _boom):
        build_event_bus("agent", _cfg())


def test_allowlisted_plugin_without_attach_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-CUSTOM-O11Y-001] Misconfigured allowlist (no attach) fails bootstrap."""

    monkeypatch.setattr(
        "agent.observability.plugins.consumer_plugins._materialize_plugin",
        lambda _ep: object(),
    )
    ep = EntryPoint(
        name="bad-shape",
        value="unused:unused",
        group=OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP,
    )
    with (
        patch(
            "agent.observability.plugins.consumer_plugins.entry_points",
            lambda: _FakeEntryPointGroups([ep]),
        ),
        pytest.raises(ValueError, match="allowlisted"),
    ):
        build_event_bus(
            "agent",
            _cfg(
                consumer_plugins=ConsumerPluginsSettings(
                    entry_point_allowlist=("bad-shape",),
                ),
            ),
        )


def test_allowlisted_plugin_non_callable_attach_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-CUSTOM-O11Y-001] Non-callable attach fails bootstrap."""

    monkeypatch.setattr(
        "agent.observability.plugins.consumer_plugins._materialize_plugin",
        lambda _ep: types.SimpleNamespace(attach="not-callable"),
    )
    ep = EntryPoint(
        name="bad-attach",
        value="unused:unused",
        group=OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP,
    )
    with (
        patch(
            "agent.observability.plugins.consumer_plugins.entry_points",
            lambda: _FakeEntryPointGroups([ep]),
        ),
        pytest.raises(TypeError, match="non-callable"),
    ):
        build_event_bus(
            "agent",
            _cfg(
                consumer_plugins=ConsumerPluginsSettings(
                    entry_point_allowlist=("bad-attach",),
                ),
            ),
        )


def test_enabled_invokes_hooks_for_allowlisted_entry_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-CUSTOM-O11Y-001] [DALC-REQ-CUSTOM-O11Y-003] Hooks receive process kind."""

    recorded: list[tuple[str, str]] = []

    def _fake_attach(
        process_kind: str,
        cfg: ObservabilityPluginsConfig,
        bus: object,
    ) -> None:
        del cfg, bus
        recorded.append(("attach", process_kind))

    monkeypatch.setattr(noop_consumer_plugin.PLUGIN, "attach", _fake_attach)

    ep = EntryPoint(
        name="noop-consumer",
        value="agent.observability.plugins.noop_consumer_plugin:PLUGIN",
        group=OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP,
    )

    with patch(
        "agent.observability.plugins.consumer_plugins.entry_points",
        lambda: _FakeEntryPointGroups([ep]),
    ):
        build_event_bus(
            "scraper",
            _cfg(
                consumer_plugins=ConsumerPluginsSettings(
                    entry_point_allowlist=("noop-consumer",),
                ),
            ),
        )

    assert recorded == [("attach", "scraper")]


def test_broken_import_does_not_fail_startup() -> None:
    """[DALC-REQ-CUSTOM-O11Y-005] Broken entry points are skipped (structured warning)."""

    bad = EntryPoint(
        name="bad-import",
        value="tests.consumer_plugin_error_on_import:PLUGIN",
        group=OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP,
    )

    with patch(
        "agent.observability.plugins.consumer_plugins.entry_points",
        lambda: _FakeEntryPointGroups([bad]),
    ):
        build_event_bus(
            "agent",
            _cfg(
                consumer_plugins=ConsumerPluginsSettings(
                    entry_point_allowlist=("bad-import",),
                ),
            ),
        )


def test_plugins_config_from_env_maps_entry_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-CUSTOM-O11Y-004] [DALC-REQ-CHART-RTV-005] Env maps entry points + optional JSON."""

    from agent.observability.plugins_config import plugins_config_from_env

    monkeypatch.setenv(
        "HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS",
        "noop-consumer,other",
    )
    monkeypatch.setenv(
        "HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_CONFIG_JSON",
        '{"k":"v"}',
    )

    cfg = plugins_config_from_env()
    assert cfg.consumer_plugins.entry_point_allowlist == ("noop-consumer", "other")
    assert cfg.consumer_plugins.json_config == '{"k":"v"}'
