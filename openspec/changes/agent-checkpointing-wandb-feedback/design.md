## Context

The repo is moving toward **config-first hosted agents** with observable runs. This change **subsumes** the earlier draft `agent-feedback-wandb-integration` (removed): unique requirements from that draft were **ported** into the specs here (checkpoint–side-effect binding, orphan reactions, W&B cardinality and late feedback, ATIF redaction and positive-mining detail, shadow bounds and `shadow_variant_id`). LangGraph’s **functional API** documents manual use of `@entrypoint(checkpointer=...)` and `@task`; we want **automatic** checkpoint boundaries so implementers cannot forget persistence. Human judgment often arrives **asynchronously** (e.g. a Slack user adds 👎 to a bot message that corresponds to a **tool outcome**). That signal must link back to a **stable tool-call id** and appear in **W&B traces** for analysis and training exports (**ATIF**).

## Goals / Non-Goals

**Goals:**

- Every agent run that uses the supported runtime **SHALL** persist checkpoints at defined boundaries (task completion / step boundaries) without per-tool boilerplate.
- **Tool calls** and **external side effects** (e.g. Slack posts) **SHALL** carry **correlation metadata** usable by reaction webhooks and by exporters.
- **W&B** **SHALL** receive runs with a **fixed tag schema** and **SHALL** allow attaching **scalar feedback** (e.g. +1 / -1) to the correct **span** or **custom metric** tied to that tool call.
- **ATIF export** **SHALL** be derivable from the same canonical trajectory representation used for checkpoints and W&B.
- **Shadow rollouts** **SHALL** execute variant configurations in a way that does not mutate production state, while emitting **comparable** tagged telemetry.

**Non-Goals:**

- Replacing LangGraph with a different orchestration engine (we **integrate** with or **mirror** its checkpoint semantics).
- Building a full Slack app marketplace distribution; a **minimal** reaction→feedback path is enough for v1.
- Owning a hosted W&B or Slack deployment; we assume **API keys** and existing projects.

## Decisions

