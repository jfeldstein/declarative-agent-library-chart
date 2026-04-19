"""Shared Prometheus label semantics (avoid import cycles between metrics modules)."""

from __future__ import annotations

from typing import Literal

TriggerResult = Literal["success", "client_error", "server_error"]
BinaryResult = Literal["success", "error"]
