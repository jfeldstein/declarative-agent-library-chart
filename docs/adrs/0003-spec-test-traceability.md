# ADR 0003: Spec–test traceability (requirement IDs, matrix, and cross-links)

<!-- Traceability: [CFHA-VER-003] — normative description of the matrix in docs/spec-test-traceability.md -->

## Status

Accepted

## Context

Normative **SHALL** requirements live in OpenSpec under `openspec/specs/`, but reviewers and CI need a **stable ID**, a **single map** from each requirement to accepted test evidence, and **bidirectional** hints so humans and agents can navigate spec ↔ test without spelunking. This ADR locks the identifier shapes, where they appear, how specs and tests reference each other, and how contributors (including agents) keep the system consistent.

## Decision

### 1. IDs for specs (promoted requirements)

- Every normative block under `openspec/specs/<capability>/spec.md` uses a heading of the form  
  `### Requirement: [<ID>] <title>`  
  where **the ID is on the same line** as `### Requirement:`.
- **Capability requirements** use  
  **`[CFHA-REQ-<CAPABILITY-SLUG>-<NNN>]`**  
  with `<CAPABILITY-SLUG>` a short uppercase kebab slug derived from the folder name (for example `HELM-UNITTEST` for `cfha-helm-unittest`), and `<NNN>` a three-digit decimal sequence **unique within that spec file**. New obligations get new numbers; **do not reuse** retired IDs.
- **Verification / process requirements** (how we enforce traceability itself) use  
  **`[CFHA-VER-<NNN>]`**  
  as defined in `openspec/specs/cfha-requirement-verification/spec.md`.
- Change-local specs under `openspec/changes/.../specs/` SHOULD follow the same bracket convention when they contain `### Requirement:` blocks, so archive moves do not require ID rewrites.

### 2. IDs for tests (no separate test-ID namespace)

- **Tests do not get a second ID family** (no `CFHA-TEST-…`). They **cite one or more requirement IDs** that they are intended to satisfy.
- The **authoritative list** of which tests (or other artifacts) evidence which requirement is the **matrix** (see below), not the docstring alone.
- Docstrings and comments exist so **reviewers and strict CI** can see intent **at the test site** without opening only the matrix.

### 3. Cross-linking format

**Spec → tests (and other evidence)**

- The **authoritative** spec → evidence map is the committed matrix in **`docs/spec-test-traceability.md`**: one table row per promoted `[CFHA-REQ-…]` / `[CFHA-VER-…]` ID with columns **ID | Spec | Evidence | CI tier**.
- **Evidence** is a comma-separated list of repository-relative paths. Optional **pytest node** precision uses  
  **`runtime/tests/<file>.py::<test_function>`**  
  (the checker resolves the path to the file; the `::` suffix is informational for humans).
- Spec prose **MAY** mention test paths in narrative, but the **matrix row MUST exist** for every promoted ID so CI can parse one artifact.

**Tests → specs**

- **Pytest** (`runtime/tests/**/*.py`): include the **exact bracketed ID** (for example `[CFHA-REQ-O11Y-SCRAPE-001]`) in the **test function docstring**, the **class docstring**, or the **module docstring** when that test is primary evidence for that requirement. Prefer the **narrowest** scope (function > class > module).
- **Helm unittest** (`examples/*/tests/**/*.yaml`): include the same bracketed IDs in a **`#` comment** on the suite or on the relevant `it:` block (or a short `# Traceability: [ID1] [ID2]` line at the top when one file evidences many rows).
- **Scripts, CI, config, JSON, Markdown** used as evidence: use a **`#` comment**, **`<!-- … -->`**, or an agreed **title/description field** so the bracketed ID appears in plain text (for example dashboard `title` suffix). This keeps `scripts/check_spec_traceability.py` and humans aligned.

### 4. Agent and maintainer playbook

**On every change that adds or materially edits a SHALL in `openspec/specs/`:**

1. Keep or assign a **stable bracketed ID** on the requirement heading (per section 1).
2. Add or update the **matrix row** in `docs/spec-test-traceability.md` (spec path, evidence paths, CI tier). If evidence is not ready, add an explicit **waived** row with reason and owner (resolve within one release cycle).
3. Update **tests or artifacts** listed as evidence so each listed **Python or Helm unittest file** contains the **same bracketed ID** in a docstring or comment (strict default in CI).
4. Run **`./ci.sh`** (or at minimum `python3 scripts/check_spec_traceability.py` from the repo root) before merge.

**Occasional validation (agents and humans):**

- Treat **`python3 scripts/check_spec_traceability.py`** as the source of mechanical truth: promoted specs have IDs, the matrix lists every ID, evidence paths exist, and (unless `CFHA_TRACEABILITY_STRICT=0`) pytest and helm unittest evidence files contain the row’s ID string.
- **Spot-check** after large refactors: pick a requirement ID from `openspec/specs/`, confirm its matrix row, open each evidence path, and confirm the ID appears there. Reverse direction: when editing a test that claims an ID, confirm the matrix still lists that test for that ID.
- Re-run full **`./ci.sh`** periodically on a clean tree so Helm and Python gates stay green together.

**CI tiers** (default PR vs opt-in vs scheduled vs manual) are documented in the matrix doc’s **CI tiers** section; they are part of how **[CFHA-VER-004]** is satisfied.

## Consequences

**Positive:** One greppable ID space; one parseable matrix; spec ↔ test navigation is explicit; agents have a single ADR to read for rules.

**Negative / trade-offs:** Adding a requirement touches spec + matrix + tests in one change; renaming files requires updating matrix evidence columns.

**Follow-ups:** If the matrix grows unwieldy, split by domain (for example Helm-only sibling matrix) with a short ADR amendment and checker updates.

## See also

- **Living matrix and tier table:** [docs/spec-test-traceability.md](../spec-test-traceability.md)
- **Checker implementation:** `scripts/check_spec_traceability.py`
- **Contributor contract:** `AGENTS.md`, `.cursor/rules/spec-traceability.mdc`
- **Normative verification capability:** `openspec/specs/cfha-requirement-verification/spec.md`