1. **Checkpoint model**  
   - **Decision**: Treat each **logical agent run** as a **thread** (`thread_id` in configurable config). Persist after each **`@task`** completion (or equivalent atomic step), matching LangGraph’s resume-after-error behavior.  
   - **Rationale**: Aligns with [LangGraph functional API + checkpointer](https://docs.langchain.com/oss/python/langgraph/use-functional-api) and enables `get_state` / history-style inspection.  
   - **Alternatives**: Checkpoint only at entrypoint return (worse for HITL and failure resume); custom ad-hoc JSON blobs (harder to interoperate).

2. **Automatic checkpointing**  
   - **Decision**: Runtime **injects** a checkpointer for compiled graphs / entrypoints registered with the agent host; **deny** or **warn** on workflows that opt out without an explicit “ephemeral” flag.  
   - **Rationale**: “Automatic” means policy at the host layer, not repeated author code.  
   - **Alternatives**: Library wrapper only (easy to bypass).

3. **Feedback correlation**  
   - **Decision**: Every externally visible artifact (Slack message) includes **structured metadata** in the transport (e.g. Slack `blocks` with invisible fields or `metadata` payload) encoding `tool_call_id`, `thread_id`, `run_id`, `wandb_trace_id` / `span_id` when available. Reactions are ingested via Events API and **resolve** to that tuple.  
   - **Rationale**: Reactions alone do not carry agent context; we must **embed** or **lookup** keys.  
   - **Alternatives**: Only channel+timestamp lookup (fragile under edits/threads).

4. **W&B mapping**  
   - **Decision**: One **W&B run** per top-level agent invocation (configurable), with **child spans** per tool call; feedback updates **wandb.log** with a structured key (e.g. `feedback/tool_call_id`) and/or **span feedback API** if used by the chosen W&B integration path. Tags: `agent_id`, `env`, `skill_id`, `skill_version`, `model_id`, `prompt_hash`, `rollout_arm` (`primary` | `shadow`), `thread_id`.  
   - **Rationale**: Consistent slicing in the UI and for downstream dataset export.  
   - **Alternatives**: One run per tool (too noisy).

5. **ATIF export**  
   - **Decision**: Define an internal **CanonicalTrajectory** (ordered steps with messages, tool calls, outcomes, feedback slots). Exporter maps to ATIF **without** losing feedback annotations.  
   - **Rationale**: Single source of truth for W&B, Slack correlation, and training.  
   - **Alternatives**: Export only from W&B (couples training to vendor log shape).

6. **Shadow rollouts**  
   - **Decision**: **Read-only** shadow path: duplicate LLM/tool planning with **tools stubbed** or routed to **no-op/sandbox** unless explicitly allowlisted; tag `rollout_arm=shadow`. For “full mirror” shadow, require an explicit **dangerous** feature flag.  
   - **Rationale**: Prevents double posting to Slack or duplicate mutations by default.  
   - **Alternatives**: Always full duplicate (unsafe).

7. **Human feedback vs operational signals**  
   - **Decision**: Treat **explicit human judgment** (reaction, rating, reviewer label) as **`HumanFeedbackEvent`** (or equivalent) with a **taxonomy reference**. Treat **implicit / behavioral signals** (message deleted, user rewrote prompt, human takeover, session abandoned) as **`RunOperationalEvent`** (or telemetry spans)—**not** the same record type as training feedback **by default**. Downstream jobs may **derive** weak labels from operational events only via **documented, opt-in** mappers (e.g. “takeover ⇒ negative proxy”) so teams do not confuse correlation with intentional labels.  
   - **Rationale**: Merging implicit signals into “feedback” pollutes reward models, blames the wrong step, and creates compliance ambiguity (“who rated this?”). Keeping a separate stream preserves honesty about provenance.  
   - **Alternatives**: Single `FeedbackEvent` enum for everything (simple schema, dangerous semantics); ignore implicit signals entirely (lose debugging power).

8. **Feedback taxonomy: global-only**  
   - **Decision**: Use a **single global, versioned label registry** for all human-judgment labels across agents. **Per-agent taxonomies are out of scope** for v1: new labels are added only by **bumping the global registry** (review + deploy), not by agent-local tables. Events may still carry **`agent_id`** for **attribution and slicing** (which agent was rated), but **label identity and meaning** are always global.  
   - **Rationale**: Maximizes comparability for pooled training, W&B filters, and ATIF exports; avoids silent semantic drift between teams.  
   - **Alternatives**: Per-agent or hybrid registries (faster local iteration, higher long-term merge cost).

## Feedback taxonomy: why global wins (reference)

**Decision**: **Global taxonomy wins**—one registry, versioned; no per-agent label namespaces in scope for this change.

| Dimension | **Global taxonomy** (chosen) | **Per-agent taxonomy** (declined for v1) |
|-----------|------------------------------|------------------------------------------|
| **Cross-agent training** | Shared head; easy to pool data | Needs mapping layer or incomparable labels |
| **Dashboards & W&B** | One filter vocabulary | Namespaced labels; harder org-wide views |
| **Governance** | One meaning per `label_id` | Drift risk across agents |
| **Schema churn** | Central version bumps | Local changes fragment exports |

**Reversibility (two-way door)** remains good if events store **`(registry_id, label_id, schema_version)`** and consumers resolve strings from the registry—not hard-coded emoji tables. Introducing per-agent namespaces later would be a **deliberate schema/product change**, not required now.

## Risks / Trade-offs

- **[Risk] PII in checkpoints and W&B** → **Mitigation**: Redaction hooks before export; configurable field blocklists; document retention.  
- **[Risk] Slack metadata size / API limits** → **Mitigation**: Short ids server-side with lookup table; store full correlation server-side keyed by `message_ts`.  
- **[Risk] Feedback latency** → **Mitigation**: Treat feedback as **async patch** to trajectory; ATIF export can be **eventually consistent**.  
- **[Risk] LangGraph version drift** → **Mitigation**: Pin versions; integration tests against `get_state` / history APIs we rely on.  
- **[Trade-off] Storage cost** → Checkpoint frequency vs retention; offer TTL and sampling for shadow runs.

## Migration Plan

1. Add checkpoint store and host wiring behind **feature flag**; default **off** in existing deployments until validated.  
2. Ship W&B + tagging with **no** Slack dependency first (internal dogfood).  
3. Enable Slack reaction ingestion in **staging** with a single workspace.  
4. Enable ATIF export as a **batch job** before online training pipelines.  
5. **Rollback**: disable flag; checkpoints remain in store but UI/export stops reading new fields (backward compatible reads).

## Open Questions

- **Production checkpointer backend**: Postgres vs Redis vs vendor (LangGraph Cloud)—pick per deployment size.  
- **ATIF schema version**: Pin to a specific ATIF revision used by the training toolchain.  
- **Span-level feedback in W&B**: Confirm best API (Weights & Biases Traces vs custom `wandb.Table`) for the SDK version in use.  
- **Global registry process**: Who approves new labels and how registry version bumps roll out to Slack emoji maps and UIs.  
- **Opt-in mappers** from `RunOperationalEvent` to training weights: which events, if any, get a blessed mapping for RL/SFT—and who signs off.
