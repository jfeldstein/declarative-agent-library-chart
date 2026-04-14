"""Optional embedded PostgreSQL via PGlite (``py-pglite``) for local dev and tests.

PGlite runs in-process (Node.js). Use **TCP mode** so ``psycopg`` connection pools work.
Single-process only: do not use with multi-worker Gunicorn expecting a shared database.

Install: ``uv sync --extra pglite`` (see ``pyproject.toml``).
"""

from __future__ import annotations

import atexit
import os
import socket
import threading
from typing import Any

_lock = threading.Lock()
_manager: Any | None = None


def _truthy(key: str) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _free_tcp_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return int(s.getsockname()[1])


def stop_pglite_embedded() -> None:
    """Stop embedded PGlite (tests / reload). Safe to call multiple times."""

    global _manager
    with _lock:
        if _manager is not None:
            try:
                _manager.stop()
            except Exception:
                pass
            _manager = None
    try:
        atexit.unregister(stop_pglite_embedded)
    except Exception:
        pass


def ensure_pglite_embedded() -> None:
    """Optionally start embedded PGlite and set ``HOSTED_AGENT_POSTGRES_URL``.

    When ``HOSTED_AGENT_USE_PGLITE`` is set and no effective Postgres URL is
    configured (see :func:`hosted_agents.observability.postgres_env.postgres_url`),
    starts PGlite in TCP mode and writes the DSN to ``HOSTED_AGENT_POSTGRES_URL`` only.
    If the flag is unset or a URL is already set, no-op. Requires optional
    ``py-pglite[psycopg]`` and a working Node.js install for the first run
    (``py-pglite`` may run ``npm install``).
    """

    global _manager
    from hosted_agents.observability.postgres_env import postgres_url

    if not _truthy("HOSTED_AGENT_USE_PGLITE"):
        return
    if postgres_url():
        return

    with _lock:
        if _manager is not None:
            return
        try:
            from py_pglite import PGliteConfig, PGliteManager
        except ImportError as exc:
            msg = (
                "HOSTED_AGENT_USE_PGLITE requires optional dependencies. "
                "Install with: uv sync --extra pglite"
            )
            raise RuntimeError(msg) from exc

        host = os.environ.get("HOSTED_AGENT_PGLITE_TCP_HOST", "127.0.0.1").strip()
        port_raw = os.environ.get("HOSTED_AGENT_PGLITE_TCP_PORT", "").strip()
        if port_raw:
            try:
                port = int(port_raw)
            except ValueError as exc:
                msg = (
                    f"HOSTED_AGENT_PGLITE_TCP_PORT must be an integer, got {port_raw!r}"
                )
                raise ValueError(msg) from exc
        else:
            port = _free_tcp_port(host)

        config = PGliteConfig(use_tcp=True, tcp_host=host, tcp_port=port)
        mgr = PGliteManager(config)
        mgr.start()
        uri: str = mgr.get_psycopg_uri()
        os.environ["HOSTED_AGENT_POSTGRES_URL"] = uri
        _manager = mgr
        atexit.register(stop_pglite_embedded)
