"""Reference scraper: pushes fixture text + entity graph slice to the RAG HTTP API."""

from __future__ import annotations

import os
import sys

import httpx


def run() -> None:
    base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
    if not base:
        print("RAG_SERVICE_URL is required", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    scope = os.environ.get("SCRAPER_SCOPE", "reference").strip() or "reference"
    payload = {
        "scope": scope,
        "entities": [
            {"id": "ref-doc", "entity_type": "document"},
            {"id": "ref-folder", "entity_type": "folder"},
        ],
        "relationships": [
            {
                "source": "ref-doc",
                "target": "ref-folder",
                "relationship_type": "contained_in",
            },
        ],
        "items": [
            {
                "text": os.environ.get(
                    "REFERENCE_SCRAPER_TEXT",
                    "Reference scraper fixture: login timeout bug tracked under REF-1.",
                ),
                "metadata": {"source": "reference-scraper"},
                "entity_id": "ref-doc",
            },
        ],
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(f"{base}/v1/embed", json=payload)
        r.raise_for_status()


if __name__ == "__main__":
    run()
