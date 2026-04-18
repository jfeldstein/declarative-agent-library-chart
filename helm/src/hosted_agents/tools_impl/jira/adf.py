"""Minimal Atlassian Document Format payloads for Jira Cloud REST v3."""

from __future__ import annotations


def plain_text_comment_body(text: str) -> dict[str, object]:
    """ADF document for a single paragraph comment."""

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            },
        ],
    }
