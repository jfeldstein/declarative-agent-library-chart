# Tasks: observability-plugin-wandb

## Implementation

- [x] Move `WandbTraceSession` to `agent/observability/plugins/wandb/trace.py`; keep `wandb_trace.py` as compatibility re-export.
- [x] Add `register_wandb_trace_plugin` subscribing to `RUN_STARTED`, `RUN_ENDED`, `TOOL_CALL_COMPLETED`, `FEEDBACK_RECORDED`.
- [x] Add middleware publishers: `publish_run_started`, `publish_run_ended`, `publish_feedback_recorded`; extend `publish_tool_call_completed` with `tool_call_id` and `duration_s`.
- [x] Wire `run_trigger_graph` / `run_tool_json` / `slack_ingest` to lifecycle events; register plugin from `build_event_bus("agent", ...)`.
- [x] Helm: `observability.plugins.wandb.{enabled,project,entity}`; update `_manifest_deployment.tpl`, `values.schema.json`, `hello_world_test.yaml`.
- [x] Promoted spec RTV-002 + traceability matrix note.
- [x] `uv run pytest` (helm/src); `python3 scripts/check_spec_traceability.py`.

## Follow-ups (out of scope)

- [ ] Optional: gate plugin registration strictly on `ObservabilityPluginsConfig.wandb.enabled` once all callers use `plugins_config_from_env()` in tests.
