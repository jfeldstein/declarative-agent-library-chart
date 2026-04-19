## Why

Production agents often need **human-in-the-loop (HITL)** pauses—for approval, edits, or policy gates—without abandoning a **declarative, config-first** operator model. [LangGraph’s functional API](https://docs.langchain.com/oss/python/langgraph/use-functional-api) supports HITL via [`interrupt`](https://reference.langchain.com/python/langgraph/types/interrupt) and [`Command`](https://docs.langchain.com/oss/python/langgraph/interrupts#resuming-interrupts) inside `@task` / `@entrypoint` workflows with checkpointing; the platform should express those pause points and resume semantics **in configuration**, not only in hand-written Python.

## What Changes

- Add a **declarative model** for HITL steps (e.g. generic human feedback, structured tool-call review) that the runtime can compile into functional-API workflows using `interrupt()` and resume via `Command(resume=...)`.
- Specify **checkpointing and threading** requirements so paused runs are durable and resumable with a stable `thread_id` (and documented interaction with any existing trigger/stream APIs).
- Define **minimal HTTP or runtime surface** (or extension of existing endpoints) to **discover interrupt payloads** and **submit resume commands** without requiring callers to embed LangGraph-specific types in raw form where a stable JSON contract suffices.
- Document alignment with LangGraph patterns: **tasks before an interrupt are not re-run** after resume; tool-call review flows (continue / update args / feedback as `ToolMessage`) are representable declaratively where in scope.

## Capabilities

### New Capabilities

- `declarative-langgraph-hitl`: Declarative configuration and runtime behavior for human-in-the-loop using LangGraph’s functional API (`interrupt`, `Command`, checkpointer), including schema for pause points, resume payloads, and operator-facing contracts.

### Modified Capabilities

- (none — no published requirement specs under `openspec/specs/` that this change amends.)

## Impact

- **[declarative-agent-library-chart](https://github.com/jfeldstein/declarative-agent-library-chart)** **Helm values / runtime config** gain optional HITL sections wired to the same declarative style as prompts and tools.
- **Python runtime** may add or extend a LangGraph `@entrypoint` path with `InMemorySaver` or production checkpointer, plus code generation or interpretation from declarative HITL config.
- **Dependencies**: `langgraph` (and related `langchain-core` types where tool-call review is implemented), consistent with existing stack choices in the runtime project.
- **API / ops**: callers and operators need a clear story for `thread_id`, streaming until interrupt, and resuming with structured JSON.

## Promotion status (DALC sync checklist §D)

**`declarative-langgraph-hitl`** remains a **draft** delta; there is **no** **`openspec/specs/declarative-langgraph-hitl/`** directory. Promotion is **deferred** until HITL behavior is ready for standalone **`openspec/specs/`** extraction and traceability.
