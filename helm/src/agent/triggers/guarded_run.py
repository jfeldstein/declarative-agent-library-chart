"""Guard trigger runs so error metrics fire before the exception propagates."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def run_guarded(operation: Callable[[], T], *, on_error: Callable[[], None]) -> T:
    try:
        return operation()
    except Exception:
        on_error()
        raise
