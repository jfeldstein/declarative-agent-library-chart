## Context

The repository already enforces **85% Python line coverage** and runs **helm unittest**, **`ct lint`**, an in-process **RAG smoke**, and optional **kind + Prometheus** tests behind an environment flag. **OpenSpec** requirements are prose **SHALL** statements; nothing today links them to tests or fails CI when a requirement lacks evidence. The **runtime-tools-mcp** spec text emphasizes **MCP** as the consumption path, which reads as mandatory **wire MCP** even though the implementation is **LangGraph**-centric and may bind tools **in-process**.

**Vocabulary:** Call this mechanism **test-to-spec traceability** when speaking to contributors. The short word **traceability** is overloaded (training-data lineage, supply chain, etc.); **test-to-spec** states the intent: **which automated tests evidence which normative spec rows**.

## Goals / Non-Goals

**Goals:**

- Define a **small, consistent ID scheme** and where IDs live (requirement headers or first line of the requirement body).
- Choose a **single source of traceability**: a **matrix** (e.g. Markdown or CSV under `docs/` or `helm/src/`) **and/or** **pytest docstrings** / file-level comments that list `CFHA-…` IDs—pick one primary artifact so CI can grep it.
- Add a **CI check** that is **practical on every PR**: e.g. fail if promoted `openspec/specs/**/spec.md` requirements lack IDs, or if matrix lists an ID with zero test references (evolve in implementation).
- Document **test tiers** so contributors know what “green CI” means vs **nightly / scheduled** heavy tests.
- Relax **tool exposure** language so **LangGraph-native** binding is clearly conforming.

**Non-Goals:**

- Replacing pytest with a new framework or requiring **real MCP sockets** in default CI.
- **100%** automated proof that every scenario is hit (expensive); first iteration targets **requirements** (SHALL blocks), not every sub-bullet.
- Renaming existing **Prometheus** metric names (`agent_runtime_mcp_*`) in this change (compatibility); wording may say “tool invocation” while series names stay stable unless a follow-up change migrates them.

## Decisions

### 1. Requirement ID format

Use **`DALC-REQ-<DOMAIN>-<NNN>`** (three-digit zero-padded) **or** shorter **`DALC-VER-NNN`** for verification meta-requirements—pick one family per capability file to avoid collisions. **Promoted specs** (`openspec/specs/`) gain IDs when edited; **change-local** specs gain IDs before archive when feasible.

**Rationale:** Human-greppable, stable across moves from `changes/` to `openspec/specs/`.

### 2. Test-to-spec artifact + tests

- **Primary:** A committed **matrix** file, e.g. `docs/spec-test-traceability.md`, columns: **Requirement ID | Spec path | Test evidence (file::test or helm test id)**.
- **Secondary:** Each test **SHALL** include the IDs it covers in a **docstring** (pytest) or **YAML comment** (helm unittest) so reviewers see intent at the call site.

**Rationale:** Matrix is one place auditors and CI can parse; docstrings avoid scroll-hunting.

### 2b. Proposed specs vs promoted specs

- **Promoted** (`openspec/specs/**`): every **`### Requirement:`** with a **SHALL** (or equivalent normative keyword) **SHALL** have an ID, a matrix row, and evidence tests **in the same PR** that lands the behavior—or a **waived** matrix row with maintainer + reason.
- **Change-local / proposed** (`openspec/changes/<change>/specs/**`): IDs are helpful for drafting, but there is **no** CI gate tying those rows to tests **until** the capability is implemented and the spec is **promoted** into `openspec/specs/`. The “one motion” rule applies at **promotion + implementation**, not at first draft of a proposal.

### 3. CI enforcement (first slice)

- Script (e.g. `scripts/check_spec_traceability.py` or shell + `rg`) run from **`ci.sh`** after tests:
  - **A)** Every `### Requirement:` under `openspec/specs/` matches a line in the matrix **or** has a documented waiver (rare).
  - **B)** Every matrix row’s tests exist (paths present).
- Stricter rules (e.g. require pytest docstring to contain ID) can be **phase 2** to avoid breaking the repo in one PR.

**Rationale:** Incremental enforcement avoids a Big Bang; still moves the bar.

### 4. AGENTS.md / Cursor rules

Add **`AGENTS.md`** at repo root (or extend if present) stating: adding/changing a **SHALL** in a promoted spec **requires** updating the **test-to-spec matrix** and **test references** in the same PR. Add a **`.cursor/rules`** fragment (or single rule file) that mirrors this for agentic contributors.

### 5. “Default” vs “scheduled” integration jobs

| Tier | Meaning | Example in this repo |
|------|---------|----------------------|
| **Default PR** | Runs on every PR / `ci.sh` without extra secrets | `pytest`, ruff, smoke_rag, helm unittest + `ct` when toolchain present |
| **Opt-in local** | Maintainer sets env var | `RUN_KIND_O11Y_INTEGRATION=1` kind + Prometheus test |
| **Scheduled** | Nightly / main-branch workflow, may use larger runners or cluster | Same kind script on a **cron** GitHub Actions job so regressions surface within ~24h without slowing every PR |
| **Manual** | Release or on-demand | Full e2e in a staging cluster |

**“More default or scheduled”** means: (a) promote a check from **opt-in** toward **default** when it is fast and reliable enough, or (b) add a **scheduled** workflow so heavy checks run **automatically** even when not on every PR—closing the gap between “we have a test” and “someone actually runs it.”

### 6. runtime-tools-mcp semantics — **contract vs wire**

The **`runtime-tools-mcp`** spec describes **operator-visible behavior**: which tools exist, how they are named and typed, how invocation and errors surface, and which **metrics** fire. That is the **contract**.

**Wire MCP** (stdio/SSE client speaking JSON-RPC to a separate tool host) is **one** implementation strategy. A **LangGraph-first** runtime may instead **bind the same tool functions in-process** (e.g. `BaseTool` objects on the compiled graph) while still honoring the **same** config flags, discovery-shaped tool lists, and telemetry names the spec defines.

**Why this matters:** CI and single-binary deployments may not want a second OS process per agent. Confusing “conformant” with “must spawn `mcp-server`” would **exclude** the primary implementation style this repo uses. The clarification is **strictly more permissive for implementers**: anything that preserves the **contract** remains conformant; the spec is **not** narrowed to a single transport.

**Conforming mental model for implementers:** implement the **contract**; use MCP wire **only** where ops teams already run external tool servers. Default PR tests prove the **contract** with in-process doubles; optional jobs may still run wire-level MCP where valuable.

## Risks / Trade-offs

- **[Risk] CI noise from brittle regex** → **Mitigation:** Start with `openspec/specs/` only; iterate script with clear error messages.
- **[Risk] Matrix rot** → **Mitigation:** CI fails on drift; PR checklist in AGENTS.md.
- **[Risk] ID churn during spec edits** → **Mitigation:** IDs are immutable once published; new obligations get new IDs; use REMOVED/Migration in deltas for retired requirements.

## Migration Plan

1. Land **delta** for `runtime-tools-mcp` and **ADDED** `dalc-requirement-verification`.
2. Backfill IDs + matrix rows for **existing** promoted specs in the same change series or a fast follow-up task (tasks.md may split).
3. Enable CI script; fix gaps until green.

## Open Questions

- Whether **helm chart** requirements should be in the **same matrix** or a sibling `docs/helm-spec-test-traceability.md` (implementation can split for clarity).
- Whether to add a **GitHub Actions** `schedule:` workflow in-repo in this change or only document the pattern in design/tasks (repo may not use GHA yet—check during apply).
