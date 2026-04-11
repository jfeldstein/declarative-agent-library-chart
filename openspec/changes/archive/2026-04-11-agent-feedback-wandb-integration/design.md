## Context

Agent systems increasingly use **tools** that produce **user-visible artifacts** (Slack messages, tickets, emails). Product and research teams want **scalar human feedback** (+1 / -1) tied to those artifacts so they can (a) **audit** failures, (b) build **ATIF** trajectories for analysis, and (c) mine **positive trajectories** for **SFT/RLFT**. **Weights & Biases** is a common hub for experiment tracking; attaching the same feedback and tags to **wandb traces** keeps training, evaluation, and production signals comparable. **Shadow rollouts** let teams try new prompts, skills, or models without swapping the default production path.

Constraints: reaction events may arrive **after** the run completes; Slack and other channels differ in how reactions are delivered; PII and secrets must not land in W&B or training exports without policy.

## Goals / Non-Goals

**Goals:**

- Define a **checkpoint** abstraction at boundaries where human feedback is meaningful (typically after a successful external side effect).
- Correlate **+1 / -1 / unlabeled** feedback to **tool-call spans** and checkpoints with stable identifiers.
- Specify **log → ATIF** mapping and **positive-sequence** export for downstream training jobs.
- Specify **wandb** run/trace usage, **required and optional tags**, and **feedback append** semantics on traces.
- Specify **shadow** execution: variant labeling, trace separation, and configurable promotion (out of scope for automatic promotion unless explicitly configured).

**Non-Goals:**

- Choosing a single training framework (HF, OpenPipe, etc.) beyond ATIF-shaped exports.
- Full Slack app marketplace submission or org-wide OAuth flows (integration points are specified; product packaging is not).
- Automatic model deployment from feedback (only data and observability contracts).

## Decisions

1. **Checkpoint and correlation identifiers**  
   - **Decision**: Every user-visible tool effect SHALL emit `run_id`, `trace_id` (or equivalent root span), `tool_call_id`, and `checkpoint_id` before the side effect is committed. The external artifact (e.g. Slack `channel` + `ts`) is stored as `external_ref` on the checkpoint.  
   - **Rationale**: Reactions reference **external** ids; training needs **internal** stable ids.  
   - **Alternatives**: Only external refs (brittle across channels); only internal ids (harder to join Slack events).

2. **Slack reactions as a primary +1/-1 source**  
   - **Decision**: Map `:+1:` / `thumbsup` to **positive**, `:-1:` / `thumbsdown` to **negative**; other reactions **ignored or logged as neutral** per configuration. Use Slack **Events API** (or equivalent) to receive `reaction_added` / `reaction_removed`, resolve `item.ts` + `channel` to `checkpoint_id` via a durable index (e.g. KV or DB).  
   - **Rationale**: Matches user mental model; emoji are explicit.  
   - **Alternatives**: Thread replies (“good/bad”) — higher NLP noise; only buttons — fewer organic signals.

3. **Idempotency and late events**  
   - **Decision**: Feedback events SHALL be **upserted** by `(checkpoint_id, user_id, reaction_type)` (or channel policy); the **latest** definitive label wins for training export where configured. Removed reactions SHALL emit a **revocation** or **neutral** update.  
   - **Rationale**: Avoid double-counting; handle async Slack delivery.

4. **ATIF trajectory shape**  
   - **Decision**: Export builds ATIF-compatible JSON from ordered spans: system/user/assistant/tool messages, **tool calls** with names/args/results, and **metadata** blocks for `checkpoint_id`, `feedback_label`, `tags`, and `variant` (primary vs shadow). Redaction runs **before** export.  
   - **Rationale**: ATIF is a useful interchange; keeps runtime agnostic of trainer.  
   - **Alternatives**: Proprietary JSON only — weaker ecosystem interop.

5. **W&B integration**  
   - **Decision**: Use **wandb**’s trace/logging APIs to record one **trace per agent run** (or per user session, configurable), with **spans** for LLM and tool calls. Human feedback is logged as a **distinct event** or **span metadata** on the matching tool/checkpoint span with keys `feedback_label`, `feedback_source`, `checkpoint_id`. Tags on the run include at minimum: `env`, `agent_name`, `agent_version`, `skill_set_version`, `model_id`, `rollout=primary|shadow`, `shadow_variant_id` (if shadow).  
   - **Rationale**: Tags enable filtered queries; trace attachment preserves timeline context.  
   - **Alternatives**: Only scalar metrics — lose per-tool attribution.

6. **Shadow rollouts**  
   - **Decision**: When enabled, the runtime MAY fork **non-mutating** or **synthetic** execution paths (or duplicate LLM calls with alternate prompts/models) tagged `rollout=shadow` and `shadow_variant_id`. Shadow tools that **mutate** external systems SHALL be disabled or replaced with **stubs** unless explicitly allowed.  
   - **Rationale**: Prevents duplicate Slack posts from shadow.  
   - **Alternatives**: Full duplicate posting — unacceptable in most orgs.

## Risks / Trade-offs

- **[Risk] PII in traces** → Mitigation: redaction pipeline, configurable blocklists, optional hashing of user ids in exports.  
- **[Risk] Feedback spam or brigading** → Mitigation: optional per-org rules (one vote per user, moderator-only channels).  
- **[Risk] W&B cost and cardinality** → Mitigation: tag cardinality limits, sampling for shadow, retention policies.  
- **[Risk] Missing correlation** → Mitigation: retries on index write; dead-letter queue for orphan reactions with alert.  
- **[Trade-off] Shadow compute** → Accept higher cost for a subset of traffic or time-windowed experiments.

## Migration Plan

1. Add instrumentation and checkpoint index behind feature flags.  
2. Enable W&B in non-prod; validate tags and feedback events.  
3. Turn on reaction webhook in a pilot workspace/channel.  
4. Enable ATIF export job in batch mode before online training consumers.  
5. Roll back by disabling webhooks and feature flags without deleting historical exports (if required by policy).

## Open Questions

- Exact ATIF schema version and field names to align with an internal golden fixture.  
- Whether **neutral** feedback is stored as explicit label or absence of label.  
- Org policy: can shadow use **real** read-only tools against production data?
