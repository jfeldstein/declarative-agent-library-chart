# Agent and contributor contract

## OpenSpec test-to-spec traceability ([CFHA-VER-005])

**Test-to-spec traceability** means: promoted **`openspec/specs/*/spec.md`** **SHALL** rows carry stable IDs, **`docs/spec-test-traceability.md`** lists evidence, and tests cite those IDs—see **`openspec/specs/cfha-requirement-verification/spec.md`**. Use this phrase (or **spec–test traceability**) when you mean this mechanism; bare **traceability** is ambiguous (e.g. data lineage, supply chain).

When you add or materially change a normative **SHALL** under `openspec/specs/*/spec.md`:

1. Assign or preserve a stable bracketed ID on the `### Requirement:` heading: `[CFHA-REQ-<SLUG>-<NNN>]` or `[CFHA-VER-<NNN>]` for verification meta-requirements, per `openspec/specs/cfha-requirement-verification/spec.md`.
2. Update **`docs/spec-test-traceability.md`** in the same change with a row for that ID (spec path, evidence paths, CI tier), unless you add an explicit **waived** row with reason and owner.
3. Update **tests** that evidence the requirement: add the same ID string to the **pytest docstring** or **helm unittest YAML comment** where those tests are listed as evidence (see `scripts/check_spec_traceability.py`).
4. Run **`python3 scripts/check_spec_traceability.py`** before merge (also runs in CI per **`.github/workflows/ci.yml`**).

**Conventions and cross-linking (spec ↔ test):** read **[ADR 0003](docs/adrs/0003-spec-test-traceability.md)**. **CI tier semantics** and the **matrix table** live in **`docs/spec-test-traceability.md`**.
