## Context

The **config-first hosted agents** direction treats prompts, tools, and deployment as **declarative configuration** (Helm values, env, YAML). [LangGraph’s functional API](https://docs.langchain.com/oss/python/langgraph/use-functional-api) implements **human-in-the-loop** with `interrupt()` inside `@task` flows and **resume** via `Command(resume=...)`, backed by a **checkpointer** so work before the pause is not repeated. Today there is no shared contract that maps **operator-authored config** to those primitives while staying aligned with upstream docs ([Human-in-the-loop](https://docs.langchain.com/oss/python/langgraph/use-functional-api#human-in-the-loop)).

## Goals / Non-Goals

**Goals:**

- Express **named HITL pause points** and their **expected resume shape** (string feedback vs structured tool-call review) in declarative config.
- Require a **durable checkpointer** and **`thread_id`** story for any HITL-enabled workflow so pause/resume is reproducible across processes.
- Expose a **stable, JSON-friendly** operator/runtime contract for “run until interrupt” and “resume with payload,” without forcing raw LangGraph Python types at the HTTP boundary where avoidable.
- Implement (or extend) the runtime using **`@entrypoint` + `@task` + `interrupt` + `Command`**, matching LangGraph functional API semantics.

**Non-Goals:**

- Defining a full visual approval UI; only **API/config contracts** and runtime behavior.
- Replacing non-functional-API graphs where not needed; **interop** with Graph API remains possible per LangGraph docs but is not required for v1.
- Cross-tenant **authorization** for who may resume a thread (beyond documenting hooks); treat as platform layering unless explicitly added later.

### HITL (this change) vs post-hoc human feedback

**HITL here** means **LangGraph `interrupt()` / `Command(resume=…)`**: the graph **stops** at a configured pause point and **does not** execute subsequent tasks until a resume payload arrives, with checkpoint state making that pause **durable** across processes when a production checkpointer (e.g. Postgres per **`postgres-agent-persistence`**) is configured.

**Post-hoc human feedback** (e.g. emoji reactions on a Slack message **after** the assistant posted) is **not** this pattern: the run may already have completed; humans attach signals that **correlate** to past `tool_call_id` / checkpoint rows via **`tool-feedback-slack`** and related stores. Reserve the term **HITL** for **pre-continuation gates**; use **human feedback** / **reaction correlation** for **async** supervision signals.

## Decisions

1. **Declarative schema for interrupt kinds**  
   - **Decision**: Support at least two config-driven patterns aligned with LangGraph examples: (a) **simple feedback** — interrupt payload is a string template or structured message; resume value is a string (or small JSON) merged into the next task input; (b) **tool-call review** — declarative mapping from resume JSON to outcomes: `continue`, `update` (args patch), `feedback` (synthetic tool message).  
   - **Rationale**: Matches [basic HITL](https://docs.langchain.com/oss/python/langgraph/use-functional-api#basic-human-in-the-loop-workflow) and [review tool calls](https://docs.langchain.com/oss/python/langgraph/use-functional-api#review-tool-calls) without inventing a third model.  
   - **Alternatives**: Only string interrupts (too weak for tool governance); only code-defined interrupts (not declarative).

2. **Compilation vs interpretation**  
   - **Decision**: Runtime **builds** an `entrypoint` graph from validated declarative config (or loads a fixed template parameterized by config), rather than `eval` of arbitrary Python.  
   - **Rationale**: Keeps security and reviewability; stays “declarative” for operators.  
   - **Alternatives**: Pluggable Python modules per agent (more flexible, less uniform).

3. **Checkpointing**  
   - **Decision**: HITL mode **MUST** use a LangGraph-compatible checkpointer; default for dev may remain in-memory, production path targets pluggable backend (e.g. Postgres saver) as a follow-on if not already present.  
   - **Rationale**: Required for `interrupt`/`Command` semantics.  
   - **Alternatives**: No checkpoint (breaks resume).

4. **HTTP surface**  
   - **Decision**: Extend or add endpoints so: initial invoke/stream can **terminate at interrupt** with a **machine-readable interrupt descriptor** (type, display message or tool-call snapshot, `thread_id`); resume endpoint accepts **JSON body** that maps to `Command(resume=...)`.  
   - **Rationale**: Declarative operators and external UIs integrate without importing LangGraph in the client.  
   - **Alternatives**: Document-only (“use LangGraph SDK locally”) — weaker for hosted agents.

5. **Streaming**  
   - **Decision**: Reuse LangGraph **streaming** modes (`updates`, `custom`, etc.) where already used; document that streams **surface interrupt boundaries** similarly to Graph API.  
   - **Rationale**: Same runtime as functional API per upstream.

## Risks / Trade-offs

- **[Risk] Config expressiveness lags hand-coded agents** → **Mitigation**: Version the declarative schema; allow a narrow “escape hatch” (e.g. named preset workflows) only if spec explicitly allows it later.  
- **[Risk] Resume payload mismatch causes confusing errors** → **Mitigation**: Validate resume JSON against the interrupt kind; return clear 4xx errors.  
- **[Risk] In-memory checkpointer in production loses state** → **Mitigation**: Spec marks production requirement for durable checkpointer when HITL is enabled; document in migration.  
- **[Trade-off] Declarative tool-call review may not cover every LangChain edge case** → Start with the three actions from LangGraph docs (`continue` / `update` / `feedback`).

## Migration Plan

1. Land schema + spec + runtime behind **feature flag** or **opt-in values** so existing single-shot triggers unchanged.  
2. Add integration tests: pause after step A, resume, assert step A not re-executed (e.g. via side-effect counter).  
3. Document **`thread_id`** generation for clients (UUID per conversation) and rollback (disable HITL section, redeploy).

## Open Questions

- Which **production checkpointer** implementation is standard for this repo (Postgres, Redis, vendor)?  
- Should **subagents** (from parallel runtime work) inherit parent `thread_id` namespace or isolate interrupts per subagent invocation?
