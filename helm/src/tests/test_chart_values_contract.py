"""Helm library chart values contract checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from hosted_agents.tools.dispatch import REGISTERED_MCP_TOOL_IDS

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HELLO_CHART = _REPO_ROOT / "examples" / "hello-world" / "Chart.yaml"
_HELLO_VALUES = _REPO_ROOT / "examples" / "hello-world" / "values.yaml"
_LIBRARY_CHART = _REPO_ROOT / "helm" / "chart" / "Chart.yaml"

_FORBIDDEN_CHART_KEYS = frozenset({"atifExport", "shadow"})

_VALUES_GLOBS = (
    "helm/chart/values.yaml",
    "helm/chart/values.*.yaml",
    "examples/*/values.yaml",
    "examples/*/values.*.yaml",
)


def _iter_mcp_enabled_tool_strings(obj: Any) -> list[str]:
    """Collect `mcp.enabledTools` entries from nested Helm values documents."""
    found: list[str] = []
    if isinstance(obj, dict):
        mcp = obj.get("mcp")
        if isinstance(mcp, dict):
            raw = mcp.get("enabledTools")
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, str):
                        found.append(item)
                    else:
                        raise AssertionError(
                            "mcp.enabledTools must be a list of strings; "
                            f"got {type(item).__name__}: {item!r}"
                        )
        for v in obj.values():
            found.extend(_iter_mcp_enabled_tool_strings(v))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_iter_mcp_enabled_tool_strings(item))
    return found


def _paths_to_forbidden_keys(obj: object, *, prefix: str = "") -> list[str]:
    """Return dotted paths to dict keys that must not exist in chart values or schema."""
    found: list[str] = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key in _FORBIDDEN_CHART_KEYS:
                found.append(path)
            found.extend(_paths_to_forbidden_keys(val, prefix=path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(
                _paths_to_forbidden_keys(
                    item, prefix=f"{prefix}[{i}]" if prefix else f"[{i}]"
                )
            )
    return found


def test_library_values_yaml_excludes_atif_and_shadow() -> None:
    """[DALC-REQ-CHART-RTV-004] Removed rollout/export keys must not reappear in default values."""
    values_path = Path(__file__).resolve().parents[2] / "chart" / "values.yaml"
    data = yaml.safe_load(values_path.read_text(encoding="utf-8"))
    hits = _paths_to_forbidden_keys(data)
    assert not hits, f"unexpected keys in values.yaml: {hits}"


def test_library_values_schema_excludes_atif_and_shadow() -> None:
    """[DALC-REQ-CHART-RTV-004] Schema must not document removed keys."""
    schema_path = Path(__file__).resolve().parents[2] / "chart" / "values.schema.json"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    hits = _paths_to_forbidden_keys(schema)
    assert not hits, f"unexpected keys in values.schema.json: {hits}"


def test_library_chart_name_is_dalc_packaging() -> None:
    """[DALC-REQ-DALC-PKG-001]"""
    chart = yaml.safe_load(_LIBRARY_CHART.read_text(encoding="utf-8"))
    assert chart.get("name") == "declarative-agent-library-chart"


def test_library_image_repository_default_is_dalc_packaging() -> None:
    """[DALC-REQ-DALC-PKG-003]"""
    values_path = Path(__file__).resolve().parents[2] / "chart" / "values.yaml"
    data = yaml.safe_load(values_path.read_text(encoding="utf-8"))
    assert data.get("image", {}).get("repository") == "declarative-agent-library-chart"


def test_hello_world_example_uses_agent_alias_and_values_key() -> None:
    """[DALC-REQ-DALC-PKG-002]"""
    chart = yaml.safe_load(_HELLO_CHART.read_text(encoding="utf-8"))
    deps = chart.get("dependencies") or []
    assert deps, "hello-world Chart.yaml must declare dependencies"
    lib = next(d for d in deps if d.get("name") == "declarative-agent-library-chart")
    assert lib.get("alias") == "agent"
    values = yaml.safe_load(_HELLO_VALUES.read_text(encoding="utf-8"))
    assert "agent" in values
    assert "declarative-agent" not in values


def test_mcp_enabled_tools_are_subset_of_dispatch_registry() -> None:
    """Helm `mcp.enabledTools` must reference only ids implemented in `tools.dispatch`."""
    bad: list[str] = []
    for pattern in _VALUES_GLOBS:
        for path in sorted(_REPO_ROOT.glob(pattern)):
            if not path.is_file():
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if data is None:
                continue
            for tid in _iter_mcp_enabled_tool_strings(data):
                if tid not in REGISTERED_MCP_TOOL_IDS:
                    bad.append(f"{path.relative_to(_REPO_ROOT)}: {tid}")
    assert not bad, (
        "mcp.enabledTools entries must be in REGISTERED_MCP_TOOL_IDS "
        f"(tools.dispatch): {bad}"
    )
