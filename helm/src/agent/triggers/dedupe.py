"""Optional in-memory dedupe for Slack ``event_id`` retries."""

from __future__ import annotations

from collections import OrderedDict


class EventDeduper:
    """FIFO-bounded set for Slack event ids (no secrets stored)."""

    def __init__(self, *, max_entries: int = 10_000) -> None:
        self._max = max(1, max_entries)
        self._seen: OrderedDict[str, None] = OrderedDict()

    def is_duplicate(self, event_id: str) -> bool:
        key = event_id.strip()
        if not key:
            return False
        if key in self._seen:
            self._seen.move_to_end(key)
            return True
        self._seen[key] = None
        self._seen.move_to_end(key)
        while len(self._seen) > self._max:
            self._seen.popitem(last=False)
        return False
