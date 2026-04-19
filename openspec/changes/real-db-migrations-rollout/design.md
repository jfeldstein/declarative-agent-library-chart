## Context

The repo already ships **SQL migration artifacts** (`helm/src/hosted_agents/migrations/`, bundled DDL, tests that validate schema helpers). Operators today follow **runbook** steps to apply DDL in real clusters. **`dalc-postgres-agent-persistence`** normative text covers **what** migrations must exist; it does not fully specify an **automated rollout** contract (Job lifecycle, ordering vs agent Deployment, idempotent re-apply policy).

## Goals / Non-Goals

**Goals:**

- Provide a **single, chart-level story** for applying migrations during install/upgrade (Helm **hook Job** or documented equivalent), reusing existing **Postgres URL** wiring from chart values.
- Make failure modes **visible** (logs, Kubernetes events, non-zero exit) so rollouts do not silently proceed with stale schema.
- Keep migrations **idempotent** where possible (consistent with existing SQL style).

**Non-Goals:**

- Replacing application-level migration tools (Alembic/Flyway) if adopted later — this design targets **this repo’s SQL bundles** and Helm/Kubernetes rollout.
- Multi-region blue/green orchestration beyond standard Helm upgrade semantics.

## Decisions

1. **Helm hook Job for `helm upgrade` / `helm install`**  
   **Rationale:** Fits GitOps and operator mental model; runs before new agent pods take traffic if hooks ordered correctly.  
   **Alternative:** Init container on Deployment — duplicates image pull and couples migrations to pod restart only.

2. **Reuse DSN from same Secret/env sources as agent `HOSTED_AGENT_POSTGRES_URL`**  
   **Rationale:** Avoid second credential path; aligns with **`checkpoints.postgresUrl`** / observability Postgres documentation.  
   **Alternative:** Separate migration-only Secret — more knobs for operators.

3. **Apply SQL from embedded chart ConfigMap or image-mounted path mirroring repo layout**  
   **Rationale:** Keeps chart self-contained; matches existing migration file discovery in Python tests.  
   **Alternative:** Download migrations from external artifact store — out of scope.

## Risks / Trade-offs

- **[Risk] Long-running migration locks tables** → **Mitigation:** Document maintenance windows for large DDL; optional timeout on Job.
- **[Risk] Hook failure blocks upgrade** → **Mitigation:** Correct by default; document `helm upgrade --no-hooks` only for break-glass with human DDL review.
- **[Trade-off] Cluster-specific drift** → Runbook remains for manual repair; automated Job is the **happy path**, not a guarantee of historical branch cleanup.

## Migration Plan

1. Land delta spec + Helm Job template behind a **values flag** defaulting to current documented behavior until enabled.
2. Add Helm unittest for rendered Job + env from Secret.
3. Document operator steps in runbook; optional integration tier applies Job in kind.

## Open Questions

- Whether migration Job uses the **same container image** as the agent vs a minimal **flyway-like** sidecar — pick based on SQL client availability in image.
- Exact **hook weight** ordering vs optional **`observability-migration`** hook already in chart (if present).
