"""Helm library chart values contract checks."""

from __future__ import annotations

from pathlib import Path

import yaml

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
