# ADR 0004: Pin trajectory exports to Harbor ATIF v1.4 (with internal canonical adapter)

## Status

Accepted

## Context

The runtime records a lightweight internal step log (`CanonicalTrajectory` / `TrajectoryStep`) for observability and export. Training and debugging pipelines increasingly expect **Agent Trajectory Interchange Format (ATIF)** — a JSON interchange used across Harbor-compatible tooling — rather than ad hoc JSON.

Harbor documents ATIF as the **Agent Trajectory Format**, with **ATIF-v1.4** as the current schema version, and points to the normative RFC and Pydantic models in the Harbor repository (see [Harbor: Agent Trajectory Format (ATIF)](https://www.harborframework.com/docs/agents/trajectory-format)).

Earlier builds of this chart emitted a placeholder `schema_version` and a non-ATIF root shape (`run_id` / `thread_id` / generic `steps[]`), which is not directly consumable by ATIF validators or Harbor workflows.

## Decision

1. **Interchange pin:** Exported JSON **SHALL** use `schema_version: "ATIF-v1.4"` and **SHALL** follow the Harbor ATIF root shape: `session_id`, `agent` (name, version, `model_name`), `steps[]`, optional aggregates such as `final_metrics`, and optional `extra` for vendor extensions.

2. **Internal canonical format:** The runtime **SHALL** keep an explicit internal provenance label **`hosted-agents-canonical-v1`** (carried under `extra.hosted_agents.canonical_format`) so consumers can tell the document was **adapted** from internal steps, not authored natively by a Harbor agent.

3. **Adapter location:** Mapping from `CanonicalTrajectory` to ATIF **SHALL** live in `hosted_agents/observability/atif.py` (`canonical_to_atif_v1_4` / `export_atif_batch`). ATIF is the **export** target; the internal trajectory remains the in-process source of truth until a future ADR merges them.

4. **Agent metadata:** `Trajectory.agent` fields **SHALL** be populated from environment (`HOSTED_AGENT_ATIF_AGENT_NAME`, `HOSTED_AGENT_ATIF_AGENT_VERSION`, `HOSTED_AGENT_ATIF_MODEL_NAME`) with safe defaults so exports validate structurally without silent misrepresentation.

5. **Optional validation:** Running Harbor's `TrajectoryValidator` (or equivalent) in CI **MAY** be added later as a dev dependency or separate job; it is **not** required for the default slim runtime image.

## Consequences

**Positive:**

- Exports align with a **published, versioned** interchange (Harbor ATIF v1.4) and can be validated or converted with Harbor tooling.
- Internal evolution can proceed behind the adapter; ATIF consumers see a stable outer contract.

**Negative / trade-offs:**

- The adapter is **best-effort**: internal `kind` values that are not true user/agent turns are mapped to `source: "system"` steps with `extra.hosted_agents` payloads.
- Token and cost aggregates are **zeroed** in `final_metrics` unless a future change wires real metrics into the trajectory builder.

**Follow-ups:**

- Optionally add `harbor` as a dev dependency and a contract test that validates golden exports.
- If the RFC moves or ATIF v1.5 ships, add a new ADR or supersede this one with an explicit version bump.

## References

- [Harbor — Agent Trajectory Format (ATIF)](https://www.harborframework.com/docs/agents/trajectory-format) (schema versions, examples, validator).
- Harbor ATIF RFC (repository): `docs/rfcs/0001-trajectory-format.md` in [laude-institute/harbor](https://github.com/laude-institute/harbor) (path may change with upstream).
