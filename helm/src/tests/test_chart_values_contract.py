"""Helm library chart values contract checks."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HELLO_CHART = _REPO_ROOT / "examples" / "hello-world" / "Chart.yaml"
_HELLO_VALUES = _REPO_ROOT / "examples" / "hello-world" / "values.yaml"
_LIBRARY_CHART = _REPO_ROOT / "helm" / "chart" / "Chart.yaml"

_FORBIDDEN_CHART_KEYS = frozenset({"atifExport", "shadow"})


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
                _paths_to_forbidden_keys(item, prefix=f"{prefix}[{i}]" if prefix else f"[{i}]")
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
