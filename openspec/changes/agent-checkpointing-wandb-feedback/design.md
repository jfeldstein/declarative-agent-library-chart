## Context

The repo is moving toward **config-first hosted agents** with observable runs. This change **subsumes** the earlier draft `agent-feedback-wandb-integration` (removed). We **dropped ATIF export** from scope: the **checkpointer** is the **source of truth** for ordered steps; **W&B** provides **automatic tracing** during execution—there is **no** separate ATIF export prerequisite. **Shadow rollouts** are **deferred** to the **`shadow-rollout-evaluation`** change.

Human judgment often arrives **asynchronously** (e.g. a Slack reaction on a bot message). That signal must link to a **stable `tool_call_id`** and **checkpoint**, update **durable storage**, and **annotate** the correct **W&B span/trace** for the step that produced the message.

## Goals / Non-Goals

**Goals:**

- Every supported agent run **SHALL** persist checkpoints at defined boundaries (task completion / step boundaries) without per-tool boilerplate.
- **Tool calls** and **external side effects** (e.g. Slack posts) **SHALL** carry **correlation metadata** in the **host’s durable store** (Slack does not support hidden metadata on messages).
- **W&B** **SHALL** receive **automatic traces** as LLM/tool work runs, with a **fixed tag schema** for slicing where values are known.
- **Checkpoint records** (or an equivalent durable index keyed by `checkpoint_id`) **SHALL** store **W&B run/span identifiers** for that step so feedback ingestion can resolve **Slack message → tool call → checkpoint → W&B** and patch traces after the fact.
- **Explicit human feedback** (e.g. reactions mapped through the global registry) **SHALL** be **durably stored** and linked to `tool_call_id` and `checkpoint_id` when resolution succeeds.

**Non-Goals:**

- **ATIF** export, canonical trajectory export buffers dedicated to ATIF, or **positive-feedback subsequence mining** for SFT/RLFT in this change.
- **Shadow rollouts** (see **`shadow-rollout-evaluation`**).
- Replacing LangGraph with a different orchestration engine (we **integrate** with or **mirror** its checkpoint semantics).
- A full Slack marketplace app; a **minimal** reaction → feedback path is enough for v1.
- **Operational lifecycle signals** as a first-class feedback taxonomy, **opt-in mappers** from ops events to training labels, or **`RunOperationalEvent`** modeling—**v1** is **explicit human feedback only**.

## Decisions

1. **Checkpoint model**  
   - **Decision**: Treat each **logical agent run** as a **thread** (`thread_id`). Persist after each **`@task`** completion (or equivalent atomic step).  
   - **Rationale**: Aligns with LangGraph functional API + checkpointer and enables resume and inspection.

2. **Automatic checkpointing**  
   - **Decision**: Runtime **injects** a checkpointer for compiled graphs / entrypoints registered with the agent host; **deny** or **warn** on workflows that opt out without an explicit **ephemeral** flag.

3. **Source of truth**  
   - **Decision**: The **checkpointer** (checkpoint history per thread) is the **authoritative ordered record** of steps for resume and for correlating feedback. W&B is **observability and annotation**, not a second source of step truth.

4. **Feedback correlation (server-side)**  
   - **Decision**: Maintain a **durable mapping** `(slack_channel_id, message_ts)` → `{ tool_call_id, checkpoint_id, run_id, thread_id, wandb_run_id, wandb_span_id (or equivalent), … }`. Do **not** rely on invisible Slack metadata on posts.  
   - **Rationale**: Slack does not support hidden per-message metadata in the way we need; server-side store is reliable.

5. **W&B tracing and feedback**  
   - **Decision**: Use the W&B integration path that **automatically** traces LLM/tool execution. When a checkpoint is written for a step, **persist** the **W&B identifiers** needed to **annotate** that step later (exact fields depend on SDK: run id, span id, trace id, etc.). On feedback ingestion: **write** the feedback to the **database** (or checkpoint-adjacent store) **and** update **W&B** for the resolved span/run.  
   - **Rationale**: Enables late reactions without requiring a separate export pipeline.

6. **Human feedback only (v1)**  
   - **Decision**: Persist **explicit human judgment** (reactions, future ratings) with the **global versioned registry**. Do **not** specify `RunOperationalEvent`, derived training labels, or ATIF provenance splits in this change.

7. **Feedback taxonomy: global-only**  
   - **Decision**: **Single global, versioned label registry** for human-judgment labels. **Per-agent taxonomies** are out of scope for v1.

## Risks / Trade-offs

- **[Risk] PII in checkpoints and W&B** → **Mitigation**: Redaction in trace payloads; configurable blocklists; document retention.  
- **[Risk] Feedback latency** → **Mitigation**: Treat feedback as **async patch** to stored records and W&B.  
- **[Risk] LangGraph / W&B SDK drift** → **Mitigation**: Pin versions; contract tests for persisted id shape and tags.  
- **[Trade-off] Storage cost** → Checkpoint frequency vs retention; sampling policies if needed later.

## Migration Plan

1. Add checkpoint store and host wiring behind **feature flag**; default **off** until validated.  
2. Ship **W&B automatic tracing** and **checkpoint ↔ W&B id** persistence **before** Slack reaction ingestion (dogfood traces without feedback loop).  
3. Enable Slack reaction ingestion in **staging** with a single workspace; verify **Slack → DB → W&B annotation** end-to-end.  
4. **Rollback**: disable flags; new fields remain backward compatible for readers that ignore them.

## Open Questions

- **Production checkpointer backend**: Postgres vs Redis vs vendor—pick per deployment size.  
- **W&B span-level updates**: Confirm the supported API for **late** feedback on an existing span (vs keyed `wandb.log`) for the pinned SDK.  
- **Global registry process**: Who approves new labels and how registry version bumps roll out to Slack emoji maps.
