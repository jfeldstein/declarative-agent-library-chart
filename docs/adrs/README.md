# Architecture Decision Records (config-first-hosted-agents)

Decisions that should not drift without an explicit new ADR are recorded here.

## File naming

Use zero-padded sequence plus a short **kebab-case** slug:

`NNNN-short-title.md`

- **`0000-topic.md`** is the boilerplate to copy when adding a new ADR (see heading instructions inside that file).
- Numbered decisions start at **0001** and increase (for example `0001-use-python-for-runtime.md` through `0012-ci-parity-as-merge-gate.md`).

The number increments for each new decision; do not reuse numbers. Superseded ADRs stay in place; add a **Supersedes** / **Superseded by** note in the affected files.

Before adding a new ADR, pick the next unused `NNNN` (e.g. one greater than the highest existing number in this directory) so filenames stay unique. CI runs [`scripts/check_adr_numbers.sh`](../../scripts/check_adr_numbers.sh) to fail the build on duplicate numbers.

## Template

New ADRs can follow the structure in `0001-use-python-for-runtime.md` (Context, Decision, Consequences).

## Index

- **0001 — [Use Python for the runtime](0001-use-python-for-runtime.md)** — Python + `uv` under `helm/src/`.
- **0002 — [85% line coverage](0002-enforce-85-percent-test-coverage.md)** — pytest-cov floor for `hosted_agents`.
- **0003 — [Spec–test traceability](0003-spec-test-traceability.md)** — requirement IDs, matrix vs tests, spec ↔ test cross-links (`docs/spec-test-traceability.md`).
- **0004 — [ATIF v1.4 export pin](0004-pin-atif-v1-4-trajectory-export.md)** — Harbor ATIF interchange and internal canonical adapter.
- **0005 — [Observability metrics vs execution persistence](0005-observability-vs-execution-persistence.md)** — terminology split for specs and docs.
- **0006 — [Config surface during alpha](0006-config-surface-alpha-breaking-changes.md)** — Helm/env may break without deprecation until a stability ADR.
- **0007 — [Feature lifecycle policy](0007-feature-lifecycle-policy.md)** — OpenSpec stages, artifacts, supersede/removal discipline.
- **0008 — [Persistence backend strategy](0008-persistence-backend-strategy.md)** — memory for tests/dev; durable stores for production-like execution persistence.
- **0009 — [Scraper job contract](0009-scraper-job-contract-standard.md)** — CronJob + `job.json`, RAG embed, scraper metrics.
- **0010 — [Trigger contract](0010-trigger-contract-standard.md)** — `POST /api/v1/trigger` and inbound `*-trigger` bridges vs scrapers/tools.
- **0011 — [Prometheus metrics schema and cardinality](0011-prometheus-metrics-schema-and-cardinality.md)** — naming, labels, scraper registry separation.
- **0012 — [CI parity as merge gate](0012-ci-parity-as-merge-gate.md)** — local parity with `.github/workflows/ci.yml`.
