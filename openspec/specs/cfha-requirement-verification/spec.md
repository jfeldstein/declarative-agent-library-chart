## ADDED Requirements

### Requirement: [CFHA-VER-001] Normative requirements carry stable identifiers

Every **normative** requirement block in each **`openspec/specs/<capability>/spec.md`** file SHALL include a **stable identifier** that is **unique within that spec file**, formatted as **`[CFHA-REQ-<CAPABILITY>-<NNN>]`** embedded in the requirement heading **or** as the first line of the requirement body immediately after the heading, where **`<CAPABILITY>`** is a short uppercase slug derived from the capability folder name (for example **`RUNTIME-MCP`** for `runtime-tools-mcp` once promoted) and **`<NNN>`** is a three-digit decimal number. New requirements SHALL receive new IDs; retired IDs SHALL not be reused.

#### Scenario: Promoted spec requirement is identifiable

- **WHEN** a reader opens any `openspec/specs/*/spec.md` file
- **THEN** each `### Requirement:` section SHALL be matchable to exactly one ID string that satisfies the format above

### Requirement: [CFHA-VER-002] Tests explicitly claim which requirements they evidence

For **Python** tests under **`runtime/tests/`**, each test function **or** its enclosing class docstring SHALL list, in plain text, the **requirement ID(s)** it is intended to satisfy for **promoted** specs. For **Helm unittest** suites under **`examples/*/tests/`**, each test case (`it:`) **or** suite comment SHALL list the same IDs where the test evidences a **SHALL** in **`openspec/specs/`** or in a **change-local** spec explicitly referenced by the matrix for that release.

#### Scenario: Pytest evidence references IDs

- **WHEN** a maintainer adds or changes a test that is the **primary** evidence for a promoted requirement
- **THEN** that test SHALL include the requirement’s **ID string** in a docstring visible to reviewers and to automated checks

#### Scenario: Helm unittest evidence references IDs

- **WHEN** a maintainer adds or changes a helm unittest that evidences a chart-level **SHALL**
- **THEN** the suite or `it:` entry SHALL include the requirement’s **ID string** in a comment or description field supported by the test file format

### Requirement: [CFHA-VER-003] Traceability matrix is the authoritative requirement-to-test map

The repository SHALL contain a committed **traceability matrix** document (path chosen in implementation, documented in **`AGENTS.md`**) that lists, at minimum, for each **requirement ID** defined in **`openspec/specs/`**: the **spec file path**, and **one or more** test evidences (pytest node id, script name, or helm unittest reference) that the project accepts as satisfying that requirement on **default PR CI** or on a **documented tier** (see **[CFHA-VER-004]**).

#### Scenario: Matrix lists all promoted requirement IDs

- **WHEN** a new requirement ID is added to any `openspec/specs/*/spec.md`
- **THEN** the traceability matrix SHALL be updated in the **same** change to include that ID and its evidences, or the change SHALL add a **waived** row with **Reason** and **owner** until evidences land (not to exceed one release cycle without resolution)

### Requirement: [CFHA-VER-004] CI documents test tiers and runs traceability checks

**Default PR** automation (for example **`ci.sh`** invoked in CI) SHALL run a **traceability check** that fails with a non-zero exit code when promoted spec requirements lack IDs or when the matrix is **inconsistent** with the rules defined in implementation (for example missing rows for IDs, or evidences pointing to non-existent tests). The project SHALL document **test tiers**: **default PR**, **opt-in integration** (environment-gated), and **scheduled** or **manual** jobs, including what runs where, so contributors understand which **SHALL** clauses are enforced on every push versus on a schedule.

#### Scenario: Traceability check runs on default PR path

- **WHEN** CI runs the default pull-request script without optional integration flags
- **THEN** the traceability check SHALL execute and SHALL fail if promoted requirements violate **[CFHA-VER-001]** or **[CFHA-VER-003]** per the implemented rules

#### Scenario: Scheduled jobs are documented

- **WHEN** a maintainer reads the traceability or CI documentation added for this capability
- **THEN** they SHALL find an explanation of **scheduled** (for example nightly) versus **default PR** integration tests and which requirements those tiers evidence

### Requirement: [CFHA-VER-005] Agent and human contributor rules reference traceability

The repository SHALL include **`AGENTS.md`** (or equivalent top-level contributor contract) stating that changes which add or materially alter a **SHALL** in **`openspec/specs/`** MUST update **tests**, the **traceability matrix**, and **requirement IDs** in the same logical change unless explicitly waived with **Reason**. Agent-facing rules (for example **Cursor rules** under **`.cursor/rules/`**) SHALL repeat the same obligation in concise form.

#### Scenario: New contributor finds the rule

- **WHEN** an agent or human opens **`AGENTS.md`** before submitting a spec change
- **THEN** they SHALL see the obligation to keep specs, IDs, tests, and the matrix aligned
