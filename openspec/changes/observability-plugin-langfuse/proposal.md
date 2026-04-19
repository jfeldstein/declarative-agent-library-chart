# Proposal: Langfuse observability plugin

## Problem

Operators need hosted-agent traces in Langfuse with minimal bespoke wiring. Phase 1 exposed lifecycle events on an in-process bus; Phase 2 requires a Langfuse SDK bridge plus Helm/env alignment.

## Approach

- Implement `LangfuseLifecycleBridge` subscribing to `SyncEventBus` for LLM/tool/RAG/trigger events.
- Extend `observability.plugins.langfuse` Helm values with host, secret refs, and flush interval toggles mapping to `HOSTED_AGENT_LANGFUSE_*`.
- Document that prompt/body redaction remains middleware-owned.

## References

- Capability: `openspec/specs/dalc-plugin-langfuse-traces/spec.md`
- Runtime module: `helm/src/agent/observability/plugins/langfuse_bridge.py`
