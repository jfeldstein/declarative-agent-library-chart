"""Tests for ``ToolSpec`` frozen contract."""

from __future__ import annotations

import ast
from dataclasses import fields

import pytest
from pydantic import BaseModel

from agent.tools.contract import ToolSpec


class _DummyArgs(BaseModel):
    pass


def test_toolspec_is_frozen() -> None:
    spec = ToolSpec(
        id="a.b",
        description="d",
        args_schema=_DummyArgs,
        handler=lambda _: {},
    )
    with pytest.raises(AttributeError):
        spec.id = "x"  # type: ignore[misc]


def test_toolspec_fields_exact() -> None:
    names = {f.name for f in fields(ToolSpec)}
    assert names == {"id", "description", "args_schema", "handler"}


def test_toolspec_contract_has_no_langchain_imports() -> None:
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "agent" / "tools" / "contract.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    banned = {"langchain", "langchain_core"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in banned, alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                assert root not in banned, node.module
