# Agent and contributor contract

## Worktrees

If you are starting a new body of work, create a new worktree for it. Read the parallel-agents-in-local-worktrees skill (at one of ~/.claude/skills, ~/.cursor/skills, .claude/skills, or .cursor/skills).

## OpenSpec test-to-spec traceability ([DALC-VER-005])

For OpenSpec **change workflow**—drafts under `openspec/changes/`, **promotion** of normative requirements into `openspec/specs/`, and **archiving** completed changes—read **[openspec/AGENTS.md](openspec/AGENTS.md)**.

**Test-to-spec traceability** means: promoted **`openspec/specs/*/spec.md`** **SHALL** rows carry stable IDs, **`docs/spec-test-traceability.md`** lists evidence, and tests cite those IDs—see **`openspec/specs/dalc-requirement-verification/spec.md`**. Use this phrase (or **spec–test traceability**) when you mean this mechanism; bare **traceability** is ambiguous (e.g. data lineage, supply chain).

When you add or materially change a normative **SHALL** under `openspec/specs/*/spec.md`:

1. Assign or preserve a stable bracketed ID on the `### Requirement:` heading: `[DALC-REQ-<SLUG>-<NNN>]` or `[DALC-VER-<NNN>]` for verification meta-requirements, per `openspec/specs/dalc-requirement-verification/spec.md`.
2. Update **`docs/spec-test-traceability.md`** in the same change with a row for that ID (spec path, evidence paths, CI tier), unless you add an explicit **waived** row with reason and owner.
3. Update **tests** that evidence the requirement: add the same ID string to the **pytest docstring** or **helm unittest YAML comment** where those tests are listed as evidence (see `scripts/check_spec_traceability.py`).
4. Run **`python3 scripts/check_spec_traceability.py`** before merge (also runs in CI per **`.github/workflows/ci.yml`**).

**Conventions and cross-linking (spec ↔ test):** read **[ADR 0003](docs/adrs/0003-spec-test-traceability.md)**. **CI tier semantics** and the **matrix table** live in **`docs/spec-test-traceability.md`**.

**Helm unittest locally:** **`helm/tests/*_test.yaml`** is exercised from each chart under **`examples/`** after **`helm dependency build`** (same shell loop as the **Helm** job in **`.github/workflows/ci.yml`**), not by running **`helm unittest`** against **`helm/chart`** alone — see **`docs/AGENTS.md`** (Commands).
