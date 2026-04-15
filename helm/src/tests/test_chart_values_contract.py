"""Helm library chart values contract checks."""

from __future__ import annotations

from pathlib import Path

import yaml


def _forbidden_keys(obj: object, *, path: str = "") -> list[str]:
    bad: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            if k in {"atifExport", "shadow"}:
                bad.append(p)
            bad.extend(_forbidden_keys(v, path=p))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            bad.extend(_forbidden_keys(item, path=f"{path}[{i}]"))
    return bad


def _dict_keys_recursive(obj: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        keys.update(obj.keys())
        for v in obj.values():
            keys |= _dict_keys_recursive(v)
    elif isinstance(obj, list):
        for item in obj:
            keys |= _dict_keys_recursive(item)
    return keys


def test_library_values_yaml_excludes_atif_and_shadow() -> None:
    """[DALC-REQ-CHART-RTV-004] Removed rollout/export keys must not reappear in default values."""
    values_path = Path(__file__).resolve().parents[2] / "chart" / "values.yaml"
    data = yaml.safe_load(values_path.read_text(encoding="utf-8"))
    hits = _forbidden_keys(data)
    assert not hits, f"unexpected keys in values.yaml: {hits}"


def test_library_values_schema_excludes_atif_and_shadow() -> None:
    """[DALC-REQ-CHART-RTV-004] Schema must not document removed keys."""
    schema_path = Path(__file__).resolve().parents[2] / "chart" / "values.schema.json"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    keys = _dict_keys_recursive(schema)
    assert "atifExport" not in keys
    assert "shadow" not in keys
