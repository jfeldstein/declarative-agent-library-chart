## Why

Promoted normative specs use **SHALL** language, but **tests** are not mechanically linked to those obligations, so reviewers and CI cannot tell whether each **implemented** requirement is exercised. Separately, the **runtime-tools-mcp** capability reads as if **wire-level MCP** were the only valid implementation, which conflicts with a **LangGraph-first** runtime where tools may be bound **in-process** while preserving the same operator and observability contracts.

## What Changes

- Introduce **test-to-spec traceability** (also called **spec–test traceability** in `docs/`): stable **requirement IDs** on **promoted** `openspec/specs/**/spec.md` **SHALL** rows, a **matrix** in **`docs/spec-test-traceability.md`**, and **pytest / Helm unittest** artifacts that cite those IDs—enforced by **`scripts/check_spec_traceability.py`** on the default PR path (exact rules in **`dalc-requirement-verification`** and ADR 0003).
- **Proposed-only** specs under `openspec/changes/.../specs/` that are **not** merged into `openspec/specs/` **do not** need matrix rows or test ID links until work is **implemented and promoted**; the obligation applies **when code ships** for a promoted **SHALL**, in the **same change** as the tests and matrix row (or an explicit waiver row).
- Add / extend project **AGENTS.md** and **Cursor rules** so contributors use the term **test-to-spec traceability** when they mean this mechanism (avoid bare “traceability,” which invites unrelated meanings such as supply-chain provenance).
- **Clarify** in **runtime-tools-mcp** that **MCP** names the **reference contract** (enablement, discovery-shaped tool lists, invocation semantics, metrics), not a mandate that every process runs a standalone MCP wire server—see design §“Contract vs wire.”
- Document **test tiers**: what runs on **every PR** vs **scheduled** vs **manual** so heavy checks can move to cron without blocking all PRs.

## Capabilities

### New Capabilities

- `dalc-requirement-verification`: Stable requirement IDs, **test-to-spec** matrix and/or test docstrings, contributor rules (AGENTS/rules), and CI enforcement for spec–test linkage for **promoted** `openspec/specs/` capabilities (and conventions for change-local specs where applicable).

### Modified Capabilities

- **`runtime-tools-mcp`** (spec today lives under change **`agent-runtime-components`**; this change adds a **delta** under `openspec/changes/traceability/specs/runtime-tools-mcp/spec.md`): Reframe tool exposure so **LangGraph-based / in-process** binding is **allowed** when it preserves configuration-driven enablement, discovery/invocation **semantics**, and metrics; MCP is the **reference contract**, not a mandate for a separate wire protocol in every deployment or in CI.

## Impact

- **`openspec/specs/`** and/or change-local specs: new verification capability; delta for **`runtime-tools-mcp`**.
- **`helm/src/tests/`**, **`examples/*/tests/`**, Helm tests: docstrings or comments with requirement IDs; possible **`docs/`** or **`helm/src/`** traceability matrix file.
- **`.github/workflows/ci.yml`** (and local **`python3 scripts/check_spec_traceability.py`**): traceability gate on default PRs; optional documented **scheduled** job pattern for kind/integration—implementation in apply phase.
- **`AGENTS.md`** and optionally **`.cursor/rules`**: contributor enforcement text.
- **No breaking change** to runtime APIs; spec clarification may widen what counts as conforming (strictly **more** permissive for implementers).
