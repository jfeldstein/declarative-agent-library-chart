# ADR 0001: Use Python for the config-first hosted agents runtime

## Status

Accepted

## Context

The `config-first-hosted-agents` prototype needs a small, testable runtime (HTTP trigger, config from environment/ConfigMap) that matches monorepo conventions (`uv`, `pytest`) and stays easy for operators to extend (Slack/Jira/Drive tooling later).

## Decision

All first-party implementation code for this project **SHALL** be **Python** (currently `>=3.11`), packaged under `runtime/src/hosted_agents/`, with tests under `runtime/tests/` and dependency management via **`uv`** + `runtime/pyproject.toml`.

Non-Python assets (Helm charts, Skaffold/DevSpace YAML) live at the project root; the Python runtime is isolated under `runtime/`.

## Consequences

- CI runs `uv sync` / `pytest` with coverage via `uv --project runtime` from the project root (`ci.sh`).
- Future services (e.g. HTTP server for `/api/v1/trigger`) are implemented in Python unless a new ADR chooses otherwise.
- Any other language prototypes must not live in `runtime/src/` without a superseding ADR.
