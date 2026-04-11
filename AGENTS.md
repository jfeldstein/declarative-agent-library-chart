# Agent and contributor contract

## OpenSpec traceability ([CFHA-VER-005])

When you add or materially change a normative **SHALL** under `openspec/specs/*/spec.md`:

1. Assign or preserve a stable bracketed ID on the `### Requirement:` heading: `[CFHA-REQ-<SLUG>-<NNN>]` or `[CFHA-VER-<NNN>]` for verification meta-requirements, per `openspec/specs/cfha-requirement-verification/spec.md`.
2. Update **`docs/spec-test-traceability.md`** in the same change with a row for that ID (spec path, evidence paths, CI tier), unless you add an explicit **waived** row with reason and owner.
3. Update **tests** that evidence the requirement: add the same ID string to the **pytest docstring** or **helm unittest YAML comment** where those tests are listed as evidence (see `scripts/check_spec_traceability.py`).
4. Run **`./ci.sh`** before merge; it includes the traceability gate.

For CI tier semantics (default PR vs opt-in vs scheduled), see **`docs/spec-test-traceability.md`**.
