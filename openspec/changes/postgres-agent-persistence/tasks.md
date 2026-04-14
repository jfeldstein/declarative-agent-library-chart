## 1. Dependencies and checkpointer wiring

- [ ] 1.1 Pin LangGraph Postgres checkpointer + DB driver in `helm/src/pyproject.toml` (align with installed `langgraph` version); document in runbook
- [ ] 1.2 Implement `build_checkpointer` Postgres branch: validate URL, construct saver, handle connection errors with actionable messages
- [ ] 1.3 Add unit tests with mocked saver constructor or testcontainer (optional marker) proving Postgres branch returns a checkpointer
- [ ] 1.4 Update `docs/runbook-checkpointing-wandb.md` with Postgres provisioning, pooling, and LangGraph compatibility notes

## 2. Schema and migrations

- [ ] 2.1 Author initial SQL migration(s) for application tables: correlation, human_feedback, operational_events, side_effect_checkpoints, tool_span_summaries (names per design)
- [ ] 2.2 Add indexes for primary lookup paths (`thread_id`, `run_id`, `(channel_id, message_ts)`, `tool_call_id`, time-range queries)
- [ ] 2.3 Document migration apply path (Helm Job vs operator `psql`) and rollback strategy (snapshot + downgrade notes)

## 3. Repository layer (memory + Postgres)

- [ ] 3.1 Introduce protocols/ABCs for correlation, feedback, operational events, side-effects, span summaries
- [ ] 3.2 Refactor existing in-memory singletons to implement the protocols; preserve default behavior when env selects memory
- [ ] 3.3 Implement Postgres repositories using connection pool; map rows to existing dataclasses/events
- [ ] 3.4 Add env `HOSTED_AGENT_OBSERVABILITY_STORE=memory|postgres` (and URL/key vars) to `ObservabilitySettings` and Helm values

## 4. Integration with HTTP and graph paths

- [ ] 4.1 Wire FastAPI routes and Slack ingest to use injected repository factory (no global hidden state in tests)
- [ ] 4.2 Ensure `run_trigger_graph` / tool paths write through repositories when Postgres enabled
- [ ] 4.3 Extend operator read APIs to read from Postgres when configured (or document that list endpoints query DB)

## 5. Helm and ops

- [ ] 5.1 Add Helm values for Postgres URL secretKeyRef, observability store mode, migration toggle
- [ ] 5.2 Optional: Helm hook Job to apply SQL migrations on upgrade (behind `observability.postgres.migrations.enabled`)

## 6. Verification

- [ ] 6.1 CI: default PR path uses mocks or sqlite-free unit tests; optional integration job with Postgres
- [ ] 6.2 `./ci.sh` green; coverage policy per repo rules (include new modules appropriately)
- [ ] 6.3 Manual smoke: enable postgres backend in kind/example values and verify checkpoint + feedback survive pod delete
