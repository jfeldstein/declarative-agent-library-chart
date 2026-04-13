## 1. Baseline tests (observability package)

- [ ] 1.1 Add unit tests for `ObservabilitySettings.from_env()` (truthy flags, JSON maps, shadow sample rate bounds, invalid JSON errors)
- [ ] 1.2 Add unit tests for `get_label_registry` / `load_label_registry_from_env` (default registry, empty `{}` / `null` string, custom JSON with labels list)
- [ ] 1.3 Add unit tests for `CorrelationStore`, `FeedbackStore` (put/get, idempotency key, orphan path, reset)
- [ ] 1.4 Add unit tests for `run_context` (bind_run_context, new_tool_call_id, wandb session contextvars)
- [ ] 1.5 Add unit tests for `build_checkpointer` (`memory` path; `postgres`/`redis`/unknown error messages; disabled checkpoints returns None)
- [ ] 1.6 Add unit tests for `side_effects.record_side_effect_checkpoint` and `TrajectoryRecorder` / `export_atif_batch` / `positive_mining_filter` / `hash_tag_value`
- [ ] 1.7 Add unit tests for `ShadowSettings.from_env` and `should_run_shadow` (tenant allowlist, sample rate 0/1, hashing stability)
- [ ] 1.8 Add unit tests for `WandbTraceSession` with `wandb_enabled=False` (mandatory_tags cardinality/hash path, log_tool_span, log_feedback, finish safe)
- [ ] 1.9 Add unit tests for `handle_slack_reaction_event` (disabled slack, orphan, unknown label, recorded human feedback + dedupe key, W&B branch when enabled with mocked session or no network)

## 2. Coverage configuration and policy docs

- [ ] 2.1 Remove `*/observability/*` from `[tool.coverage.run] omit` in `runtime/pyproject.toml` after tests from §1 bring total coverage ≥ `fail-under`
- [ ] 2.2 Run `./ci.sh` and fix any gaps (add tests or narrowly scoped `pragma: no cover` with rationale—no package-wide omit)
- [ ] 2.3 Add ADR 0003 (or amend ADR 0002) stating observability is in scope for ADR 0002 unless explicitly carved out later; link from `docs/development-log.md` when merging

## 3. Verification

- [ ] 3.1 Confirm coverage report lists `hosted_agents/observability/*` with non-zero covered lines
- [ ] 3.2 Confirm no new network calls in default unit test run (W&B/Slack remain mocked or disabled)
