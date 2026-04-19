## 1. Helm migration Job scaffolding

- [ ] 1.1 Add chart values + schema flags for optional Postgres migration `Job` (disabled by default), reusing documented DSN / Secret wiring aligned with **`HOSTED_AGENT_POSTGRES_URL`**.
- [ ] 1.2 Implement named template(s) or manifest slice for the Job (hook annotations, ServiceAccount if needed, resource limits).
- [ ] 1.3 Wire migration SQL into the Job container command (image + entrypoint aligned with design decision).

## 2. Verification

- [ ] 2.1 Helm unittest: rendered Job appears when enabled; env/Secret refs match existing Postgres patterns; hook ordering documented in template comments.
- [ ] 2.2 Update **`docs/runbook-checkpointing-wandb.md`** (or dedicated runbook section) with operator steps, failure triage, and relation to **`[DALC-REQ-POSTGRES-AGENT-PERSISTENCE-004]`**.
- [ ] 2.3 **`python3 scripts/check_spec_traceability.py`** after promoting **`dalc-postgres-migrations-rollout`** requirements into **`openspec/specs/`** with matrix rows and pytest/Helm citations per ADR 0003.

## 3. Promotion (post-implementation)

- [ ] 3.1 Merge delta **`openspec/changes/real-db-migrations-rollout/specs/`** into **`openspec/specs/dalc-postgres-migrations-rollout/spec.md`** when behavior ships; archive change per **`openspec/AGENTS.md`**.
