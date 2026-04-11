"""Canonical trajectory builder (ordered steps for W&B and ATIF)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrajectoryStep:
    kind: str
    payload: dict[str, Any]
    created_at: float = field(default_factory=time.time)


@dataclass
class CanonicalTrajectory:
    run_id: str
    thread_id: str
    steps: list[TrajectoryStep] = field(default_factory=list)


class TrajectoryRecorder:
    """Process-local recorder keyed by ``run_id``."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_run: dict[str, CanonicalTrajectory] = {}

    def start(self, run_id: str, thread_id: str) -> None:
        with self._lock:
            self._by_run[run_id] = CanonicalTrajectory(run_id=run_id, thread_id=thread_id)

    def append(self, run_id: str, kind: str, payload: dict[str, Any]) -> None:
        with self._lock:
            tr = self._by_run.get(run_id)
            if tr is None:
                tr = CanonicalTrajectory(run_id=run_id, thread_id="")
                self._by_run[run_id] = tr
            tr.steps.append(TrajectoryStep(kind=kind, payload=dict(payload)))

    def get(self, run_id: str) -> CanonicalTrajectory | None:
        with self._lock:
            tr = self._by_run.get(run_id)
            if tr is None:
                return None
            return CanonicalTrajectory(
                run_id=tr.run_id,
                thread_id=tr.thread_id,
                steps=list(tr.steps),
            )

    def reset(self) -> None:
        with self._lock:
            self._by_run.clear()


trajectory_recorder = TrajectoryRecorder()
