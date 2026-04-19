# OpenSpec workflow (repository contract)

Instructions for handling **`openspec/`** correctly on the first pass. This file intentionally avoids describing the repo’s historical state—only roles, transitions, and obligations.

For **test-to-spec traceability** when editing promoted specs (`openspec/specs/*/spec.md`), follow the repository root **`AGENTS.md`** (stable IDs, matrix, pytest/Helm citations, `scripts/check_spec_traceability.py`). Prefer the phrase **spec–test traceability** or **OpenSpec test-to-spec traceability** per **[DALC-VER-005]** so “traceability” stays unambiguous.

---

## Two layers (do not conflate)

| Layer | Path | Role |
|--------|------|------|
| **Promoted (canonical)** | **`openspec/specs/<capability>/spec.md`** | Normative requirements the codebase and CI are judged against once merged. |
| **Change workspace (draft)** | **`openspec/changes/<change-name>/`** | Proposal, design, tasks, and optional **delta** specs for *that change only*. |

**Delta specs** live under **`openspec/changes/<change-name>/specs/<capability>/spec.md`**. They are **draft** text for review and iteration. They do **not** replace promoted specs until you complete **promotion** (below).

**Archiving** moves a change folder to **`openspec/changes/archive/<YYYY-MM-DD>-<change-name>/`**. That is **filing**, not specification. It does **not** copy text into **`openspec/specs/`**.

---

## Lifecycle transitions (what to do at each step)

### 1. Start a change

- Create or use an OpenSpec change directory **`openspec/changes/<change-name>/`** per your **`openspec`** CLI workflow and **`config.yaml`** schema (`spec-driven`, etc.).
- Maintain **`proposal.md`**, **`design.md`** (when useful), and **`tasks.md`** as required by that schema.

**Exit criteria:** Intent and scope are writable without blocking implementation.

---

### 2. Author delta specs (optional but typical)

- Add or edit **`openspec/changes/<change-name>/specs/<capability>/spec.md`** while the design stabilizes.
- Treat these files as **negotiable drafts**: headers like **ADDED** / **MODIFIED** / **REMOVED** (or equivalent) describe intent relative to *today’s* promoted baseline, not the final promoted file format.

**Exit criteria:** Draft text is precise enough that a reviewer could implement or promote it without guesswork.

---

### 3. Implement and verify

- Implement behavior in code, chart, tests, and docs as **`tasks.md`** describes.
- **Before merge (or in the same change series),** align **tests and evidence** with how you will promote requirements (pytest docstrings / Helm `#` comments / matrix rows per root **`AGENTS.md`**).

**Exit criteria:** CI-style checks pass locally; tasks you mark done are actually evidenced.

---

### 4. Promote (sync) draft → canonical **before** treating the capability as “landed”

**Promotion** means: merge the **normative** content of the delta into the right **`openspec/specs/<capability>/spec.md`** (create the capability folder if needed), then wire traceability.

**Do this when the behavior is real** (same release/PR as the code, or immediately after—never “eventually” without a tracked follow-up).

For each capability you are promoting:

1. **Merge** delta text into **`openspec/specs/<capability>/spec.md`**, resolving conflicts **in favor of shipped behavior** and **in favor of stable requirement IDs** where both exist.
2. **Assign or preserve** bracketed IDs on **`### Requirement:`** lines per **`openspec/specs/dalc-requirement-verification/spec.md`** and root **`AGENTS.md`**.
3. **Update** **`docs/spec-test-traceability.md`** for every new or materially changed **`SHALL`** (or add a **waived** row with approver + reason where policy allows).
4. **Cite IDs** in tests listed as evidence; run **`python3 scripts/check_spec_traceability.py`**.

**Naming:** Promoted capability directories under **`openspec/specs/`** use the **long-lived** slug (e.g. **`dalc-…`**). Delta folders under a change may use shorter or older names; **promotion is the moment to normalize** names to the canonical tree.

**Exit criteria:** Promoted spec(s) match what mainline code does; traceability gate is green.

---

### 5. Complete and check off the change

- Mark **`tasks.md`** complete only when implementation **and** promotion/traceability obligations for **in-scope** requirements are satisfied (or explicitly waived per project rules).
- If part of the change is intentionally **not** promoted (spike, superseded design), record that decision in **`proposal.md`** or **`design.md`** so future readers do not assume a missing **`openspec/specs/`** file is an oversight.

**Exit criteria:** Honest checklist; no “done” without verification you actually ran.

---

### 6. Archive the change folder (optional housekeeping)

- When the change is finished and merged, move **`openspec/changes/<change-name>/`** to **`openspec/changes/archive/<YYYY-MM-DD>-<change-name>/`** using a **new** date prefix if the target name already exists.
- **Do not** treat this step as “syncing specs.” Promotion (§4) must already have happened for any behavior that required a normative spec update.

**Acceptable “archive without full delta text in root” only when:** the delta was exploratory, withdrawn, or fully absorbed under a **different** promoted capability after explicit merge—and that decision is documented in the archived **`proposal.md`** / **`design.md`**.

**Exit criteria:** Active **`openspec/changes/`** listing stays uncluttered; history remains in **`archive/`** if you need forensic context.

---

## Transition cheat sheet

| From | To | Action |
|------|----|--------|
| Idea | Change workspace | Create **`openspec/changes/<name>/`**, proposal (+ design/tasks per schema). |
| Draft | Implementable spec | Iterate delta specs under **`specs/<capability>/`** until precise. |
| Code merged | Canonical truth | **Promote** into **`openspec/specs/`**, IDs + matrix + test citations (§4). |
| Done | Historical record | **Archive** dated folder; optional cleanup of stale delta-only duplicates only after promotion decision is clear. |

---

## Anti-patterns (avoid)

- **Archiving first** and assuming **`openspec/specs/`** updated itself.
- **Leaving delta specs as the only normative copy** after merge.
- **Promoting without IDs / matrix / test citations** when **`SHALL`** clauses changed.
- **Blind copy** from **`archive/`** onto **`openspec/specs/`**—root specs may already include traceability edits; always **three-way merge**: delta intent + shipped behavior + existing IDs/matrix.

---

## Related paths

| Document | Purpose |
|----------|---------|
| **`docs/adrs/0003-spec-test-traceability.md`** | Spec ↔ test conventions |
| **`docs/spec-test-traceability.md`** | Requirement ID matrix |
| **`openspec/specs/dalc-requirement-verification/spec.md`** | Meta-rules for IDs and promotion quality |
| **`.cursor/skills/openspec-archive-change/SKILL.md`** | Mechanical archive steps (still read §4 first) |
