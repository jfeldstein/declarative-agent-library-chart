# ADR 0001: Use Python for the config-first hosted agents runtime

## Status

Accepted

## Context

The `config-first-hosted-agents` prototype needs a small, testable runtime (HTTP trigger, config from environment/ConfigMap) that matches monorepo conventions (`uv`, `pytest`) and stays easy for operators to extend (Slack/Jira/Drive tooling later).

## Decision

All first-party implementation code for this project **SHALL** be **Python** (currently `>=3.11`), packaged under `helm/src/hosted_agents/`, with tests under `helm/src/tests/` and dependency management via **`uv`** + `helm/src/pyproject.toml`.

Non-Python assets (Helm charts, Skaffold/DevSpace YAML) live at the project root; the Python runtime is isolated under `helm/src/`.

## Consequences

- CI runs `uv sync` / `pytest` with coverage via the **Python** job in `.github/workflows/ci.yml` (and the same commands locally; see [`docs/local-ci.md`](../local-ci.md)).
- Future services (e.g. HTTP server for `/api/v1/trigger`) are implemented in Python unless a new ADR chooses otherwise.
- Any other language prototypes must not live alongside the published Python package under `helm/src/` without a superseding ADR.
