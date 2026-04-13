# Architecture Decision Records (config-first-hosted-agents)

Decisions that should not drift without an explicit new ADR are recorded here.

## File naming

Use zero-padded sequence plus a short **kebab-case** slug:

`NNNN-short-title.md`

- **`0000-topic.md`** is the boilerplate to copy when adding a new ADR (see heading instructions inside that file).
- Numbered decisions start at **0001** and increase (e.g. `0001-use-python-for-runtime.md`, `0002-enforce-85-percent-test-coverage.md`, `0003-spec-test-traceability.md`).

The number increments for each new decision; do not reuse numbers. Superseded ADRs stay in place; add a **Supersedes** / **Superseded by** note in the affected files.

Before adding a new ADR, pick the next unused `NNNN` (e.g. one greater than the highest existing number in this directory) so filenames stay unique. CI runs [`scripts/check_adr_numbers.sh`](../../scripts/check_adr_numbers.sh) to fail the build on duplicate numbers.

## Template

New ADRs can follow the structure in `0001-use-python-for-runtime.md` (Context, Decision, Consequences).
