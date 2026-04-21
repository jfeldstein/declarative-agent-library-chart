# ADR 0007: Feature lifecycle policy (OpenSpec changes, runtime, and chart)

## Status

Accepted

## Context

This repository is **alpha**: capabilities move from **proposal** through **implementation** to **promoted** normative specs, and features are sometimes **removed** (for example ATIF trajectory export choices, shadow or experimental paths) without a long enterprise deprecation runway. Contributors need a **repeatable** story for where work lives at each stage, which **artifacts** must move in lockstep, and how **retirements** stay auditable.

That story must compose with **[ADR 0003](0003-spec-test-traceability.md)** (spec IDs, `docs/spec-test-traceability.md`, test citations, waivers) and **[ADR 0006](0006-config-surface-alpha-breaking-changes.md)** (alpha breaking changes on Helm/env without a formal deprecation window until a future stability ADR).

## Decision

### 1. Lifecycle stages

Treat every feature as being in one of these stages:

| Stage | Meaning | Typical location |
| --- | --- | --- |
| **Proposed** | Design and tasks agreed; not yet normative for the whole repo | `openspec/changes/<change-id>/` (proposal, tasks, delta specs as the change defines) |
| **Implemented** | Code, chart, and tests exist on a branch or merged to main | Application under `helm/src/`, chart under `helm/chart/`, examples as needed |
| **Promoted** | Requirement is normative for the project | `openspec/specs/` with stable **[DALC-REQ-…]** / **[DALC-VER-…]** IDs per ADR 0003 |
| **Deprecated** | Still present but scheduled or marked for removal; operators/contributors should migrate | Same as implemented/promoted plus explicit note in development log and, if normative, in promoted spec text or a superseding ADR |
| **Removed** | Behavior, keys, or exports no longer exist | Code and templates updated; specs/matrix/tests/examples cleaned; removal recorded in development log |

Stages are **not** a semver promise; they describe **process and documentation**, not API stability (see ADR 0006).

### 2. Artifacts that must stay aligned

When a feature **enters**, **changes materially**, or **exits** any stage, update the set that applies to that feature:

1. **Promoted specs:** `openspec/specs/**/spec.md` — requirement headings and SHALL text; IDs unchanged unless the requirement is split/superseded (then follow supersede pattern below).
2. **Traceability matrix:** `docs/spec-test-traceability.md` — rows for each active ID; waive only per ADR 0003 (approver + reason).
3. **Tests:** Pytest docstrings and Helm unittest comments citing the same IDs as matrix evidence.
4. **Examples:** Under `examples/` (and chart defaults) so operators can see the supported shape; remove or rewrite when a feature is removed.
5. **Development log:** `docs/development-log.md` — short entry for merge-worthy changes (add, change, deprecate, remove).

For **chart/runtime** features, keep **template output and env contract** consistent with what the **`agent`** package reads (ADR 0006).

### 3. New ADR vs updating an existing ADR

- **Update an existing ADR** when refining **the same decision** (clarifications, extra bullets, consequences) without reversing the core choice.
- **Add a new ADR** when the decision is **new** (new policy area), **reverses** a prior decision, or **redefines** scope such that readers would be misled by editing the old doc alone.

Use the next free number under `docs/adrs/` and link backward from the new ADR to any ADRs it clarifies or constrains.

### 4. Supersede pattern

When a decision **replaces** an earlier one:

- New ADR **Status** remains **Accepted**; in **Context** or **Decision**, state that it **supersedes ADR NNN** for scope *X*.
- Optionally set the superseded ADR’s **Status** to **Superseded by [ADR NNN](NNN-….md)** in a follow-up edit to that file (same PR or later), so navigation stays clear.
- Move normative text in **promoted specs** to the new wording; do not leave contradictory SHALLs. Retire or renumber IDs only with matrix and test updates in the same change.

Removals (e.g. dropping an export format or a shadow flag) **SHOULD** mention **why** in the development log and, if the behavior was normative, either remove the requirement from promoted specs or mark it deprecated then remove in a subsequent change with traceability rows updated accordingly.

## Consequences

**Positive:**

- One predictable checklist for proposals, promotion, and teardown.
- Removals stay traceable: specs, matrix, tests, and examples do not drift silently.
- Aligns with existing alpha posture (ADR 0006) without pretending semver lifecycle.

**Negative / trade-offs:**

- More files touched per feature than “code only”; small changes can still require matrix or example updates.
- Stage names are internal discipline, not machine-enforced labels in git.

**Follow-ups:**

- If the repo adds release versioning or LTS, extend this ADR or supersede it with explicit deprecation timelines and compatibility layers.
- Optional automation: checklist in CI or PR template pointing at this ADR for “promoted spec” and “removal” PRs.

## See also

- **[ADR 0003](0003-spec-test-traceability.md)** — spec–test traceability (IDs, matrix, waivers, checker).
- **[ADR 0006](0006-config-surface-alpha-breaking-changes.md)** — alpha config surface and breaking changes.
