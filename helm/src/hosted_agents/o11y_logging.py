"""Structured logging (structlog) and test hooks for observability."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog

SERVICE_NAME = "declarative-agent"
LOG_FORMAT_ENV = "HOSTED_AGENT_LOG_FORMAT"

_configured = False


def _event_to_message(
    _logger: Any, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def reset_logging_for_tests() -> None:
    """Allow tests to re-run :func:`configure_request_logging` with a different format."""
    global _configured
    _configured = False


def configure_request_logging() -> None:
    """Configure structlog once per process (console or JSON per env)."""
    global _configured
    if _configured:
        return
    _configured = True

    fmt = (os.environ.get(LOG_FORMAT_ENV) or "console").strip().lower()
    if fmt == "json":
        processors: list[Any] = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _event_to_message,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=False),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger():
    return structlog.get_logger()
