## 1. Spec deltas and ID backfill (promoted specs)

- [x] 1.1 Add **`[DALC-REQ-…]`** IDs to every `### Requirement:` block under **`openspec/specs/**/*.spec.md`**, using capability-specific slugs per **[DALC-VER-001]** (see `dalc-requirement-verification` spec).
- [x] 1.2 Port the **`runtime-tools-mcp`** **MODIFIED** text from `openspec/changes/traceability/specs/runtime-tools-mcp/spec.md` into **`openspec/changes/agent-runtime-components/specs/runtime-tools-mcp/spec.md`** (or the canonical location used until archive) so active work does not diverge.
- [x] 1.3 Update **`openspec/specs/dalc-agent-o11y-scrape/spec.md`** (and any other file) that **references** “MCP contract” or **`runtime-tools-mcp`** wording if needed so cross-links stay consistent with the relaxed exposure language.

## 2. Traceability matrix and test annotations

- [x] 2.1 Create **`docs/spec-test-traceability.md`** (or path chosen in design) with columns **ID | Spec | Evidence | CI tier**, and populate **one row per** promoted requirement ID.
- [x] 2.2 Add requirement ID references to **pytest** tests under **`helm/src/tests/`** (docstrings) for rows that claim Python evidence.
- [x] 2.3 Add requirement ID references to **helm unittest** YAML under **`helm/tests/`** where those tests evidence chart **SHALL** clauses.

## 3. CI traceability gate

- [x] 3.1 Implement **`scripts/check_spec_traceability.py`** (or shell equivalent) per **design §3**: validate ID presence on promoted specs, matrix completeness, and that evidence paths/tests exist.
- [x] 3.2 Wire the script into **`.github/workflows/ci.yml`** (for example a `traceability` job or post-test step) after the main test stages; print actionable errors on failure.
- [x] 3.3 If the first slice is too strict, gate **strict mode** behind an env var only long enough to backfill, then make strict the default (document in script header).

## 4. Contributor and agent rules

- [x] 4.1 Add or update **`AGENTS.md`** with obligations from **[DALC-VER-005]** (specs + IDs + matrix + tests).
- [x] 4.2 Add a **`.cursor/rules`** entry (for example **`spec-traceability.mdc`**) summarizing the same for agentic edits.

## 5. Integration tiers (documentation + optional automation)

- [x] 5.1 Document **default PR / opt-in / scheduled / manual** tiers in **`docs/spec-test-traceability.md`** or **`README.md`** (per **[DALC-VER-004]**), including **`RUN_KIND_O11Y_INTEGRATION`** and **`helm test`** hook behavior.
- [x] 5.2 If the repo uses **GitHub Actions**, add a **scheduled** workflow (cron) that runs **`RUN_KIND_O11Y_INTEGRATION=1`** (or the shell script) on **`main`**; otherwise add a short **“Suggested CI”** snippet to **`docs/`** for operators.

## 6. Verification

- [x] 6.1 Run **local CI parity** (README: uv + Helm + ADR check) or rely on **`.github/workflows/ci.yml`** on PRs; fix any traceability or test drift until green.
- [x] 6.2 Run **`python3 scripts/check_spec_traceability.py`** (project equivalent to **`openspec validate traceability`**) and resolve validation issues.
