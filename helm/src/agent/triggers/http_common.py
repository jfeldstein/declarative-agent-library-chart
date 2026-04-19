"""Shared HTTP helpers for trigger webhook routes."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request


def parse_utf8_json_object(
    raw_body: bytes,
    *,
    on_bad_json: Callable[[], None],
) -> dict[str, Any]:
    try:
        data: Any = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        on_bad_json()
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(data, dict):
        on_bad_json()
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    return data


def request_id_from_request(request: Request) -> str:
    rid = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )
    if rid:
        return str(rid).strip()
    return str(uuid.uuid4())
