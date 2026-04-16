# Agent notes (declarative-agent-library-chart)

Concise orientation for automated assistants working in this repository.

## Layout

| Path | Role |
|------|------|
| `helm/src/hosted_agents/` | FastAPI app, LangGraph trigger pipeline, RAG, scrapers (Python package root) |
| `helm/src/tests/` | Pytest (coverage floor enforced in CI) |
| `helm/chart/` | Declarative Agent Library Helm chart |
| `examples/*/` | Application charts that depend on the library chart |
| `helm/tests/` | Helm unittest suites (`*_test.yaml`) loaded with each example’s `values.yaml` |
| `docs/adrs/` | Architecture Decision Records (`NNNN-slug.md`) |
| `docs/development-log.md` | Human changelog-style notes for notable changes |
| `.github/workflows/ci.yml` | GitHub Actions (Python, Helm, ADR, spec traceability) |
| `docs/spec-test-traceability.md` | Test-to-spec matrix: requirement → evidence (parsed in CI) |
| `docs/adrs/0003-spec-test-traceability.md` | Test-to-spec rules, waivers, pytest `::` convention |

## OpenSpec test-to-spec traceability ([DALC-VER-005])

**Test-to-spec traceability** is the ID + matrix + pytest/Helm citation practice for **promoted** `openspec/specs/` (see **[DALC-VER-001]**). Prefer that term over bare **traceability**.

When you add or change a normative **SHALL** under `openspec/specs/*/spec.md`:

1. Put **`[DALC-REQ-…]`** or **`[DALC-VER-…]`** on the **same line** as **`### Requirement:`** (see **[DALC-VER-001]** / [ADR 0003](adrs/0003-spec-test-traceability.md)).
2. Update **`docs/spec-test-traceability.md`** with a matrix row (spec path, evidence paths, CI tier, waiver columns). **Waivers** need an approving maintainer **GitHub username** and **reason**; do not add waivers without explicit human approval.
3. Add the same ID to **pytest** docstrings (use **`file.py::test_name`** in the matrix when one test maps to one requirement) or **Helm unittest** `#` comments.
4. Run **`python3 scripts/check_spec_traceability.py`** from the repo root (also runs in CI).

## Commands

From the repo root:

- **CI parity:** follow [docs/local-ci.md](local-ci.md) (Python via **uv**, Helm via **helm** + **ct** + **helm-unittest**, ADRs via `scripts/check_adr_numbers.sh`, spec traceability via `scripts/check_spec_traceability.py`). GitHub runs the same stages in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).
- **Python only:** `uv sync --all-groups --project helm/src` then `cd helm/src` and `uv run ruff format --check hosted_agents tests`, `uv run ruff check hosted_agents tests`, `uv run complexipy`, `uv run pytest tests/ -v --tb=short`

## ADR numbering

New ADRs live under `docs/adrs/` as `NNNN-short-title.md` (four digits, hyphen, kebab-case slug). Copy the boilerplate from `docs/adrs/0000-topic.md`.

**Avoid collisions:** each `NNNN` must appear on exactly one ADR file. Before adding a file, list `docs/adrs/[0-9][0-9][0-9][0-9]-*.md` and choose the next unused integer (typically max existing + 1). Do not reuse a number after rename or supersede; keep the file and cross-link per `docs/adrs/README.md`.

CI runs `scripts/check_adr_numbers.sh` to fail duplicate numbers.

## Scope

Prefer small, task-focused changes; match existing style and patterns. Do not expand Helm or runtime behavior unless the task requires it.
