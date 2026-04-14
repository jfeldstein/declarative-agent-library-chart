## Context

**Test-to-spec traceability** is enforced by **`scripts/check_spec_traceability.py`** and **`docs/spec-test-traceability.md`**. IDs today use the **`CFHA-`** prefix and capability folders use **`cfha-`**, which no longer matches DALC product naming.

## Goals / Non-Goals

**Goals:**

- Apply a **single atomic migration** on `main`: rename **`openspec/specs/cfha-*`** → **`dalc-*`**, and rename all **requirement ID prefixes** **`CFHA-` → `DALC-`** while preserving **`<SLUG>-<NNN>`** suffixes (e.g. `O11Y-SCRAPE-001`).
- Update the traceability checker, matrix, ADR 0003, contributor docs, Cursor rules, and all test/Helm comments that embed IDs or spec paths.
- Fix **in-spec cross-references** (e.g. `dalc-agent-o11y-scrape` instead of `cfha-agent-o11y-scrape` in body text).

**Non-Goals:**

- Changing the **semantic text** of requirements except where it explicitly says **CFHA** as the product name (e.g. chart-testing title “CFHA Helm charts” → “DALC” / “Declarative Agent Library”).
- Renaming **unrelated** runtime metrics, Helm release names, or Grafana files (handled by other changes).
- Rewriting **archived** OpenSpec change history under `openspec/changes/archive/` (optional follow-up).

## Decisions

1. **Preserve numeric suffixes and capability slugs**  
   **Rationale:** Minimizes diff noise and keeps **one-to-one** mapping for reviewers (`CFHA-REQ-O11Y-SCRAPE-001` ↔ `DALC-REQ-O11Y-SCRAPE-001`).  
   **Alternative:** New numbering scheme — rejected as unnecessary churn.

2. **Verification meta-requirements:** `[CFHA-VER-001]` → `[DALC-VER-001]` (same numbers).  
   **Rationale:** Keeps **[VER-004]** references to meta-rules consistent with a simple prefix swap.

3. **Folder rename mapping** (prefix swap only):

   | From | To |
   |------|-----|
   | `cfha-requirement-verification` | `dalc-requirement-verification` |
   | `cfha-chart-testing-ct` | `dalc-chart-testing-ct` |
   | `cfha-helm-unittest` | `dalc-helm-unittest` |
   | `cfha-agent-o11y-scrape` | `dalc-agent-o11y-scrape` |
   | `cfha-agent-o11y-logs-dashboards` | `dalc-agent-o11y-logs-dashboards` |
   | `cfha-rag-from-scrapers` | `dalc-rag-from-scrapers` |

4. **`check_spec_traceability.py`**  
   **Rationale:** Replace `ID_PATTERN` / matrix patterns to accept **`DALC-REQ-`** and **`DALC-VER-`** only (no dual acceptance after merge, unless we use a **one-PR** transition with temporary union—prefer **single cutover**).  
   **Env var:** Introduce **`DALC_TRACEABILITY_STRICT`**; optionally accept **`CFHA_TRACEABILITY_STRICT`** as deprecated alias for one release with a stderr warning, or document a breaking rename only.

5. **Slug derivation text** in **`dalc-requirement-verification`**: Example folder **`dalc-helm-unittest`** → slug **`HELM-UNITTEST`** (strip `dalc-` prefix for slug derivation, same as today’s strip of `cfha-`).

## Risks / Trade-offs

- **[Risk] Missed reference** → **Mitigation:** `rg 'CFHA-REQ|CFHA-VER|openspec/specs/cfha-'` on repo root; run **`python3 scripts/check_spec_traceability.py`** until green.
- **[Risk] OpenSpec archive / tooling** → **Mitigation:** If `openspec validate` or internal links use paths, update **active** change metadata; archive optional.
- **[Trade-off] Large PR** → Acceptable: mechanical renames should stay one merge commit for consistency.

## Migration Plan

1. `git mv` each `openspec/specs/cfha-*` → `dalc-*`.
2. Bulk-update **`### Requirement:`** lines and docstrings/comments.
3. Update checker script + matrix + ADR + workflows.
4. Run full pytest, helm unittest, traceability script, `ct lint` as in CI.

## Open Questions

- Whether to keep **`CFHA_TRACEABILITY_STRICT`** as a silent alias for one release (maintainer preference).
