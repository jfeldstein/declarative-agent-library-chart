"""Contract checks for Python complexity gates (Ruff C901 + complexipy)."""

from __future__ import annotations

import tomllib
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _pyproject_table() -> dict:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))


def test_ruff_config_enables_c901_with_mccabe_cap() -> None:
    """[DALC-REQ-PYTHON-COMPLEXITY-CI-001] McCabe cyclomatic complexity is selected and capped in pyproject."""
    lint = _pyproject_table().get("tool", {}).get("ruff", {}).get("lint", {})
    extend = lint.get("extend-select", [])
    assert "C901" in extend, "Ruff C901 (McCabe) must be in extend-select"
    mccabe = lint.get("mccabe", {})
    assert isinstance(mccabe.get("max-complexity"), int), "mccabe.max-complexity must be set"


def test_complexipy_config_targets_package_paths() -> None:
    """[DALC-REQ-PYTHON-COMPLEXITY-CI-002] complexipy paths and cognitive threshold are committed in pyproject."""
    cfg = _pyproject_table().get("tool", {}).get("complexipy", {})
    paths = set(cfg.get("paths", []))
    assert {"hosted_agents", "tests"}.issubset(paths), (
        "complexipy paths must include hosted_agents and tests"
    )
    assert isinstance(cfg.get("max-complexity-allowed"), int), "max-complexity-allowed must be set"
