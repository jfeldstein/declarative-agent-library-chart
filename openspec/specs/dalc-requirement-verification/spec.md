## Reader note (non-normative)

Contributor docs and OpenSpec changes may use **test-to-spec traceability** as shorthand for the obligations in this file (IDs on promoted requirements, matrix rows, pytest/Helm citations). The English word **traceability** alone is overloaded; prefer **test-to-spec** when you mean this repository’s spec↔test gate.

## ADDED Requirements

### Requirement: [DALC-VER-001] Normative requirements carry stable identifiers

Every **normative** requirement block in each **`openspec/specs/<capability>/spec.md`** file SHALL include a **stable identifier** that is **unique within that spec file**, formatted as **`[DALC-REQ-<CAPABILITY>-<NNN>]`** or **`[DALC-VER-<NNN>]`** on the **same line** as the **`### Requirement:`** Markdown heading (heading form **`### Requirement: [<ID>] <title>`**). The ID SHALL NOT be placed only on a following line. **`<CAPABILITY>`** is a short uppercase slug derived from the capability folder name (for example **`HELM-UNITTEST`** for `dalc-helm-unittest`) and **`<NNN>`** is a three-digit decimal number. New requirements SHALL receive new IDs; retired IDs SHALL not be reused.

#### Scenario: Promoted spec requirement is identifiable

- **WHEN** a reader opens any `openspec/specs/*/spec.md` file
- **THEN** each `### Requirement:` line SHALL include exactly one bracketed ID that satisfies the format above

### Requirement: [DALC-VER-002] Tests explicitly claim which requirements they evidence

For **Python** tests under **`runtime/tests/`**: when the traceability matrix lists evidence as **`path.py::test_function`**, that **test function’s** docstring SHALL contain the **requirement ID** string. When the matrix lists only **`path.py`**, the ID SHALL appear in the **module, class, or any test function** docstring in that file. For **Helm unittest** suites under **`examples/*/tests/`**, the ID SHALL appear in a **`#` comment** on the suite or on the relevant **`it:`** block; a single top-of-file **`# Traceability:`** line is acceptable when one file evidences many requirements, but **prefer** a comment adjacent to the **`it:`** when one case maps to one requirement.

#### Scenario: Pytest evidence references IDs

- **WHEN** a maintainer adds or changes a test that is the **primary** evidence for a promoted requirement
- **THEN** that test SHALL include the requirement’s **ID string** in the scope defined above so reviewers and automated checks can see the linkage

#### Scenario: Helm unittest evidence references IDs

- **WHEN** a maintainer adds or changes a helm unittest that evidences a chart-level **SHALL**
- **THEN** the suite or `it:` entry SHALL include the requirement’s **ID string** in a comment as above

### Requirement: [DALC-VER-003] Traceability matrix is the authoritative requirement-to-test map

The repository SHALL contain a committed **traceability matrix** document (path **`docs/spec-test-traceability.md`**, documented in **`docs/AGENTS.md`**) with columns **ID**, **Spec**, **Evidence**, **CI tier**, **Waiver approver**, **Waiver reason**. For each **requirement ID** in **`openspec/specs/`**, there SHALL be exactly one row. **Active** rows SHALL use **`-`** or leave empty both waiver columns; **waived** rows SHALL set **both** columns: **Waiver approver** SHALL be the approving maintainer’s **GitHub username** (human, explicit approval—typically via PR review), and **Waiver reason** SHALL explain the deferral. Waived rows MAY use **`-`** as the sole **Evidence** token to skip file-backed evidence until resolved.

#### Scenario: Matrix lists all promoted requirement IDs

- **WHEN** a new requirement ID is added to any `openspec/specs/*/spec.md`
- **THEN** the traceability matrix SHALL be updated in the **same** change to include that ID, or the change SHALL add a **waived** row with **approver** and **reason** per the rules above (resolve within one release cycle)

### Requirement: [DALC-VER-004] CI documents test tiers and runs traceability checks

**Default PR** automation (for example **`.github/workflows/ci.yml`** on pull requests) SHALL run a **traceability check** that fails with a non-zero exit code when promoted spec requirements violate **[DALC-VER-001]** or **[DALC-VER-003]** per **`scripts/check_spec_traceability.py`**. The project SHALL document **test tiers**: **default PR**, **opt-in integration** (environment-gated), and **scheduled** or **manual** jobs, including what runs where, so contributors understand which **SHALL** clauses are enforced on every push versus on a schedule.

#### Scenario: Traceability check runs on default PR path

- **WHEN** CI runs the default pull-request workflow without optional integration flags
- **THEN** the traceability check SHALL execute and SHALL fail if promoted requirements violate **[DALC-VER-001]** or **[DALC-VER-003]** per the implemented rules

#### Scenario: Scheduled jobs are documented

- **WHEN** a maintainer reads the traceability or CI documentation added for this capability
- **THEN** they SHALL find an explanation of **scheduled** (for example nightly) versus **default PR** integration tests and which requirements those tiers evidence

### Requirement: [DALC-VER-005] Agent and human contributor rules reference traceability

The repository SHALL include **`docs/AGENTS.md`** (or equivalent top-level contributor contract) stating that changes which add or materially alter a **SHALL** in **`openspec/specs/`** MUST update **tests**, the **traceability matrix**, and **requirement IDs** in the same logical change unless an explicitly **approved waiver** row is used. Agent-facing rules (for example **Cursor rules** under **`.cursor/rules/`**) SHALL repeat the same obligation in concise form.

#### Scenario: New contributor finds the rule

- **WHEN** an agent or human opens **`docs/AGENTS.md`** before submitting a spec change
- **THEN** they SHALL see the obligation to keep specs, IDs, tests, and the matrix aligned
