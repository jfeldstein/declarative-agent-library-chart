## 1. Schema and validation

- [ ] 1.1 Add declarative schema (YAML/JSON Schema or Pydantic models) for HITL: interrupt kinds (`simple_feedback`, `tool_call_review`), ordering hooks, and resume payload shapes.
- [ ] 1.2 Document example Helm/values fragments aligned with [declarative-agent-library-chart](https://github.com/jfeldstein/declarative-agent-library-chart) conventions.

## 2. LangGraph functional workflow

- [ ] 2.1 Implement builder that compiles validated HITL config into an `@entrypoint` + `@task` workflow using `interrupt()` and checkpointer injection.
- [ ] 2.2 Implement `simple_feedback` path: string (or small JSON) interrupt and merge resume into downstream task input.
- [ ] 2.3 Implement `tool_call_review` path: map resume actions `continue`, `update`, `feedback` to `ToolCall` / `ToolMessage` outcomes per LangGraph docs.

## 3. HTTP API and threading

- [ ] 3.1 Extend or add endpoints: initial invoke/stream stops at interrupt with JSON interrupt descriptor; resume endpoint accepts JSON mapped to `Command(resume=...)`.
- [ ] 3.2 Require and validate `thread_id` (or configurable key) on invoke/resume; return clear errors on mismatch or invalid resume shape.
- [ ] 3.3 Document client flow (generate `thread_id`, stream until interrupt, POST resume) in runtime README or operator docs.

## 4. Persistence and operations

- [ ] 4.1 Wire checkpointer: dev default may remain in-memory; document production requirement for durable backend when HITL is enabled.
- [ ] 4.2 Feature-flag or values-gate HITL so existing single-shot triggers stay unchanged when disabled.

## 5. Verification

- [ ] 5.1 Add integration tests: counter or mock proves pre-interrupt task does not re-run on resume for the same `thread_id`.
- [ ] 5.2 Add tests for invalid resume payloads (4xx) and for tool-call review branches (`continue` / `update` / `feedback`).
