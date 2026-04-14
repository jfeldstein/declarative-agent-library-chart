# ADR 0003: Spec–test traceability (requirement IDs, matrix, waivers)

<!-- Traceability: [DALC-VER-003] — normative description of docs/spec-test-traceability.md -->

## Status

Accepted

## Context

Normative **SHALL** requirements live in OpenSpec under `openspec/specs/`. Reviewers and automation need **stable IDs**, a **single matrix** from each requirement to accepted evidence, **bidirectional** hints (spec ↔ test), and a **machine-checkable** notion of **waived** requirements when evidence is intentionally deferred.

## Decision

### 1. IDs on promoted requirements

- Heading form: **`### Requirement: [<ID>] <title>`** with the bracketed ID **on the same line** as `### Requirement:` (see **[DALC-VER-001]**).
- Capability requirements: **`[DALC-REQ-<CAPABILITY-SLUG>-<NNN>]`**; verification meta-requirements: **`[DALC-VER-<NNN>]`**.

### 2. Matrix as source of truth

- Path: **`docs/spec-test-traceability.md`**.
- Columns: **ID | Spec | Evidence | CI tier | Waiver approver | Waiver reason**.
- Parsed by **`scripts/check_spec_traceability.py`**; keep the **Matrix** table format stable.

### 3. Waivers (human approval required)

- **Active** row: **Waiver approver** and **Waiver reason** are **`-`** or empty.
- **Waived** row: **both** columns MUST be set. **Waiver approver** MUST be the **GitHub username** of a maintainer who **explicitly approved** the waiver (e.g. PR review). Placeholder values (e.g. `pending`, `todo`) are invalid.
- **Waiver reason** MUST be at least ~10 characters and explain the deferral.
- Waived rows MAY use **`-`** as the only **Evidence** cell token until evidence lands; the checker skips path and annotation checks for that row.

**Policy:** Agents MUST NOT add or alter waiver columns without a maintainer’s explicit approval in the same PR.

### 4. Tests citing specs

- **Pytest:** Matrix may use **`file.py::test_name`**; then the ID MUST appear in **that function’s** docstring. A bare **`file.py`** allows the ID in any module/class/function docstring (see **[DALC-VER-002]**).
- **Helm unittest:** IDs in **`#` comments** (suite or `it:`-adjacent preferred).

### 5. Local vs CI

- Default PR CI runs **`python3 scripts/check_spec_traceability.py`** (see **`.github/workflows/ci.yml`**). **`DALC_TRACEABILITY_STRICT=0`** disables content checks temporarily; paths must still exist for active rows. **`CFHA_TRACEABILITY_STRICT`** is a deprecated alias (stderr warning).

## Consequences

- Adding a requirement usually touches spec heading, matrix row, and evidence annotations together—or a **waived** row with approver + reason.
- Waivers are auditable (who approved, why).

## See also

- **Matrix:** [docs/spec-test-traceability.md](../spec-test-traceability.md)
- **Checker:** `scripts/check_spec_traceability.py`
- **Contributor notes:** [docs/AGENTS.md](../AGENTS.md)
