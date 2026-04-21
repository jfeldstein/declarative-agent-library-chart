"""Single global, versioned label registry for human feedback (JSON-in-env)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LabelEntry:
    label_id: str
    display_name: str
    scalar: int | None = None


def _label_ids_with_scalar_sign(
    labels: dict[str, LabelEntry],
    *,
    want_negative: bool,
) -> list[str]:
    """Ids whose scalar is ``< 0`` when ``want_negative`` else ``> 0``."""

    out: list[str] = []
    for lid, other in labels.items():
        s = other.scalar
        if s is None:
            continue
        if want_negative and s < 0:
            out.append(lid)
        if not want_negative and s > 0:
            out.append(lid)
    return out


@dataclass(frozen=True)
class LabelRegistry:
    registry_id: str
    schema_version: str
    labels: dict[str, LabelEntry]

    def resolve(self, label_id: str) -> LabelEntry | None:
        return self.labels.get(label_id)

    def opposing_scalar_label_ids(self, label_id: str) -> list[str]:
        """Return registry label ids on the opposite side of zero (e.g. negative vs positive).

        Used when a user adds a thumbs-up/down style reaction to retract prior opposite feedback.
        """

        entry = self.resolve(label_id)
        if entry is None or entry.scalar is None:
            return []
        s = entry.scalar
        if s > 0:
            out = _label_ids_with_scalar_sign(self.labels, want_negative=True)
        elif s < 0:
            out = _label_ids_with_scalar_sign(self.labels, want_negative=False)
        else:
            return []
        return sorted(out)


def _builtin_default_registry() -> LabelRegistry:
    return LabelRegistry(
        registry_id="default",
        schema_version="1",
        labels={
            "positive": LabelEntry("positive", "Positive", 1),
            "negative": LabelEntry("negative", "Negative", -1),
            "neutral": LabelEntry("neutral", "Neutral", 0),
        },
    )


def _labels_from_env_list(raw_labels: list[object]) -> dict[str, LabelEntry]:
    labels: dict[str, LabelEntry] = {}
    for item in raw_labels:
        if not isinstance(item, dict):
            continue
        lid = str(item.get("label_id") or "").strip()
        if not lid:
            continue
        disp = str(item.get("display_name") or lid)
        scalar = item.get("scalar")
        sc: int | None = int(scalar) if isinstance(scalar, int) else None
        labels[lid] = LabelEntry(lid, disp, sc)
    return labels


def load_label_registry_from_env() -> LabelRegistry:
    raw = os.environ.get("HOSTED_AGENT_LABEL_REGISTRY_JSON", "").strip()
    if not raw or raw in ("{}", "null"):
        return _builtin_default_registry()
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = "HOSTED_AGENT_LABEL_REGISTRY_JSON must be a JSON object"
        raise ValueError(msg)
    rid = str(data.get("registry_id") or "custom")
    ver = str(data.get("schema_version") or "1")
    raw_labels = data.get("labels")
    labels = _labels_from_env_list(raw_labels) if isinstance(raw_labels, list) else {}
    return LabelRegistry(registry_id=rid, schema_version=ver, labels=labels)


_cached_registry: LabelRegistry | None = None


def get_label_registry(*, reload: bool = False) -> LabelRegistry:
    """Return the process-global registry (env-backed; tests may ``reload=True``)."""

    global _cached_registry
    if _cached_registry is None or reload:
        _cached_registry = load_label_registry_from_env()
    return _cached_registry
