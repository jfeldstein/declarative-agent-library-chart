# Design: Langfuse observability plugin

## Architecture

1. **Configuration** — `LangfusePluginSettings` captures Helm/env keys (`HOSTED_AGENT_LANGFUSE_*`).
2. **Bootstrap** — `build_langfuse_client` constructs `langfuse.Langfuse` when enabled + keys exist; `register_langfuse_plugin` attaches subscribers only on the **agent** bus (HTTP workload).
3. **Bridge** — `LangfuseLifecycleBridge` wraps each observation with `propagate_attributes` so Langfuse sessions/tags align with thread + tenant identifiers already present in `TriggerContext`.
4. **Telemetry mapping**
   - Generations → `llm.generation.completed` → `start_observation(..., as_type="generation")`.
   - Tool spans → `tool.call.*` events → `as_type="tool"`.
   - Retrieval spans → `rag.*` events → `as_type="retriever"`.
   - Trigger completion → `trigger.request.responded` closes with `flush()` to export buffered spans quickly.
   - Scores → future `feedback.recorded` payloads can call `create_score`.

## Redaction stance

Langfuse MUST NOT become a second redactor. Middleware + LangGraph instrumentation own raw prompt/output handling; the bridge emits bounded metadata only (token counts, enum labels, structured tags).

## Testing strategy

- Mock Langfuse client records `start_observation`, `flush`, and `create_trace_id`.
- Helm unittest asserts env wiring for secret-backed keys.
