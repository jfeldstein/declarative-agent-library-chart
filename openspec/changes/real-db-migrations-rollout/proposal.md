## Why

Today, SQL migration artifacts and documentation describe **operator-driven** application of DDL to Postgres (runbook, hooks, manual steps). CI validates SQL shape and in-process paths, but there is **no first-class, automated rollout path** that applies schema changes safely across environments (ordering, locking, idempotency, observability, and rollback posture) as part of deploy/upgrade — leaving a gap between “migrations exist” and “migrations are reliably applied in production.”

## What Changes

- Introduce a **documented migrations rollout capability**: how schema changes are **packaged**, **versioned**, **applied** during chart/agent upgrades, and **verified** (pre/post checks), without silently assuming manual `kubectl exec` as the only path.
- Define operator-facing contracts for **job ordering** relative to agent pods (migrate-before-traffic), **credentials** reuse with existing Postgres DSN wiring, and **failure semantics** (surface errors, optional retry policy).
- Add normative requirements under a **new promoted capability** (delta spec first), with traceability to Helm Job/CronJob hooks or equivalent mechanism as implemented.

## Capabilities

### New Capabilities

- `dalc-postgres-migrations-rollout`: Declarative and operational contract for **applying** hosted-agents Postgres migrations during rollout (hooks, Jobs, idempotent apply, observability); complements **`dalc-postgres-agent-persistence`** artifact DDL with a **process** for real-cluster application.

### Modified Capabilities

- `dalc-postgres-agent-persistence`: Cross-reference or refine **`[DALC-REQ-POSTGRES-AGENT-PERSISTENCE-004]`** narrative only if the new capability **supersedes** part of “how migrations land in prod”; otherwise leave IDs stable and link from new spec scenarios.

## Impact

- **Helm**: optional **`Job`** / **`pre-install`/`pre-upgrade` hook** wiring (or documented alternative) using existing Secret/DSN patterns from **`checkpoints.postgresUrl`** / observability Postgres env.
- **Runtime / ops**: alignment with migration SQL under **`helm/src/hosted_agents/migrations/`** and runbooks; CI may gain an integration-tier check that renders migration Job manifests.
- **Docs**: `docs/runbook-checkpointing-wandb.md` or successor links to rollout procedure.
