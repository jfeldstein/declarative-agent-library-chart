## Why

Normative specs use **SHALL** language, but tests are not mechanically linked to those obligations, so reviewers and CI cannot tell whether each requirement is exercised. Separately, the **runtime-tools-mcp** capability reads as if **wire-level MCP** were the only valid implementation, which conflicts with a **LangGraph-first** runtime where tools may be bound **in-process** while preserving the same operator and observability contracts.

## What Changes

- Introduce **stable requirement IDs** and a **traceability convention**: every test (or matrix row) **SHALL** reference the requirement IDs it is intended to satisfy; add a **machine-checkable** gate in CI where feasible (e.g. script that fails if promoted specs contain `### Requirement:` blocks without IDs, or if IDs lack matrix/test coverage—exact rules in design/spec).
- Add project **AGENTS.md** (and/or **Cursor rules**) that require new/changed **SHALL** requirements to update tests **and** the traceability matrix (or docstrings) in the same change.
- **Clarify** in **runtime-tools-mcp** that **MCP** describes the **external contract and configuration model** (enablement, discovery-shaped tool lists, invocation semantics, metrics) and that implementations **MAY** satisfy it via **LangGraph-native or in-process** tool registration **without** requiring a separate MCP client/server process in CI, as long as behavior and metrics match the spec.
- Document **test tiers**: what runs on **every PR** vs what runs **on a schedule** or **manually** (e.g. kind + Prometheus), so “more default or scheduled integration jobs” means optionally promoting heavy checks from **manual/opt-in** to **scheduled** (nightly) or **default** CI when infrastructure allows—without blocking all PRs on cluster tests.

## Capabilities

### New Capabilities

- `cfha-requirement-verification`: Stable requirement IDs, traceability matrix and/or test docstrings, contributor rules (AGENTS/rules), and CI enforcement for spec–test linkage for **promoted** `openspec/specs/` capabilities (and conventions for change-local specs where applicable).

### Modified Capabilities

- **`runtime-tools-mcp`** (spec today lives under change **`agent-runtime-components`**; this change adds a **delta** under `openspec/changes/traceability/specs/runtime-tools-mcp/spec.md`): Reframe tool exposure so **LangGraph-based / in-process** binding is **allowed** when it preserves configuration-driven enablement, discovery/invocation **semantics**, and metrics; MCP is the **reference contract**, not a mandate for a separate wire protocol in every deployment or in CI.

## Impact

- **`openspec/specs/`** and/or change-local specs: new verification capability; delta for **`runtime-tools-mcp`**.
- **`runtime/tests/`**, **`examples/*/tests/`**, Helm tests: docstrings or comments with requirement IDs; possible **`docs/`** or **`runtime/`** traceability matrix file.
- **`ci.sh`** (or sibling scripts): new verification step(s); optional documented **scheduled** job pattern (e.g. GitHub Actions workflow) for kind/integration—implementation in apply phase.
- **`AGENTS.md`** and optionally **`.cursor/rules`**: contributor enforcement text.
- **No breaking change** to runtime APIs; spec clarification may widen what counts as conforming (strictly **more** permissive for implementers).
