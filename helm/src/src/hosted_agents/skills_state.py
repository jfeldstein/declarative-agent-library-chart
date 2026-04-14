"""Process-local tools unlocked by loaded skills (POC — use sticky sessions in production)."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_unlocked: set[str] = set()


def reset_skill_unlocked_tools() -> None:
    with _lock:
        _unlocked.clear()


def unlock_tools(names: list[str]) -> None:
    with _lock:
        _unlocked.update(names)


def unlocked_tools() -> frozenset[str]:
    with _lock:
        return frozenset(_unlocked)
