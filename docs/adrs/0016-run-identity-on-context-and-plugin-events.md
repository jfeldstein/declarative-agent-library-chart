# ADR 0016: Run identity on TriggerContext and plugin-interpreted lifecycle events

## Status

Accepted

## Context

Several concerns must agree on **who this run is** for labeling and tracing: Prometheus LLM metrics, optional Weights & Biases runs, and similar integrations. When each layer **re-reads process environment** (`HOSTED_AGENT_*` aliases) to infer agent id and chat model, behavior drifts across modules, precedence rules multiply, and tests monkeypatch env in many places.

The core trigger pipeline (`run_trigger_graph`, inbound bridges) should also stay **free of vendor-specific shaping**: building W&B tag dicts inside the LangGraph wrapper couples execution to one integration.

This ADR records the **general practice** we apply: attach identity to explicit request context, resolve it once at entry boundaries, emit lifecycle events that carry neutral facts, and let **plugins** map facts to vendor formats. Where the synchronous run context is absent (for example Slack reaction feedback after the fact), **durable correlation** carries the same identity captured when context was still available.

## Decision

1. **Explicit context over ambient configuration** — Resolve agent id and chat model spec **once** when constructing [`TriggerContext`](../../helm/src/agent/trigger_context.py) at trigger entry ([`POST /api/v1/trigger`](../../helm/src/agent/app.py), Slack/Jira dispatch, admin helpers). Downstream code reads **`TriggerContext` fields**, not scattered `os.environ` lookups for per-run identity.

2. **Single assignment, many readers** — Canonical env alias precedence for identity exists in **one module** at construction time only (for example `runtime_identity.py`). Prometheus metrics, optional `wandb_session` tagging, and other consumers use the context object; they **do not** re-resolve the same identity from **`os.environ`** / `HOSTED_AGENT_*` for agent id, chat model, or equivalent fields when **`TriggerContext`** already carries those values (**context is truth**; no redundant env reads on the hot path).

3. **Plugins interpret; the core publishes facts** — Lifecycle publishers (see [ADR 0014](0014-observability-plugin-architecture.md)) emit events such as `RUN_STARTED` with payloads that include **`TriggerContext`** (or equivalent structured facts), **not** precomputed vendor tag dictionaries. Integration plugins (for example W&B trace) subscribe and build vendor-specific tags or config from that payload. The core runtime does **not** import integration-specific tag helpers.

4. **Correlation closes the asynchronous gap** — When later work lacks a live `TriggerContext` (feedback tied to an earlier Slack message), **persist identity** alongside existing correlation (`run_id`, `thread_id`, …) at the moment correlation is recorded (for example when recording a Slack post). Later handlers pass **neutral fields** on events (identity from correlation); they remain unaware of how W&B or another plugin will use them.

## Consequences

**Positive:**

- One precedence rule for env aliases; fewer magic-string reads and easier tests (set context fields or construction-time env once).
- Clear separation: execution pipeline vs plugin-specific interpretation, aligned with [ADR 0015](0015-integration-agnostic-observability-plugins.md) for shared observability layers.
- Async paths can retain the same agent/model identity as the originating run without re-inferring from env.

**Negative / trade-offs:**

- `TriggerContext` and correlation payloads carry more fields; construction sites and tests must stay in sync.
- Plugins must validate payload shape; breaking event contracts requires coordinated updates.

**Relationship to other ADRs:**

- [ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md) — Metric names and label bounding still governed there; this ADR governs **where** label **values** for agent/model identity come from (`TriggerContext`).
- [ADR 0014](0014-observability-plugin-architecture.md) — Event bus remains the integration boundary; this ADR specifies **what** run facts cross that boundary.

## Related

- [ADR 0011: Prometheus metrics schema and cardinality](0011-prometheus-metrics-schema-and-cardinality.md)
- [ADR 0014: Observability plugin architecture](0014-observability-plugin-architecture.md)
- [ADR 0015: Integration-agnostic observability plugins](0015-integration-agnostic-observability-plugins.md)
