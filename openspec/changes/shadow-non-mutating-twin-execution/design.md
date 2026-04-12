## Context

The hosted agent runtime can execute a **primary** LangGraph/LangChain path per HTTP trigger. Shadow configuration (variant id, sampling, allowlists) exists, but a **second execution** that mirrors planner/model/tool behavior **without** external mutation is not fully specified or implemented. Operators need a **twin** that is safe by default, comparable in telemetry, and **isolated** from primary persistence.

## Goals / Non-Goals

**Goals:**

- Run a **shadow twin** for eligible requests that receives the **same normalized input** (messages, tool allowlists, skill activation state as of request boundary) as the primary, under `rollout_arm=shadow`.
- **Classify tools** and **stub** mutating side effects by default; allow **explicit shadow allowlist** and a **dangerous full-mirror** flag for exceptional environments.
- Maintain **checkpoint and thread isolation** so shadow never overwrites primary `thread_id` checkpoints.
- Provide **failure isolation**: shadow errors surface as shadow telemetry, not as primary user-visible failure (default).
- Emit **telemetry comparable** to primary (latency, tokens, tool plan shape, outcome) joined by `request_correlation_id`.

**Non-Goals:**

- Perfect **bit-for-bit determinism** across primary and shadow (models may still sample); the spec targets **structural** comparability and safe stubbing, not identical outputs.
- Building a **generic sandbox** for arbitrary binary tools; v1 focuses on **declarative tool metadata** + built-in implementations.
- **Cross-region** shadow or multi-tenant fair scheduling beyond existing percentage/allowlist/window flags.

## Decisions

1. **Twin scheduling**  
   - **Decision**: Default **after-primary** twin in-process (same worker) with a **short deadline** and **cancellation** when the client connection ends (configurable). Optional **async** mode enqueues twin work on a local queue (same pod) before considering cross-pod workers.  
   - **Rationale**: Minimizes race with primary mutations and simplifies correlation; async avoids tail latency on primary.  
   - **Alternatives**: Always parallel (higher tail latency risk for primary); always separate worker (higher ops burden).

2. **Execution context**  
   - **Decision**: Shadow runs under `ShadowExecutionContext` carrying `shadow_variant_id`, `rollout_arm=shadow`, `request_correlation_id`, **shadow thread id** (`thread_id` + stable suffix/namespace), and **stub policy**. Tool dispatch checks context before invoking real I/O.  
   - **Rationale**: Central choke point; avoids scattering `if shadow` across every tool.  
   - **Alternatives**: Duplicate graphs compiled per mode (harder to maintain).

3. **Tool classification**  
   - **Decision**: Each tool id **SHALL** declare `shadowBehavior`: `inherit` (default: use registry class), `read_only`, `mutating_external`, `internal`. Registry maps unknown tools to **mutating_external** (safe default).  
   - **Rationale**: Explicit metadata beats heuristic URL matching.  
   - **Alternatives**: Heuristic only (error-prone); code annotations only (harder for YAML-configured tools).

4. **Stub results**  
   - **Decision**: Stub returns a **typed envelope** `{ "shadow_stub": true, "tool": "<id>", "reason": "not_allowlisted|danger_flag_off", "args_redacted": {...} }` with redaction applied before export; duration still recorded.  
   - **Rationale**: Exporters and W&B can filter/analyze stubbed steps consistently.  
   - **Alternatives**: Empty dict (loses provenance); raise (breaks planner unless caught).

5. **Checkpointing**  
   - **Decision**: Shadow uses **separate checkpointer namespace** (`thread_id` + `shadow_variant_id` + `request_correlation_id` hash) or **ephemeral** shadow graph compile without persistence (configurable). Default **ephemeral** shadow checkpoints to reduce storage cost.  
   - **Rationale**: Avoids collision and retention explosion.  
   - **Alternatives**: Shared checkpointer (unsafe); always persisted (costly).

6. **Failure isolation**  
   - **Decision**: Twin exceptions convert to `RunOperationalEvent` / shadow span error with **no impact** on primary HTTP status (default).  
   - **Rationale**: Shadow is observability-first.  
   - **Alternatives**: Fail open / fail closed (product-specific).

## Risks / Trade-offs

- **[Risk] Shadow doubles LLM cost** → **Mitigation**: sampling + tenant caps + max shadow steps/tokens.  
- **[Risk] Stub diverges from real tool enough to mislead** → **Mitigation**: document stub envelope; optional **shadow allowlist** for read-only tools that mirror prod APIs.  
- **[Risk] Hidden mutators** (misclassified tools) → **Mitigation**: default unknown = mutating; CI lint for tool registry completeness.  
- **[Trade-off] After-primary shadow** adds latency to overall request handling when run synchronously → async mode and strict budgets.

## Migration Plan

1. Ship **spec + flags** with shadow twin **off** by default.  
2. Enable in staging with **async** shadow and **zero** allowlisted mutating tools.  
3. Dogfood comparison dashboards (W&B) on read-only tools only.  
4. Gradually allowlist **safe** read-only externals; keep mutating tools stubbed.  
5. **Rollback**: disable `HOSTED_AGENT_SHADOW_TWIN_ENABLED` (name TBD) — primary unchanged.

## Open Questions

- Whether **supervisor multi-turn** shadow must cap turns independently of primary.  
- Whether **RAG** calls count as external mutating (usually read) vs internal cache writes.  
- Exact **W&B** model: one run with two arms vs two runs joined by tag (preference: two runs + shared `request_correlation_id` for simpler queries).
