"""Socket Mode listener (background thread) for ``app_mention``."""

from __future__ import annotations

import logging
import threading
import uuid
from typing import TYPE_CHECKING

from hosted_agents.slack_trigger.config import SlackTriggerSettings

if TYPE_CHECKING:
    from hosted_agents.slack_trigger.dedupe import EventDeduper

_LOG = logging.getLogger(__name__)


def start_socket_mode_listener(
    settings: SlackTriggerSettings,
    deduper: EventDeduper,
) -> threading.Thread:
    """Start Slack Bolt Socket Mode in a daemon thread (blocks inside the thread on ``connect()``)."""

    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    from hosted_agents.slack_trigger.dispatch import dispatch_raw_app_mention_event

    bolt_app = App(
        token=settings.bot_token,
        signing_secret=settings.signing_secret or "",
    )

    @bolt_app.event("app_mention")
    def _on_mention(event, ack):
        ack()
        rid = str(uuid.uuid4())
        try:
            dispatch_raw_app_mention_event(
                event,
                transport="socket",
                request_id=rid,
                outer_event_id=None,
                deduper=deduper,
                settings_event_dedupe=settings.event_dedupe,
            )
        except Exception:
            _LOG.exception("slack_trigger_socket_dispatch_failed")

    handler = SocketModeHandler(bolt_app, settings.app_token)

    def _run() -> None:
        handler.connect()

    thread = threading.Thread(
        target=_run,
        daemon=True,
        name="slack-trigger-socket-mode",
    )
    thread.start()
    return thread
