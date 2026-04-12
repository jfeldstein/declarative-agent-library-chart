## 1. Spec deltas and ID backfill (promoted specs)

- [ ] 1.1 Add **`[CFHA-REQ-…]`** IDs to every `### Requirement:` block under **`openspec/specs/**/*.spec.md`**, using capability-specific slugs per **[CFHA-VER-001]** (see `cfha-requirement-verification` spec).
- [ ] 1.2 Port the **`runtime-tools-mcp`** **MODIFIED** text from `openspec/changes/traceability/specs/runtime-tools-mcp/spec.md` into **`openspec/changes/agent-runtime-components/specs/runtime-tools-mcp/spec.md`** (or the canonical location used until archive) so active work does not diverge.
- [ ] 1.3 Update **`openspec/specs/cfha-agent-o11y-scrape/spec.md`** (and any other file) that **references** “MCP contract” or **`runtime-tools-mcp`** wording if needed so cross-links stay consistent with the relaxed exposure language.

## 2. Traceability matrix and test annotations

- [ ] 2.1 Create **`docs/spec-test-traceability.md`** (or path chosen in design) with columns **ID | Spec | Evidence | CI tier**, and populate **one row per** promoted requirement ID.
- [ ] 2.2 Add requirement ID references to **pytest** tests under **`runtime/tests/`** (docstrings) for rows that claim Python evidence.
- [ ] 2.3 Add requirement ID references to **helm unittest** YAML under **`examples/*/tests/`** where those tests evidence chart **SHALL** clauses.

## 3. CI traceability gate

- [ ] 3.1 Implement **`scripts/check_spec_traceability.py`** (or shell equivalent) per **design §3**: validate ID presence on promoted specs, matrix completeness, and that evidence paths/tests exist.
- [ ] 3.2 Wire the script into **`ci.sh`** after the main test stages; print actionable errors on failure.
- [ ] 3.3 If the first slice is too strict, gate **strict mode** behind an env var only long enough to backfill, then make strict the default (document in script header).

## 4. Contributor and agent rules

- [ ] 4.1 Add or update **`AGENTS.md`** with obligations from **[CFHA-VER-005]** (specs + IDs + matrix + tests).
- [ ] 4.2 Add a **`.cursor/rules`** entry (for example **`spec-traceability.mdc`**) summarizing the same for agentic edits.

## 5. Integration tiers (documentation + optional automation)

- [ ] 5.1 Document **default PR / opt-in / scheduled / manual** tiers in **`docs/spec-test-traceability.md`** or **`README.md`** (per **[CFHA-VER-004]**), including **`RUN_KIND_O11Y_INTEGRATION`** and **`helm test`** hook behavior.
- [ ] 5.2 If the repo uses **GitHub Actions**, add a **scheduled** workflow (cron) that runs **`RUN_KIND_O11Y_INTEGRATION=1`** (or the shell script) on **`main`**; otherwise add a short **“Suggested CI”** snippet to **`docs/`** for operators.

## 6. Verification

- [ ] 6.1 Run **`ci.sh`** end-to-end locally (with Helm toolchain where applicable) and fix any traceability or test drift until green.
- [ ] 6.2 Run **`openspec validate traceability`** (or project equivalent) if available, and resolve validation issues.
