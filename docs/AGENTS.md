# Agent notes (declarative-agent-library-chart)

Concise orientation for automated assistants working in this repository.

## Layout

| Path | Role |
|------|------|
| `runtime/src/hosted_agents/` | FastAPI app, LangGraph trigger pipeline, RAG, scrapers |
| `runtime/tests/` | Pytest (coverage floor enforced in CI) |
| `helm/chart/` | Declarative Agent Library Helm chart |
| `examples/*/` | Application charts that depend on the library chart |
| `docs/adrs/` | Architecture Decision Records (`NNNN-slug.md`) |
| `docs/development-log.md` | Human changelog-style notes for notable changes |
| `.github/workflows/ci.yml` | GitHub Actions (Python, Helm, ADR checks) |

## Commands

From the repo root:

- **CI parity:** follow the “Local CI” section in [README.md](../README.md) (Python via **uv**, Helm via **helm** + **ct** + **helm-unittest**, ADRs via `scripts/check_adr_numbers.sh`). GitHub runs the same stages in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).
- **Python only:** `uv sync --all-groups --project runtime` then `cd runtime` and `uv run ruff check src tests`, `uv run pytest tests/ -v --tb=short`

## ADR numbering

New ADRs live under `docs/adrs/` as `NNNN-short-title.md` (four digits, hyphen, kebab-case slug). Copy the boilerplate from `docs/adrs/0000-topic.md`.

**Avoid collisions:** each `NNNN` must appear on exactly one ADR file. Before adding a file, list `docs/adrs/[0-9][0-9][0-9][0-9]-*.md` and choose the next unused integer (typically max existing + 1). Do not reuse a number after rename or supersede; keep the file and cross-link per `docs/adrs/README.md`.

CI runs `scripts/check_adr_numbers.sh` to fail duplicate numbers.

## Scope

Prefer small, task-focused changes; match existing style and patterns. Do not expand Helm or runtime behavior unless the task requires it.
