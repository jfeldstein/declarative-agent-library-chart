# ADR 0002: Enforce minimum 85% line coverage on Python code

## Status

Accepted

## Context

The runtime will grow (HTTP adapters, tool integrations, config parsing). We want fast feedback and a floor on untested code so refactors stay safe.

## Decision

Python tests **SHALL** run with **pytest-cov** measuring the `hosted_agents` package. Total line coverage **SHALL** be **at least 85%**, enforced with `--cov-fail-under=85` in project CI (`ci.sh` and local `pytest` invocations used for verification).

Coverage configuration lives in `runtime/pyproject.toml` under `[tool.coverage.*]`. Omitted paths (e.g. virtualenvs) are explicit there.

## Consequences

- Pull requests that touch this project and drop coverage below the threshold fail CI.
- New modules require tests (or justified `pragma: no cover` only where appropriate).
- The monorepo CI dispatch pattern documents this as the recommended approach for Python projects using coverage gates.
