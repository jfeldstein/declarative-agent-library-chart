"""Package metadata."""

from hosted_agents import __version__


def test_version_is_semantic_string() -> None:
    assert __version__
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts[:2])
