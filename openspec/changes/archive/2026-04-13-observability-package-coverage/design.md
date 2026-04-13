## Context

The runtime ships `hosted_agents/observability/` (checkpoint factory, correlation store, feedback model, Slack ingest, trajectory/ATIF helpers, optional W&B adapter, etc.). CI enforces **≥85%** line coverage on `hosted_agents` via `pytest-cov`, but `tool.coverage.run.omit` currently excludes `*/observability/*`, so regressions in that package do not affect the gate. ADR 0002 states the runtime **SHALL** maintain ≥85% coverage on first-party code; the omit is an undocumented exception.

## Goals / Non-Goals

**Goals:**

- Include `hosted_agents/observability/` in the **same** coverage run and **same** `fail-under` threshold as the rest of `hosted_agents`.
- Add **fast, deterministic** tests (no network; W&B and Slack mocked or stubbed) that exercise branches that matter for correctness and future refactors.
- Keep tests **maintainable**: prefer small focused modules over one giant integration file if the package grows.

**Non-Goals:**

- Raising `fail-under` above 85% (unless the team explicitly chooses to after baseline).
- Integration tests against real W&B or Slack APIs (belongs in separate optional markers).
- Rewriting observability architecture; coverage work may suggest refactors but should not expand scope without a new change.

## Decisions

1. **Remove the omit entry** for `*/observability/*` in `runtime/pyproject.toml` once tests bring the aggregate back to **≥85%**. If a **tiny** subset remains impractical to cover (e.g. optional import paths), use **`# pragma: no cover`** with a one-line rationale on those lines only—not whole-package omit.

2. **Testing strategy**  
   - **Pure logic**: `settings`, `label_registry`, `atif` redaction/mining, `shadow.should_run_shadow`, `feedback_store` idempotency, `correlation_store`, `run_context` getters/setters.  
   - **Branches**: `build_checkpointer` for `memory` vs error paths for `postgres`/`redis`/unknown backend.  
   - **W&B**: mock `wandb` import or pass `ObservabilitySettings(wandb_enabled=False)` and assert `recorded_logs` / `recorded_spans` on `WandbTraceSession` without calling the network.  
   - **Slack ingest**: drive `handle_slack_reaction_event` with dict payloads; assert human vs orphan paths.

3. **ADR alignment**  
   - Prefer a **new ADR 0003** (“Observability coverage included in ADR 0002 scope”) or a **one-paragraph amendment** to 0002 stating that **all** packages under `runtime/src/hosted_agents/` are in scope unless a future ADR explicitly excludes a path. OpenSpec records the *requirement*; ADR records the *project policy*.

4. **Order of work**  
   - Land tests until coverage with omit **removed** passes locally and in CI **in the same change** as removing omit (or remove omit only after tests merge in a stacked PR—never leave main red).

## Risks / Trade-offs

- **[Risk] Temporary coverage dip** if omit is removed before tests merge → **Mitigation**: single PR or stacked PRs; do not push a commit that only deletes omit.
- **[Risk] Flaky tests** if real `wandb.init` runs → **Mitigation**: keep `wandb_enabled` false in unit tests; patch or isolate import.
- **[Trade-off] Test volume** vs package size → Accept more test files over re-introducing broad omit.

## Migration Plan

1. Add tests under `runtime/tests/` (e.g. `test_observability_*.py` split by concern).  
2. Remove `*/observability/*` from `[tool.coverage.run] omit`.  
3. Run `./ci.sh` until green.  
4. Optional: add ADR 0003 or amend 0002 and link from `docs/development-log.md`.

## Open Questions

- Whether to split observability into multiple test modules by submodule from day one or start with one file and split when it exceeds ~400 lines.
